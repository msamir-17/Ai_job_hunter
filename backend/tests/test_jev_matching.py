import uuid
import pytest

from app.models import CandidateProfile, Job
from app.schemas.matching import JevJobEvalResult
from app.services.jev_matching import JevMatchingService


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_jev_service_evaluation():
    """Verify JevMatchingService evaluates job fit and enforces experience ceiling."""
    cand = CandidateProfile(
        id=uuid.uuid4(),
        headline="Junior ML Engineer",
        target_titles=["AI Engineer", "Machine Learning Engineer"],
        skills=["Python", "PyTorch", "FastAPI"],
        experience=[],
    )

    # Job A: Matches skills & within 3 years cap
    job_good = Job(
        id=uuid.uuid4(),
        title="Junior AI Engineer",
        company="Startup A",
        location="Remote",
        is_remote=True,
        skills_required=["Python", "PyTorch"],
        description_raw="We are looking for a Junior AI Engineer with Python skills. Entry level.",
    )

    # Job B: Senior role requiring over 3 years
    job_senior = Job(
        id=uuid.uuid4(),
        title="Senior Staff AI Engineer",
        company="BigTech B",
        location="Remote",
        is_remote=True,
        skills_required=["Python", "C++", "CUDA"],
        description_raw="Requires 8+ years experience leading machine learning teams.",
    )

    service = JevMatchingService(confidence_threshold=0.60)

    # Evaluate Good Job (expect pass)
    res_good = await service.evaluate_job_fit(candidate=cand, job=job_good, max_experience_years=3.0)
    assert isinstance(res_good, JevJobEvalResult)
    assert res_good.meets_experience_ceiling is True
    assert res_good.domain_fit in ("Direct Fit", "Adjacent Role")
    assert res_good.skill_score >= 3
    assert res_good.passed_jev_filter is True

    # Evaluate Senior Job (expect filtered out due to senior role > 3 years ceiling)
    res_senior = await service.evaluate_job_fit(candidate=cand, job=job_senior, max_experience_years=3.0)
    assert res_senior.meets_experience_ceiling is False
    assert res_senior.passed_jev_filter is False


@pytest.mark.anyio
async def test_jev_batch_evaluation():
    """Verify batch evaluation returns proper results for all jobs."""
    cand = CandidateProfile(
        id=uuid.uuid4(),
        headline="AI Fresher",
        target_titles=["Python Developer"],
        skills=["Python", "SQL"],
        experience=[],
    )

    jobs = [
        Job(
            id=uuid.uuid4(),
            title="Junior Python Developer",
            company="Co 1",
            skills_required=["Python"],
            description_raw="Entry level python developer.",
        ),
        Job(
            id=uuid.uuid4(),
            title="Senior Principal Architect",
            company="Co 2",
            skills_required=["Java", "Go"],
            description_raw="10+ years experience required.",
        ),
    ]

    service = JevMatchingService()
    results = await service.evaluate_batch(cand, jobs, max_experience_years=3.0)
    assert len(results) == 2
    assert results[0].meets_experience_ceiling is True
    assert results[1].meets_experience_ceiling is False
