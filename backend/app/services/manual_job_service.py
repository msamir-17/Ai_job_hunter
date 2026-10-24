"""
Service for handling manual job ingestion (Pasted JD text or Job Posting URL).
Resolves direct ATS URLs (Greenhouse, Lever) via public API without web scraping,
or extracts structured job details using the BaseLLMProvider.
"""
import hashlib
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.greenhouse_adapter import USER_AGENT, _clean_html as clean_gh_html
from app.adapters.lever_adapter import _clean_html as clean_lever_html
from app.llm.base import BaseLLMProvider
from app.models import Job
from app.schemas.job import ExtractedJobData, ManualJobSubmissionRequest
from app.services.dedup_service import generate_dedup_key

logger = logging.getLogger("ai_job_hunter.services.manual_job")

GREENHOUSE_REGEX = re.compile(
    r"(?:https?://)?(?:boards|job-boards)\.greenhouse\.io/(?:v1/boards/)?(?P<slug>[^/]+)/jobs/(?P<id>\d+)",
    re.IGNORECASE,
)
LEVER_REGEX = re.compile(
    r"(?:https?://)?jobs\.lever\.co/(?P<slug>[^/]+)/(?P<id>[a-f0-9\-]+)",
    re.IGNORECASE,
)


class ManualJobService:
    def __init__(self, db: AsyncSession, llm_provider: BaseLLMProvider):
        self.db = db
        self.llm_provider = llm_provider

    async def ingest_manual_job(self, req: ManualJobSubmissionRequest) -> Job:
        url = (req.url or "").strip()
        raw_text = (req.raw_text or "").strip()

        # 1. Check for direct Greenhouse URL
        if url:
            gh_match = GREENHOUSE_REGEX.search(url)
            if gh_match:
                slug = gh_match.group("slug")
                job_id = gh_match.group("id")
                return await self._fetch_greenhouse_job(slug, job_id, url)

            # 2. Check for direct Lever URL
            lever_match = LEVER_REGEX.search(url)
            if lever_match:
                slug = lever_match.group("slug")
                job_id = lever_match.group("id")
                return await self._fetch_lever_job(slug, job_id, url)

        # 3. If generic URL without raw_text, attempt to fetch page text
        content_to_extract = raw_text
        source = "manual-paste" if raw_text else "manual-url"

        if url and not content_to_extract:
            content_to_extract = await self._fetch_page_text(url)
            source = "manual-url"

        # 4. Extract structured job metadata via LLM
        system_prompt = (
            "You are an expert recruitment parser. Extract job details from the provided job description.\n"
            "Guardrails:\n"
            "- Extract ONLY facts explicitly stated in the job posting.\n"
            "- Do not invent salary or location if missing.\n"
            "- List required technical and professional skills accurately.\n"
        )
        user_prompt = f"Job Posting URL: {url or 'N/A'}\n\nJob Description:\n{content_to_extract[:8000]}"

        extracted: ExtractedJobData = await self.llm_provider.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=ExtractedJobData,
        )

        external_id = f"manual-{hashlib.sha256((url or content_to_extract[:200]).encode('utf-8')).hexdigest()[:16]}"
        dedup_key = generate_dedup_key(
            company=extracted.company,
            title=extracted.title,
            location=extracted.location,
            is_remote=extracted.is_remote,
        )

        # Check existing by dedup_key or external_id
        existing_job = await self._find_existing_job(source, external_id, dedup_key)
        if existing_job:
            return existing_job

        new_job = Job(
            id=uuid.uuid4(),
            source=source,
            external_id=external_id,
            title=extracted.title,
            company=extracted.company,
            location=extracted.location,
            is_remote=extracted.is_remote,
            salary_min=extracted.salary_min,
            salary_max=extracted.salary_max,
            description_raw=extracted.summary or content_to_extract,
            skills_required=extracted.skills_required,
            url=url or None,
            source_url=url or None,
            apply_url=url or None,
            posted_at=datetime.now(timezone.utc),
            dedup_key=dedup_key,
        )
        self.db.add(new_job)
        await self.db.commit()
        await self.db.refresh(new_job)
        return new_job

    async def _fetch_greenhouse_job(self, slug: str, job_id: str, original_url: str) -> Job:
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{job_id}"
        async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
            resp = await client.get(api_url)
            resp.raise_for_status()
            data = resp.json()

        title = (data.get("title") or "").strip()
        location_obj = data.get("location") or {}
        location_str = location_obj.get("name", "") if isinstance(location_obj, dict) else str(location_obj)
        content_html = data.get("content") or ""
        clean_desc = clean_gh_html(content_html)

        is_remote = "remote" in (location_str or "").lower() or "remote" in title.lower()
        company = slug.replace("-", " ").title()

        posted_at = None
        if data.get("first_published"):
            try:
                posted_at = datetime.fromisoformat(data["first_published"])
            except Exception:
                posted_at = datetime.now(timezone.utc)

        abs_url = (data.get("absolute_url") or original_url).strip()
        dedup_key = generate_dedup_key(company, title, location_str, is_remote)

        existing_job = await self._find_existing_job("greenhouse", job_id, dedup_key)
        if existing_job:
            return existing_job

        new_job = Job(
            id=uuid.uuid4(),
            source="greenhouse",
            external_id=str(job_id),
            title=title,
            company=company,
            location=location_str or None,
            is_remote=is_remote,
            salary_min=None,
            salary_max=None,
            description_raw=clean_desc,
            skills_required=[],
            url=abs_url,
            source_url=abs_url,
            apply_url=abs_url,
            posted_at=posted_at or datetime.now(timezone.utc),
            dedup_key=dedup_key,
        )
        self.db.add(new_job)
        await self.db.commit()
        await self.db.refresh(new_job)
        return new_job

    async def _fetch_lever_job(self, slug: str, job_id: str, original_url: str) -> Job:
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        api_url = f"https://api.lever.co/v0/postings/{slug}/{job_id}"
        async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
            resp = await client.get(api_url)
            resp.raise_for_status()
            data = resp.json()

        title = (data.get("text") or "").strip()
        categories = data.get("categories") or {}
        location_str = categories.get("location") if isinstance(categories, dict) else ""
        workplace_type = (data.get("workplaceType") or "").lower()
        is_remote = workplace_type == "remote" or "remote" in (location_str or "").lower()

        created_ms = data.get("createdAt")
        posted_at = None
        if isinstance(created_ms, (int, float)):
            try:
                posted_at = datetime.fromtimestamp(created_ms / 1000.0, tz=timezone.utc)
            except Exception:
                posted_at = datetime.now(timezone.utc)

        source_url = (data.get("hostedUrl") or original_url).strip()
        apply_url = (data.get("applyUrl") or source_url).strip()
        company = slug.replace("-", " ").title()

        desc_html = data.get("description") or data.get("descriptionPlain") or ""
        clean_desc = clean_lever_html(desc_html)

        dedup_key = generate_dedup_key(company, title, location_str, is_remote)

        existing_job = await self._find_existing_job("lever", job_id, dedup_key)
        if existing_job:
            return existing_job

        new_job = Job(
            id=uuid.uuid4(),
            source="lever",
            external_id=str(job_id),
            title=title,
            company=company,
            location=location_str or None,
            is_remote=is_remote,
            salary_min=None,
            salary_max=None,
            description_raw=clean_desc,
            skills_required=[],
            url=source_url,
            source_url=source_url,
            apply_url=apply_url,
            posted_at=posted_at or datetime.now(timezone.utc),
            dedup_key=dedup_key,
        )
        self.db.add(new_job)
        await self.db.commit()
        await self.db.refresh(new_job)
        return new_job

    async def _fetch_page_text(self, url: str) -> str:
        headers = {"User-Agent": USER_AGENT}
        try:
            async with httpx.AsyncClient(headers=headers, timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                for s in soup(["script", "style", "nav", "footer", "header"]):
                    s.decompose()
                text = soup.get_text(separator="\n")
                lines = (line.strip() for line in text.splitlines())
                return "\n".join(chunk for chunk in lines if chunk)
        except Exception as e:
            logger.warning(f"Failed fetching page text from {url}: {e}")
            return f"Job posting at URL: {url}"

    async def _find_existing_job(
        self, source: str, external_id: str, dedup_key: str | None
    ) -> Job | None:
        stmt = select(Job).where(
            (Job.source == source) & (Job.external_id == external_id)
        )
        res = await self.db.execute(stmt)
        existing = res.scalars().first()
        if existing:
            return existing

        if dedup_key:
            dedup_stmt = select(Job).where(Job.dedup_key == dedup_key)
            dedup_res = await self.db.execute(dedup_stmt)
            return dedup_res.scalars().first()

        return None
