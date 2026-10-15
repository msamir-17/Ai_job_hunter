"""
Unit tests for Archetype Lens Configurations and Dynamic Role Classifier.
Verifies preset integrity, layout priority ordering, and intelligent JD classification.
"""
import pytest
from app.core.archetypes import (
    classify_job_archetype,
    get_archetype,
    list_available_archetypes,
)


def test_list_and_get_archetypes():
    """Verify built-in archetypes exist and have required layout properties."""
    archetypes = list_available_archetypes()
    assert len(archetypes) == 4
    ids = {a.archetype_id for a in archetypes}
    assert ids == {"genai", "swe", "ai_eng", "data"}

    # Test retrieval
    swe = get_archetype("swe")
    assert swe.archetype_id == "swe"
    assert swe.primary_angle == "swe"
    assert swe.skill_category_order[0] == "Backend & Systems"

    # Test fallback
    fallback = get_archetype("nonexistent_role")
    assert fallback.archetype_id == "genai"


def test_classify_genai_job():
    """Verify GenAI/LLM job postings are classified to genai archetype."""
    result = classify_job_archetype(
        job_title="Senior Generative AI Application Engineer",
        job_description="We are looking for an LLM specialist experienced in LangGraph, RAG, prompt engineering, and Ragas evaluation.",
        skills_required=["Python", "LangChain", "RAG", "LLMs"],
    )
    assert result.recommended_archetype_id == "genai"
    assert result.confidence_score > 0.40
    assert "genai" in result.archetype_weights
    assert any("llm" in kw.lower() or "rag" in kw.lower() for kw in result.extracted_keywords)


def test_classify_backend_swe_job():
    """Verify Backend/Distributed systems postings are classified to swe archetype."""
    result = classify_job_archetype(
        job_title="Backend Software Engineer (FastAPI / PostgreSQL)",
        job_description="Seeking a backend engineer to design REST APIs, optimize PostgreSQL queries, build microservices, and manage distributed task queues.",
        skills_required=["FastAPI", "PostgreSQL", "Docker", "AsyncIO"],
    )
    assert result.recommended_archetype_id == "swe"
    assert result.confidence_score > 0.40
    assert result.archetype_weights["swe"] > result.archetype_weights["genai"]


def test_classify_ml_ai_eng_job():
    """Verify Deep Learning / Model training postings are classified to ai_eng archetype."""
    result = classify_job_archetype(
        job_title="Machine Learning Engineer - Deep Learning",
        job_description="Responsible for PyTorch neural network training, transformer fine-tuning, and dense vector embeddings.",
        skills_required=["PyTorch", "Deep Learning", "Transformers", "NLP"],
    )
    assert result.recommended_archetype_id == "ai_eng"
    assert result.archetype_weights["ai_eng"] > 0.35


def test_classify_empty_or_sparse_job():
    """Verify sparse or ambiguous job descriptions return a balanced fallback result."""
    result = classify_job_archetype(
        job_title="General Engineer",
        job_description="Join our fast-paced company and solve hard problems.",
        skills_required=[],
    )
    assert result.recommended_archetype_id in {"genai", "swe", "ai_eng", "data"}
    # Weights should sum to 1.0
    total_weights = sum(result.archetype_weights.values())
    assert pytest.approx(total_weights, 0.01) == 1.0
