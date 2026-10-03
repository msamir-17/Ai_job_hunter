import uuid
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.llm.base import BaseLLMProvider
from app.models import CandidateProfile, Job, JobMatch
from app.schemas.tailoring import (
    TailoredCoverLetterDraft,
    TailoredResumeBullet,
    TailoredResumeDraft,
)
from app.services.document_tailoring import (
    DocumentTailoringService,
    extract_job_required_terms,
    extract_verified_candidate_terms,
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
    return AsyncMock(spec=BaseLLMProvider)


def test_extract_verified_candidate_terms():
    """Verify term extraction normalizes skills, target titles, and headline words."""
    cand = CandidateProfile(
        headline="AI & PyTorch Engineer",
        target_titles=["Machine Learning Engineer"],
        skills=["Python", "PyTorch", {"name": "FastAPI"}],
    )
    terms = extract_verified_candidate_terms(cand)

    assert "python" in terms
    assert "pytorch" in terms
    assert "fastapi" in terms
    assert "machine learning engineer" in terms


def test_audit_text_passes_when_grounded():
    """Verify auditor passes text containing only verified candidate skills."""
    cand = CandidateProfile(
        headline="AI Engineer",
        skills=["Python", "PyTorch", "FastAPI"],
    )
    job = Job(
        title="ML Engineer",
        company="AI Labs",
        skills_required=["Python", "PyTorch", "CUDA", "Kubernetes"],
    )

    service = DocumentTailoringService(db=AsyncMock())
    clean_text = "Designed and deployed neural network models using Python and PyTorch within FastAPI services."

    audit = service.audit_text_for_hallucinations(
        text=clean_text,
        candidate=cand,
        job=job,
    )

    assert audit.is_grounded is True
    assert len(audit.hallucinated_terms) == 0
    assert "python" in audit.verified_terms_used
    assert "pytorch" in audit.verified_terms_used
    assert "fastapi" in audit.verified_terms_used
    assert "Audit PASSED" in audit.audit_explanation


def test_audit_text_flags_hallucinated_terms():
    """Verify auditor flags unverified technical skills required by job that appear in text."""
    cand = CandidateProfile(
        headline="Junior AI Developer",
        skills=["Python", "FastAPI"],  # Does NOT have Kubernetes or CUDA
    )
    job = Job(
        title="Senior Infrastructure AI Engineer",
        company="Scale Systems",
        skills_required=["Python", "Kubernetes", "CUDA", "Docker"],
    )

    service = DocumentTailoringService(db=AsyncMock())
    # Candidate text falsely claims experience with Kubernetes and CUDA
    hallucinated_text = (
        "Architected scalable model serving using Kubernetes clusters and optimized kernels with CUDA."
    )

    audit = service.audit_text_for_hallucinations(
        text=hallucinated_text,
        candidate=cand,
        job=job,
    )

    assert audit.is_grounded is False
    assert "kubernetes" in audit.hallucinated_terms
    assert "cuda" in audit.hallucinated_terms
    assert "Audit FAILED" in audit.audit_explanation


@pytest.mark.anyio
async def test_generate_tailored_bullets(mock_db, mock_llm_provider):
    """Verify tailored resume bullets generation invokes provider with strict system prompt."""
    mock_llm_provider.generate_structured.return_value = TailoredResumeDraft(
        target_role="AI Engineer",
        company_name="Neural AI",
        bullets=[
            TailoredResumeBullet(
                bullet_point="Engineered PyTorch neural pipelines processing 1M tokens/sec.",
                relevant_skill="PyTorch",
                source_experience_company="AI Labs",
                grounding_rationale="Derived from ML Intern role at AI Labs.",
            )
        ],
    )

    cand = CandidateProfile(id=uuid.uuid4(), headline="AI Engineer", skills=["Python", "PyTorch"])
    job = Job(id=uuid.uuid4(), title="AI Engineer", company="Neural AI")

    service = DocumentTailoringService(db=mock_db, provider=mock_llm_provider)
    result = await service.generate_tailored_bullets(candidate=cand, job=job)

    assert len(result.bullets) == 1
    assert result.bullets[0].relevant_skill == "PyTorch"
    assert "AI Labs" in result.bullets[0].source_experience_company

    call_args = mock_llm_provider.generate_structured.call_args[1]
    assert "<candidate_profile_data>" in call_args["user_prompt"]
    assert "ZERO-HALLUCINATION RULES" in call_args["system_prompt"]


@pytest.mark.anyio
async def test_generate_cover_letter(mock_db, mock_llm_provider):
    """Verify cover letter generation invokes provider and returns structured draft."""
    mock_llm_provider.generate_structured.return_value = TailoredCoverLetterDraft(
        recipient="Hiring Team",
        opening_paragraph="I am excited to apply for the AI Engineer role.",
        body_paragraphs=["During my time at AI Labs, I developed PyTorch models."],
        closing_paragraph="I look forward to discussing how my verified experience aligns with your team.",
        full_text="Dear Hiring Team,\n\nI am excited to apply...",
        highlighted_skills=["PyTorch", "Python"],
    )

    cand = CandidateProfile(id=uuid.uuid4(), headline="AI Engineer", skills=["Python", "PyTorch"])
    job = Job(id=uuid.uuid4(), title="AI Engineer", company="Neural AI")

    service = DocumentTailoringService(db=mock_db, provider=mock_llm_provider)
    result = await service.generate_cover_letter(candidate=cand, job=job)

    assert result.recipient == "Hiring Team"
    assert "PyTorch" in result.highlighted_skills
    assert len(result.body_paragraphs) == 1


@pytest.mark.anyio
async def test_generate_application_package_not_found(mock_db):
    """Raises ValueError when candidate profile or job is not found."""
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_res

    service = DocumentTailoringService(db=mock_db)
    with pytest.raises(ValueError, match="CandidateProfile with ID"):
        await service.generate_application_package(uuid.uuid4(), uuid.uuid4())
