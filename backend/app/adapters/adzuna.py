import logging
from typing import Any
import httpx
from app.adapters.base import BaseJobSourceAdapter
from app.config import settings

logger = logging.getLogger(__name__)

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs"


class AdzunaJobSourceAdapter(BaseJobSourceAdapter):
    """
    Job source adapter for Adzuna Job Search API (aggregating Naukri, Indeed, LinkedIn, etc.)
    """

    def __init__(self, country: str = "in", app_id: str | None = None, app_key: str | None = None):
        self.country = country.lower()
        self.app_id = app_id or settings.ADZUNA_APP_ID
        self.app_key = app_key or settings.ADZUNA_APP_KEY

    @property
    def source_name(self) -> str:
        return "adzuna"

    async def fetch_jobs(
        self, limit: int | None = None, query: str = "software python ai ml", **kwargs: Any
    ) -> list[dict[str, Any]]:
        """
        Fetches live jobs from Adzuna API for target country and search query.
        """
        if not self.app_id or not self.app_key or self.app_id == "your_adzuna_app_id_here":
            raise ValueError("ADZUNA_APP_ID and ADZUNA_APP_KEY must be configured in settings or environment.")

        results_per_page = limit or 20
        url = f"{ADZUNA_BASE_URL}/{self.country}/search/1"
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": results_per_page,
            "what": query,
            "content-type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
        except Exception as err:
            raise RuntimeError(f"Failed to fetch jobs from Adzuna API: {str(err)}") from err

        raw_results = data.get("results", [])
        return self._transform_adzuna_payload(raw_results, limit=limit)

    def _transform_adzuna_payload(
        self, results: list[dict[str, Any]], limit: int | None = None
    ) -> list[dict[str, Any]]:
        transformed: list[dict[str, Any]] = []

        for item in results:
            if limit is not None and len(transformed) >= limit:
                break

            external_id = str(item.get("id") or "")
            if not external_id:
                continue

            title = str(item.get("title") or "")
            # Strip HTML tags if any in title or description
            company_info = item.get("company") or {}
            company = company_info.get("display_name") or "Direct Hire"
            
            location_info = item.get("location") or {}
            display_location = location_info.get("display_name") or "India"

            description = item.get("description") or ""
            url = item.get("redirect_url") or None
            
            salary_min = item.get("salary_min")
            salary_max = item.get("salary_max")
            
            # Simple keyword extraction for required skills from title + description
            skills_extracted: list[str] = []
            combined_text = f"{title} {description}".lower()
            for tech in ["python", "javascript", "react", "node", "fastapi", "pytorch", "tensorflow", "docker", "aws", "postgresql", "sql", "java", "c++", "mlops"]:
                if tech in combined_text:
                    skills_extracted.append(tech.capitalize())

            is_remote = "remote" in display_location.lower() or "remote" in combined_text

            raw_dict = {
                "external_id": external_id,
                "title": title,
                "company": company,
                "location": display_location,
                "is_remote": is_remote,
                "salary_min": int(salary_min) if salary_min is not None else None,
                "salary_max": int(salary_max) if salary_max is not None else None,
                "raw_description": description,
                "skills_required": skills_extracted,
                "url": url,
            }
            transformed.append(raw_dict)

        return transformed
