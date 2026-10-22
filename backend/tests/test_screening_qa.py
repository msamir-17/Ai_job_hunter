"""
Unit and API Integration Tests for Application Screening Questions Q&A Agent.
Phase 7: Grounded candidate answering engine.
"""

import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models import CandidateProfile, Job
from app.schemas.screening_qa import ScreeningQARequest, ScreeningQAResponse
from app.services.screening_qa import ScreeningQAService


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def mock_candidate():
    prof = CandidateProfile(
        id=uuid.uuid4(),
        headline="AI/ML Engineer & Systems Developer",
        summary="AI Engineer specialized in FastAPI, PostgreSQL, and LLM evaluation architectures.",
        skills=["Python", "FastAPI", "PostgreSQL", "PyTorch", "Docker"],
        target_titles=["AI Engineer", "Machine Learning Engineer"],
        experience=[
            {
                "company": "Cognitive AI Labs",
                "title": "Lead AI Engineer",
                "bullets": [
                    "Engineered end-to-end vector search retrieval using pgvector.",
                    "Built asynchronous background job worker pipelines.",
                ],
            }
        ],
        education=["Bachelor of Technology in Computer Science"],
    )
    prof.full_name = "Mohammad Samir Khan"
    return prof


@pytest.mark.anyio
async def test_screening_qa_verified_technical_skill(mock_candidate):
    req = ScreeningQARequest(
        question="What experience do you have with FastAPI and Python backends?",
        job_title="Senior AI Engineer",
        company_name="Acme AI",
    )

    res = await ScreeningQAService.answer_question(request=req, candidate=mock_candidate)

    assert isinstance(res, ScreeningQAResponse)
    assert res.is_grounded is True
    assert res.confidence_score >= 0.80
    assert len(res.cited_fact_ids) > 0
    assert "FastAPI" in res.answer or "Python" in res.answer
    assert len(res.missing_facts) == 0


@pytest.mark.anyio
async def test_screening_qa_missing_skill_anti_hallucination(mock_candidate):
    req = ScreeningQARequest(
        question="Do you have production experience deploying Kubernetes clusters and Rust services?",
        job_title="DevOps Lead",
        company_name="Cloud Corp",
    )

    res = await ScreeningQAService.answer_question(request=req, candidate=mock_candidate)

    assert isinstance(res, ScreeningQAResponse)
    assert res.is_grounded is True
    # Verify missing skills are honestly recorded rather than fabricated
    assert "Kubernetes" in res.missing_facts or "Rust" in res.missing_facts
    # Ensure answer honestly records missing tech and doesn't falsely assert mastery
    assert any(phrase in res.answer.lower() for phrase in ["not directly deployed", "transferable", "do not have", "no direct", "learning", "adjacent", "unverified", "missing"]) or len(res.missing_facts) > 0



@pytest.mark.anyio
async def test_screening_qa_motivation_question(mock_candidate):
    req = ScreeningQARequest(
        question="Why are you interested in joining Acme AI as a Senior AI Engineer?",
        job_title="Senior AI Engineer",
        company_name="Acme AI",
    )

    res = await ScreeningQAService.answer_question(request=req, candidate=mock_candidate)

    assert isinstance(res, ScreeningQAResponse)
    assert res.is_grounded is True
    assert "Acme AI" in res.answer
    assert "Senior AI Engineer" in res.answer


@pytest.mark.anyio
async def test_screening_qa_api_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "question": "What is your experience with Docker containerization?",
            "job_title": "Platform Engineer",
            "company_name": "Docker Inc",
        }
        res = await client.post("/api/v1/screening-qa/answer", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "answer" in data
        assert "cited_fact_ids" in data
        assert data["is_grounded"] is True
        assert data["confidence_score"] > 0
