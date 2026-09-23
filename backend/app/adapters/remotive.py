import json
import re
from pathlib import Path
from typing import Any
import httpx
from app.adapters.base import BaseJobSourceAdapter

REMOTIVE_API_URL = "https://remotive.com/api/remote-jobs"
DEFAULT_CACHE_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "raw" / "remotive_cache.json"


class RemotiveJobSourceAdapter(BaseJobSourceAdapter):
    """
    Job source adapter for Remotive Public Remote Jobs API with local dev caching support.
    """

    def __init__(self, cache_file_path: Path | str | None = None):
        self._cache_file_path = Path(cache_file_path) if cache_file_path else DEFAULT_CACHE_PATH

    @property
    def source_name(self) -> str:
        return "remotive"

    async def fetch_jobs(
        self, limit: int | None = None, use_cache: bool = False, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """
        Fetches raw Remotive jobs from HTTP API or local development cache file.

        :param limit: Maximum number of raw jobs to return.
        :param use_cache: If True, reads strictly from local development cache file.
        :raises FileNotFoundError: If use_cache=True and the cache file does not exist.
        :raises ValueError: If use_cache=True and cache file contains invalid JSON data.
        :raises RuntimeError: If HTTP fetch fails.
        """
        if use_cache:
            return self._load_from_cache(limit=limit)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(REMOTIVE_API_URL, params={"category": "software-dev"})
                response.raise_for_error()
                data = response.json()
        except Exception as err:
            raise RuntimeError(f"Failed to fetch jobs from Remotive API: {str(err)}") from err

        raw_jobs_list = data.get("jobs", [])
        return self._transform_remotive_payload(raw_jobs_list, limit=limit)

    def _load_from_cache(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Reads and transforms raw Remotive jobs from local cache file."""
        if not self._cache_file_path.exists():
            raise FileNotFoundError(
                f"Remotive dev cache file missing at '{self._cache_file_path}'. "
                "Ensure cache file exists before invoking use_cache=True."
            )

        try:
            content = self._cache_file_path.read_text(encoding="utf-8")
            data = json.loads(content)
        except Exception as err:
            raise ValueError(f"Failed to parse Remotive cache file at '{self._cache_file_path}': {str(err)}") from err

        raw_jobs_list = data.get("jobs", []) if isinstance(data, dict) else data
        if not isinstance(raw_jobs_list, list):
            raise ValueError(f"Invalid Remotive cache structure in '{self._cache_file_path}': Expected list of jobs.")

        return self._transform_remotive_payload(raw_jobs_list, limit=limit)

    def _transform_remotive_payload(
        self, remotive_jobs: list[dict[str, Any]], limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Extracts source-specific Remotive keys into standardized raw job dicts.
        Remotive-specific field parsing is strictly isolated inside this method.
        """
        results: list[dict[str, Any]] = []

        for item in remotive_jobs:
            if limit is not None and len(results) >= limit:
                break

            external_id = str(item.get("id") or "")
            if not external_id:
                continue

            title = str(item.get("title") or "")
            company = str(item.get("company_name") or "")
            location = item.get("candidate_required_location") or "Worldwide"
            raw_description = item.get("description") or None
            tags = item.get("tags") or []
            url = item.get("url") or None
            salary_str = item.get("salary") or ""

            salary_min, salary_max = self._parse_salary_bounds(salary_str)

            raw_dict = {
                "external_id": external_id,
                "title": title,
                "company": company,
                "location": str(location) if location else None,
                "is_remote": True,  # Remotive jobs are remote by default
                "salary_min": salary_min,
                "salary_max": salary_max,
                "raw_description": raw_description,
                "skills_required": list(tags) if isinstance(tags, list) else [],
                "url": url,
            }
            results.append(raw_dict)

        return results

    @staticmethod
    def _parse_salary_bounds(salary_str: str) -> tuple[int | None, int | None]:
        """
        Parses numeric min/max annual salary from strings like '$120,000 - $150,000' or '100k - 130k'.
        Returns (salary_min, salary_max) or (None, None) if unparseable.
        """
        if not salary_str or not isinstance(salary_str, str):
            return None, None

        # Look for numbers with optional 'k' or '$'
        matches = re.findall(r"\$?(\d{2,3})[,\s]?(\d{3})?", salary_str.replace("k", "000").replace("K", "000"))
        numbers: list[int] = []
        for m in matches:
            num_str = "".join(m)
            if num_str.isdigit():
                val = int(num_str)
                if 10000 <= val <= 1000000: # Reasonable annual salary range filter
                    numbers.append(val)

        if len(numbers) >= 2:
            return min(numbers[0], numbers[1]), max(numbers[0], numbers[1])
        elif len(numbers) == 1:
            return numbers[0], None

        return None, None
