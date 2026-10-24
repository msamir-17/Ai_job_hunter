"""
Greenhouse ATS Public Boards Job Source Adapter.
Fetches official, unblocked direct postings from Greenhouse public boards API:
https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
import httpx
import yaml
from bs4 import BeautifulSoup

from app.adapters.base import BaseJobSourceAdapter

logger = logging.getLogger("ai_job_hunter.adapters.greenhouse")

USER_AGENT = "AI-Job-Hunter-Bot/1.0 (+https://github.com/msamir-17/Ai_job_hunter)"
DEFAULT_COMPANIES = [
    "stripe",
    "figma",
    "gitlab",
    "canonical",
    "elastic",
    "datadog",
    "cloudflare",
    "discord",
    "dropbox",
    "gusto",
    "brex",
    "coinbase",
    "anthropic",
]


def _clean_html(raw_html: str | None) -> str:
    """Converts HTML job descriptions into clean, normalized plain text."""
    if not raw_html or not raw_html.strip():
        return ""
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator="\n")
        lines = (line.strip() for line in text.splitlines())
        return "\n".join(chunk for chunk in lines if chunk)
    except Exception:
        return raw_html.strip()


def load_greenhouse_slugs() -> list[str]:
    """Loads company slugs from companies.yaml with fallback to defaults."""
    candidate_paths = [
        Path(__file__).parent.parent / "data" / "companies.yaml",
        Path(__file__).parent.parent.parent / "config" / "companies.yaml",
    ]
    for p in candidate_paths:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "greenhouse" in data and isinstance(data["greenhouse"], list):
                        return [str(s).strip() for s in data["greenhouse"] if str(s).strip()]
            except Exception as e:
                logger.warning(f"Could not parse companies.yaml at {p}: {e}")
    return DEFAULT_COMPANIES


class GreenhouseJobSourceAdapter(BaseJobSourceAdapter):
    """
    Adapter fetching direct job postings from Greenhouse public company boards.
    """

    def __init__(self, slugs: list[str] | None = None, concurrency: int = 5):
        self.slugs = slugs or load_greenhouse_slugs()
        self.concurrency = concurrency

    @property
    def source_name(self) -> str:
        return "greenhouse"

    async def fetch_jobs(self, limit: int | None = None, **kwargs: Any) -> list[dict[str, Any]]:
        target_slugs = kwargs.get("slugs") or self.slugs
        if isinstance(target_slugs, str):
            target_slugs = [target_slugs]

        semaphore = asyncio.Semaphore(self.concurrency)
        all_jobs: list[dict[str, Any]] = []

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(headers=headers, timeout=10.0, follow_redirects=True) as client:
            async def fetch_board(slug: str) -> list[dict[str, Any]]:
                async with semaphore:
                    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
                    try:
                        resp = await client.get(url)
                        if resp.status_code == 404:
                            logger.info(f"Greenhouse board not found for slug '{slug}' (404), skipping.")
                            return []
                        resp.raise_for_status()
                        payload = resp.json()
                        raw_items = payload.get("jobs", [])
                        company_display = slug.replace("-", " ").title()

                        board_jobs = []
                        for item in raw_items:
                            job_id = str(item.get("id"))
                            title = (item.get("title") or "").strip()
                            if not title or not job_id:
                                continue

                            location_obj = item.get("location") or {}
                            location_str = location_obj.get("name", "") if isinstance(location_obj, dict) else str(location_obj)

                            is_remote = False
                            loc_lower = (location_str or "").lower()
                            title_lower = title.lower()
                            if "remote" in loc_lower or "anywhere" in loc_lower or "home based" in loc_lower or "remote" in title_lower:
                                is_remote = True

                            # Parse first_published if present
                            posted_at = None
                            first_pub = item.get("first_published")
                            if first_pub:
                                try:
                                    posted_at = datetime.fromisoformat(first_pub)
                                except Exception:
                                    posted_at = None

                            abs_url = (item.get("absolute_url") or "").strip()
                            content_html = item.get("content") or ""
                            clean_desc = _clean_html(content_html)

                            board_jobs.append({
                                "source": self.source_name,
                                "external_id": job_id,
                                "title": title,
                                "company": company_display,
                                "location": location_str or None,
                                "is_remote": is_remote,
                                "salary_min": None,
                                "salary_max": None,
                                "raw_description": clean_desc,
                                "skills_required": [],
                                "url": abs_url or None,
                                "source_url": abs_url or None,
                                "apply_url": abs_url or None,
                                "posted_at": posted_at,
                                "dedup_key": None,
                            })

                        return board_jobs
                    except Exception as err:
                        logger.warning(f"Failed fetching Greenhouse board '{slug}': {err}")
                        return []

            tasks = [fetch_board(slug) for slug in target_slugs]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for res in results:
                if isinstance(res, list):
                    all_jobs.extend(res)

        if limit is not None and limit > 0:
            return all_jobs[:limit]
        return all_jobs
