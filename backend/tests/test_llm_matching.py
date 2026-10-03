import uuid
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.llm.base import BaseLLMProvider
from app.models import CandidateProfile, Job, JobMatch
from app.schemas.matching import SkillGapAnalysis
from app.services.llm_matching import (
    LLMMatchingService,
    format_candidate_for_prompt,
    format_job_for_prompt,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def mock_db():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_llm_provider():
    provider = AsyncMock(spec=BaseLLMProvider)
    return provider


def test_format_candidate_for_prompt():
    """Verify format_candidate_for_prompt formats only verified candidate fields."""
    cand = CandidateProfile(
        headline="Senior AI/ML Engineer",
        target_titles=["AI Engineer", "ML Researcher"],
        skills=["Python", "PyTorch", "pgvector"],
        summary="Building production vector search systems.",
        experience=[
            {
                "title": "Machine Learning Engineer",
                "company": "DeepTech",
                "description": "Architected pgvector similarity search.",
            }
        ],
        education=[
            {
                "degree": "M.S.",
                "field_of_study": "Computer Science",
                "institution": "Stanford",
            }
        ],
    )
    formatted = format_candidate_for_prompt(cand)

    assert "Headline: Senior AI/ML Engineer" in formatted
    assert "Target Roles: AI Engineer, ML Researcher" in formatted
    assert "Verified Skills: Python, PyTorch, pgvector" in formatted
    assert "Summary: Building production vector search systems." in formatted
    assert "Machine Learning Engineer at DeepTech" in formatted
    assert "M.S. - Computer Science - Stanford" in formatted


def test_format_candidate_for_prompt_empty():
    """Verify empty profile returns fallback string."""
    cand = CandidateProfile()
    assert format_candidate_for_prompt(cand) == "Candidate has an empty profile."


def test_format_job_for_prompt():
    """Verify format_job_for_prompt formats job details accurately."""
    job = Job(
        title="Lead Machine Learning Engineer",
        company="Vector Corp",
        location="San Francisco, CA",
        is_remote=True,
        skills_required=["Python", "PyTorch", "Docker"],
        description_raw="We need a strong ML engineer for our retrieval pipeline.",
    )
    formatted = format_job_for_prompt(job)

    assert "Title: Lead Machine Learning Engineer" in formatted
    assert "Company: Vector Corp" in formatted
    assert "Location: San Francisco, CA (Remote: True)" in formatted
    assert "Required Skills List: Python, PyTorch, Docker" in formatted
    assert "Job Description:\nWe need a strong ML engineer" in formatted


@pytest.mark.anyio
async def test_evaluate_match_shortlisted(mock_db, mock_llm_provider):
    """Verify score >= 65 assigns 'shortlisted' status and updates JobMatch."""
    mock_llm_provider.generate_structured.return_value = SkillGapAnalysis(
        llm_score=85,
        matched_skills=["Python", "PyTorch"],
        missing_required_skills=[],
        missing_preferred_skills=["Docker"],
        analysis_summary="Strong match across required core ML skills.",
        recommendation="strong_match",
    )

    cand = CandidateProfile(id=uuid.uuid4(), headline="AI Engineer", skills=["Python", "PyTorch"])
    job = Job(id=uuid.uuid4(), title="AI Engineer", company="Tech Corp")
    match = JobMatch(
        candidate_profile_id=cand.id,
        job_id=job.id,
        passed_deterministic=True,
        vector_score=0.91,
        status="review",
    )

    service = LLMMatchingService(db=mock_db, provider=mock_llm_provider)
    result = await service.evaluate_match(candidate=cand, job=job, match=match)

    assert result.llm_score == 85
    assert result.status == "shortlisted"
    assert match.status == "shortlisted"
    assert match.llm_score == 85
    assert match.matched_skills == ["Python", "PyTorch"]
    assert match.missing_skills == ["Docker"]
    assert result.recommendation == "strong_match"

    # Verify untrusted data boundary tags in LLM call
    call_args = mock_llm_provider.generate_structured.call_args[1]
    assert "<candidate_profile_data>" in call_args["user_prompt"]
    assert "</candidate_profile_data>" in call_args["user_prompt"]
    assert "<job_posting_data>" in call_args["user_prompt"]
    assert "</job_posting_data>" in call_args["user_prompt"]


@pytest.mark.anyio
async def test_evaluate_match_review_and_rejected(mock_db, mock_llm_provider):
    """Verify score 40-64 assigns 'review' and score < 40 assigns 'rejected'."""
    cand = CandidateProfile(id=uuid.uuid4(), headline="Junior Developer")
    job = Job(id=uuid.uuid4(), title="Staff ML Engineer", company="AI Labs")
    match1 = JobMatch(candidate_profile_id=cand.id, job_id=job.id, passed_deterministic=True)

    # Moderate score (50) -> 'review'
    mock_llm_provider.generate_structured.return_value = SkillGapAnalysis(
        llm_score=50,
        matched_skills=["Python"],
        missing_required_skills=["Distributed Systems", "CUDA"],
        missing_preferred_skills=[],
        analysis_summary="Candidate knows Python but lacks required systems experience.",
        recommendation="moderate_match",
    )

    service = LLMMatchingService(db=mock_db, provider=mock_llm_provider)
    res1 = await service.evaluate_match(candidate=cand, job=job, match=match1)
    assert res1.status == "review"
    assert match1.status == "review"

    # Low score (25) -> 'rejected'
    match2 = JobMatch(candidate_profile_id=cand.id, job_id=job.id, passed_deterministic=True)
    mock_llm_provider.generate_structured.return_value = SkillGapAnalysis(
        llm_score=25,
        matched_skills=[],
        missing_required_skills=["CUDA", "PyTorch", "C++"],
        missing_preferred_skills=["Triton"],
        analysis_summary="Major technical mismatch.",
        recommendation="weak_match",
    )
    res2 = await service.evaluate_match(candidate=cand, job=job, match=match2)
    assert res2.status == "rejected"
    assert match2.status == "rejected"


@pytest.mark.anyio
async def test_analyze_single_match_not_found(mock_db, mock_llm_provider):
    """Raises ValueError when candidate profile or job is not found."""
    mock_res_empty = MagicMock()
    mock_res_empty.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_res_empty

    service = LLMMatchingService(db=mock_db, provider=mock_llm_provider)
    with pytest.raises(ValueError, match="CandidateProfile with ID"):
        await service.analyze_single_match(uuid.uuid4(), uuid.uuid4())
