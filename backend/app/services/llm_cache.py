"""
Content-Hash LLM Result Caching Service.
Computes SHA-256 hashes of (Job Description + Candidate Skills) to eliminate redundant LLM API calls,
reducing API costs to $0 for recurring or identical job postings.
"""
import hashlib
import json
from typing import Dict, Any, Optional

# In-memory LRU cache fallback
_MEMORY_LLM_CACHE: Dict[str, Dict[str, Any]] = {}


def compute_content_hash(candidate_skills: list, job_title: str, job_description: str) -> str:
    """
    Compute a deterministic SHA-256 hash for candidate skill set and job details.
    """
    cleaned_skills = sorted(list(set(str(s).strip().lower() for s in (candidate_skills or []))))
    raw_payload = f"SKILLS:{','.join(cleaned_skills)}|TITLE:{job_title.strip().lower()}|DESC:{job_description.strip()}"
    return hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()


class LLMCacheService:
    """Service to get/set cached LLM structured match responses."""

    @staticmethod
    def get_cached_result(content_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached LLM match result if content hash exists."""
        return _MEMORY_LLM_CACHE.get(content_hash)

    @staticmethod
    def set_cached_result(content_hash: str, match_result: Dict[str, Any]) -> None:
        """Store LLM match result in cache indexed by content hash."""
        _MEMORY_LLM_CACHE[content_hash] = match_result

    @staticmethod
    def clear_cache() -> None:
        """Clear memory cache (used for unit testing)."""
        _MEMORY_LLM_CACHE.clear()
