"""
Lever ATS Public Postings Job Source Adapter.
Fetches official, unblocked direct postings from Lever public API:
https://api.lever.co/v0/postings/{slug}?mode=json
"""
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import httpx
import yaml
from bs4 import BeautifulSoup

from app.adapters.base import BaseJobSourceAdapter

logger = logging.getLogger("ai_job_hunter.adapters.lever")

USER_AGENT = "AI-Job-Hunter-Bot/1.0 (+https://github.com/msamir-17/Ai_job_hunter)"
DEFAULT_COMPANIES = [
    "spotify",
    "palantir",
    "lever",
]


def _clean_html(raw_html: str | None) -> str:
    """Converts HTML text or job descriptions into clean, normalized plain text."""
    if not raw_html or not raw_html.strip():
        return ""
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator="\n")
        lines = (line.strip() for line in text.splitlines())
        return "\n".join(chunk for chunk in lines if chunk)
    except Exception:
        return raw_html.strip()


def load_lever_slugs() -> list[str]:
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
                    if data and "lever" in data and isinstance(data["lever"], list):
                        return [str(s).strip() for s in data["lever"] if str(s).strip()]
            except Exception as e:
                logger.warning(f"Could not parse companies.yaml at {p}: {e}")
    return DEFAULT_COMPANIES


class LeverJobSourceAdapter(BaseJobSourceAdapter):
    """
    Adapter fetching direct job postings from Lever public company boards.
    """

    def __init__(self, slugs: list[str] | None = None, concurrency: int = 5):
        self.slugs = slugs or load_lever_slugs()
        self.concurrency = concurrency

    @property
    def source_name(self) -> str:
        return "lever"

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
                    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
                    try:
                        resp = await client.get(url)
                        if resp.status_code == 404:
                            logger.info(f"Lever board not found for slug '{slug}' (404), skipping.")
                            return []
                        resp.raise_for_status()
                        raw_items = resp.json()
                        if not isinstance(raw_items, list):
                            return []

                        company_display = slug.replace("-", " ").title()
                        board_jobs = []

                        for item in raw_items:
                            job_id = str(item.get("id"))
                            title = (item.get("text") or "").strip()
                            if not title or not job_id:
                                continue

                            categories = item.get("categories") or {}
                            location_str = categories.get("location") if isinstance(categories, dict) else ""
                            workplace_type = (item.get("workplaceType") or "").lower()

                            is_remote = False
                            loc_lower = (location_str or "").lower()
                            title_lower = title.lower()
                            if workplace_type == "remote" or "remote" in loc_lower or "anywhere" in loc_lower or "remote" in title_lower:
                                is_remote = True

                            # Created at is epoch ms
                            posted_at = None
                            created_ms = item.get("createdAt")
                            if isinstance(created_ms, (int, float)):
                                try:
                                    posted_at = datetime.fromtimestamp(created_ms / 1000.0, tz=timezone.utc)
                                except Exception:
                                    posted_at = None

                            source_url = (item.get("hostedUrl") or "").strip()
                            apply_url = (item.get("applyUrl") or "").strip()

                            # Combine description and lists sections
                            desc_parts = []
                            desc_html = item.get("description") or item.get("descriptionPlain") or ""
                            if desc_html:
                                desc_parts.append(_clean_html(desc_html))

                            lists = item.get("lists") or []
                            if isinstance(lists, list):
                                for lst in lists:
                                    if isinstance(lst, dict):
                                        header = lst.get("text") or ""
                                        content = lst.get("content") or ""
                                        cleaned_content = _clean_html(content)
                                        if header and cleaned_content:
                                            desc_parts.append(f"{header}:\n{cleaned_content}")
                                        elif cleaned_content:
                                            desc_parts.append(cleaned_content)

                            clean_desc = "\n\n".join(part for part in desc_parts if part)

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
                                "url": source_url or None,
                                "source_url": source_url or None,
                                "apply_url": apply_url or source_url or None,
                                "posted_at": posted_at,
                                "dedup_key": None,
                            })

                        return board_jobs
                    except Exception as err:
                        logger.warning(f"Failed fetching Lever board '{slug}': {err}")
                        return []

            tasks = [fetch_board(slug) for slug in target_slugs]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for res in results:
                if isinstance(res, list):
                    all_jobs.extend(res)

        if limit is not None and limit > 0:
            return all_jobs[:limit]
        return all_jobs
