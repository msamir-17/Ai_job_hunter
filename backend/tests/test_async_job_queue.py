"""
Unit tests for Async Job Queue, Content-Hash LLM Cache, and Pipeline State Machine.
"""
import pytest
from app.services.llm_cache import compute_content_hash, LLMCacheService
from app.services.job_queue import PipelineStatus


def test_content_hash_deterministic():
    """Test compute_content_hash returns identical SHA-256 for identical inputs regardless of skill ordering."""
    skills_1 = ["Python", "FastAPI", "PyTorch"]
    skills_2 = ["PyTorch", "python", "FASTAPI "]
    
    hash_1 = compute_content_hash(skills_1, "AI Engineer", "Build ML systems.")
    hash_2 = compute_content_hash(skills_2, "AI Engineer", "Build ML systems.")
    
    assert hash_1 == hash_2
    assert len(hash_1) == 64 # SHA-256 length


def test_llm_cache_service():
    """Test LLMCacheService get and set operations."""
    LLMCacheService.clear_cache()
    
    c_hash = compute_content_hash(["Python"], "Backend Engineer", "Job desc text.")
    assert LLMCacheService.get_cached_result(c_hash) is None

    payload = {"vector_score": 0.88, "llm_score": 88}
    LLMCacheService.set_cached_result(c_hash, payload)
    
    cached = LLMCacheService.get_cached_result(c_hash)
    assert cached is not None
    assert cached["vector_score"] == 0.88
    assert cached["llm_score"] == 88


def test_pipeline_status_constants():
    """Test PipelineStatus state machine string constants."""
    assert PipelineStatus.INGESTED == "ingested"
    assert PipelineStatus.FILTERED == "filtered"
    assert PipelineStatus.SCORED == "scored"
    assert PipelineStatus.TAILORED == "tailored"
    assert PipelineStatus.NOTIFIED == "notified"
