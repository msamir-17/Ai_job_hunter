"""
JobSpy Job Source Adapter.
Aggregates live job postings directly from LinkedIn, Indeed, Glassdoor, and ZipRecruiter
using the open-source python-jobspy library.
Does NOT require any API keys.
"""
import asyncio
import logging
import re
from datetime import date, datetime, timezone
from typing import Any
import pandas as pd

from app.adapters.base import BaseJobSourceAdapter

logger = logging.getLogger("ai_job_hunter.adapters.jobspy")

DEFAULT_SITES = ["linkedin", "indeed", "glassdoor"]
DEFAULT_SEARCH_TERM = "Software Engineer"
DEFAULT_LOCATION = "India"
DEFAULT_COUNTRY_INDEED = "india"

INDIAN_LOCATIONS = {
    "india", "bengaluru", "bangalore", "mumbai", "delhi", "hyderabad",
    "pune", "chennai", "noida", "gurugram", "gurgaon", "kolkata",
    "ahmedabad", "jaipur", "kochi", "chandigarh", "indore"
}


def sanitize_location_and_remote(
    location: str | None,
    is_remote: bool | None,
    default_location: str = DEFAULT_LOCATION,
) -> tuple[str, bool | None]:
    """
    Ensures 'Remote' is treated strictly as a work arrangement / job mode, NEVER a geographic location.
    If location is 'remote', 'wfh', etc., maps geographic location to default (e.g. 'India')
    and marks is_remote=True.
    """
    if not location or not location.strip():
        return default_location, is_remote

    loc_str = location.strip()
    loc_lower = loc_str.lower()

    if loc_lower in ("remote", "wfh", "work from home", "anywhere"):
        return default_location, True

    if "remote" in loc_lower or "wfh" in loc_lower:
        cleaned = re.sub(r"\b(remote|wfh|work from home)\b", "", loc_str, flags=re.IGNORECASE)
        cleaned = re.sub(r"[,/()\s-]+", " ", cleaned).strip()
        final_loc = cleaned if cleaned else default_location
        return final_loc, True

    return loc_str, is_remote


def normalize_job_type(job_type: str | None) -> str | None:
    """Normalizes employment type to python-jobspy accepted JobType string."""
    if not job_type:
        return None
    jt = job_type.lower().replace("-", "").replace(" ", "").strip()
    valid_types = {
        "fulltime": "fulltime",
        "parttime": "parttime",
        "contract": "contract",
        "internship": "internship",
        "temporary": "temporary",
    }
    return valid_types.get(jt)


def detect_country_indeed(location: str | None, default_country: str = DEFAULT_COUNTRY_INDEED) -> str:
    """Intelligently detects whether to target indeed.co.in (India) or other region."""
    if not location or not location.strip():
        return default_country
    loc_lower = location.lower()
    if any(city in loc_lower for city in INDIAN_LOCATIONS):
        return "india"
    if any(us_kw in loc_lower for us_kw in ["usa", "united states", "us ", "california", "new york", "texas"]):
        return "USA"
    if any(uk_kw in loc_lower for uk_kw in ["uk", "united kingdom", "london"]):
        return "UK"
    if any(ca_kw in loc_lower for ca_kw in ["canada", "toronto", "vancouver"]):
        return "Canada"
    return default_country


class JobSpyJobSourceAdapter(BaseJobSourceAdapter):
    """
    Adapter fetching multi-board live job postings from LinkedIn, Indeed,
    and Glassdoor without requiring external API keys.
    Defaults to India region with dynamic city detection.
    Treats geographic location and remote work arrangement as separate dimensions.
    """

    def __init__(
        self,
        sites: list[str] | None = None,
        search_term: str = DEFAULT_SEARCH_TERM,
        location: str = DEFAULT_LOCATION,
        country_indeed: str = DEFAULT_COUNTRY_INDEED,
        is_remote: bool | None = None,
        job_type: str | None = None,
    ):
        self.sites = sites or DEFAULT_SITES
        self.search_term = search_term
        clean_loc, detected_remote = sanitize_location_and_remote(location, is_remote, DEFAULT_LOCATION)
        self.location = clean_loc
        self.country_indeed = country_indeed
        self.is_remote = detected_remote if is_remote is None else is_remote
        self.job_type = job_type

    @property
    def source_name(self) -> str:
        return "jobspy"

    async def fetch_jobs(self, limit: int | None = None, **kwargs: Any) -> list[dict[str, Any]]:
        search_term = kwargs.get("search_term") or self.search_term
        raw_location = kwargs.get("location") or self.location
        raw_is_remote = kwargs.get("is_remote", self.is_remote)
        raw_job_type = kwargs.get("job_type", self.job_type)
        sites = kwargs.get("sites") or self.sites
        results_wanted = limit or 15

        # Sanitize location and remote so 'Remote' is never treated as a geographic location
        clean_location, is_remote = sanitize_location_and_remote(
            raw_location, raw_is_remote, default_location=DEFAULT_LOCATION
        )
        normalized_jt = normalize_job_type(raw_job_type)
        country = kwargs.get("country_indeed") or detect_country_indeed(clean_location, self.country_indeed)

        logger.info(
            f"JobSpy fetching up to {results_wanted} jobs for '{search_term}' "
            f"in location='{clean_location}' (is_remote={is_remote}, job_type={normalized_jt}, country_indeed='{country}') from sites: {sites}"
        )

        scrape_kwargs: dict[str, Any] = {
            "site_name": sites,
            "search_term": search_term,
            "location": clean_location,
            "results_wanted": results_wanted,
            "country_indeed": country,
        }
        if is_remote is not None:
            scrape_kwargs["is_remote"] = is_remote
        if normalized_jt:
            scrape_kwargs["job_type"] = normalized_jt

        try:
            from jobspy import scrape_jobs

            df = await asyncio.to_thread(
                scrape_jobs,
                **scrape_kwargs,
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

            # Handle location & remote arrangement accurately
            loc = row.get("location")
            location_str = str(loc).strip() if loc and not pd.isna(loc) else None
            
            raw_row_remote = row.get("is_remote")
            if raw_row_remote is not None and not pd.isna(raw_row_remote):
                job_is_remote = bool(raw_row_remote)
            else:
                wfh_type = str(row.get("work_from_home_type") or "").lower()
                job_is_remote = (
                    "remote" in wfh_type
                    or bool(location_str and "remote" in location_str.lower())
                )

            if location_str and location_str.lower() in ("remote", "remote only"):
                location_str = f"Remote, {clean_location}"
            elif not location_str:
                location_str = clean_location

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
                "is_remote": job_is_remote,
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
