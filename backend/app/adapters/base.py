from abc import ABC, abstractmethod
from typing import Any


class BaseJobSourceAdapter(ABC):
    """
    Abstract interface for job source adapters.

    All source adapters (Remotive, Manual, future JSearch/Greenhouse) must implement
    this contract to convert source-specific payloads into raw dictionary lists for normalization.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Canonical name identifying this job source (e.g., 'remotive', 'manual')."""
        pass

    @abstractmethod
    async def fetch_jobs(self, limit: int | None = None, **kwargs: Any) -> list[dict[str, Any]]:
        """
        Fetches raw job items from the source system or local development cache.

        :param limit: Maximum number of raw jobs to fetch.
        :param kwargs: Additional source-specific options (e.g. use_cache=True).
        :return: List of raw job dictionaries.
        """
        pass
