"""
JobSpy Job Source Adapter.
Aggregates live job postings directly from LinkedIn, Indeed, Glassdoor, and ZipRecruiter
using the open-source python-jobspy library.
Does NOT require any API keys.
"""
import asyncio
import logging
from datetime import date, datetime, timezone
from typing import Any
import pandas as pd

from app.adapters.base import BaseJobSourceAdapter

logger = logging.getLogger("ai_job_hunter.adapters.jobspy")

DEFAULT_SITES = ["linkedin", "indeed", "glassdoor"]
DEFAULT_SEARCH_TERM = "Software Engineer"
DEFAULT_LOCATION = "Remote"


class JobSpyJobSourceAdapter(BaseJobSourceAdapter):
    """
    Adapter fetching multi-board live job postings from LinkedIn, Indeed,
    and Glassdoor without requiring external API keys.
    """

    def __init__(
        self,
        sites: list[str] | None = None,
        search_term: str = DEFAULT_SEARCH_TERM,
        location: str = DEFAULT_LOCATION,
        country_indeed: str = "USA",
    ):
        self.sites = sites or DEFAULT_SITES
        self.search_term = search_term
        self.location = location
        self.country_indeed = country_indeed

    @property
    def source_name(self) -> str:
        return "jobspy"

    async def fetch_jobs(self, limit: int | None = None, **kwargs: Any) -> list[dict[str, Any]]:
        search_term = kwargs.get("search_term") or self.search_term
        location = kwargs.get("location") or self.location
        sites = kwargs.get("sites") or self.sites
        results_wanted = limit or 15

        logger.info(
            f"JobSpy fetching up to {results_wanted} jobs for '{search_term}' "
            f"in '{location}' from sites: {sites}"
        )

        try:
            from jobspy import scrape_jobs

            df = await asyncio.to_thread(
                scrape_jobs,
                site_name=sites,
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                country_indeed=self.country_indeed,
            )
        except Exception as e:
            logger.error(f"JobSpy scraping failed: {e}", exc_info=True)
            return []

        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            logger.info("JobSpy returned no jobs for query.")
            return []

        normalized_jobs: list[dict[str, Any]] = []

        for _, row in df.iterrows():
            title = str(row.get("title") or "").strip()
            company = str(row.get("company") or "").strip()
            if not title or not company:
                continue

            site = str(row.get("site") or "jobspy").lower().strip()
            external_id = str(row.get("id") or "").strip()
            if not external_id:
                # Fallback deterministic id
                external_id = f"{site}-{hash((company, title))}"

            job_url = str(row.get("job_url") or "").strip() or None
            job_url_direct = str(row.get("job_url_direct") or "").strip() or None
            apply_url = job_url_direct or job_url
            source_url = job_url or job_url_direct

            # Handle location
            loc = row.get("location")
            location_str = str(loc).strip() if loc and not pd.isna(loc) else None
            is_remote = bool(row.get("is_remote")) if not pd.isna(row.get("is_remote")) else False
            if location_str and "remote" in location_str.lower():
                is_remote = True

            # Handle salaries
            salary_min = None
            salary_max = None
            min_amt = row.get("min_amount")
            max_amt = row.get("max_amount")
            if min_amt is not None and not pd.isna(min_amt):
                try:
                    salary_min = int(float(min_amt))
                except (ValueError, TypeError):
                    salary_min = None
            if max_amt is not None and not pd.isna(max_amt):
                try:
                    salary_max = int(float(max_amt))
                except (ValueError, TypeError):
                    salary_max = None

            # Handle date_posted
            posted_at = None
            date_val = row.get("date_posted")
            if date_val is not None and not pd.isna(date_val):
                if isinstance(date_val, datetime):
                    posted_at = date_val.replace(tzinfo=timezone.utc) if date_val.tzinfo is None else date_val
                elif isinstance(date_val, date):
                    posted_at = datetime(date_val.year, date_val.month, date_val.day, tzinfo=timezone.utc)
                elif isinstance(date_val, str):
                    try:
                        posted_at = datetime.fromisoformat(date_val).replace(tzinfo=timezone.utc)
                    except Exception:
                        posted_at = None

            raw_desc = str(row.get("description") or "").strip() or None

            normalized_jobs.append({
                "source": site,  # Saves exact source as 'linkedin', 'indeed', etc.
                "external_id": external_id,
                "title": title,
                "company": company,
                "location": location_str,
                "is_remote": is_remote,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "raw_description": raw_desc,
                "skills_required": [],
                "url": apply_url or source_url,
                "source_url": source_url,
                "apply_url": apply_url,
                "posted_at": posted_at,
                "dedup_key": None,
            })

        logger.info(f"JobSpy successfully parsed {len(normalized_jobs)} live postings.")
        if limit is not None and limit > 0:
            return normalized_jobs[:limit]
        return normalized_jobs
