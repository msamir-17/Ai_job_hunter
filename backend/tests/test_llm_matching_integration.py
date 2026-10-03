import uuid
from unittest.mock import AsyncMock
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.database import AsyncSessionLocal, engine
from app.llm import BaseLLMProvider, get_llm_provider
from app.main import app
from app.models import CandidateProfile, Job, JobMatch, User
from app.schemas.matching import SkillGapAnalysis
from app.services.llm_matching import LLMMatchingService


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def dispose_db_engine():
    yield
    await engine.dispose()


@pytest.mark.anyio
async def test_llm_matching_real_postgres():
    """
    Integration test verifying Stage 3 LLM skill gap analysis, score persistence,
    status updates, and FastAPI REST endpoints against real Docker PostgreSQL (port 5435).
    """
    test_user_id = uuid.uuid4()
    test_email = f"llm_test_{test_user_id.hex[:8]}@example.com"

    candidate_profile_id = None
    job_ids = []

    # Setup mock BaseLLMProvider
    mock_provider = AsyncMock(spec=BaseLLMProvider)
    mock_provider.generate_structured.return_value = SkillGapAnalysis(
        llm_score=88,
        matched_skills=["Python", "PyTorch"],
        missing_required_skills=["pgvector"],
        missing_preferred_skills=["Docker"],
        analysis_summary="Strong candidate with proven PyTorch and Python background.",
        recommendation="strong_match",
    )

    app.dependency_overrides[get_llm_provider] = lambda: mock_provider

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        try:
            # 1. Setup User, CandidateProfile, Job, and JobMatch in real Postgres (port 5435)
            async with AsyncSessionLocal() as db:
                user = User(
                    id=test_user_id,
                    email=test_email,
                    hashed_password="hashed_password",
                    full_name="LLM Match Integration Candidate",
                )
                db.add(user)

                candidate = CandidateProfile(
                    user_id=test_user_id,
                    headline="AI & Machine Learning Engineer",
                    skills=["Python", "PyTorch", "FastAPI"],
                    target_titles=["AI Engineer", "ML Engineer"],
                    experience=[
                        {
                            "title": "AI Intern",
                            "company": "DeepTech",
                            "description": "Trained neural models in PyTorch.",
                        }
                    ],
                )
                db.add(candidate)
                await db.commit()
                await db.refresh(candidate)
                candidate_profile_id = candidate.id

                job1 = Job(
                    source="manual",
                    external_id=f"ext_{uuid.uuid4().hex[:8]}",
                    title="Senior AI Engineer",
                    company="Neural Search Labs",
                    description_raw="Seeking AI Engineer with PyTorch, Python, and pgvector experience.",
                    is_remote=True,
                    skills_required=["Python", "PyTorch", "pgvector"],
                )
                db.add(job1)
                await db.commit()
                await db.refresh(job1)
                job_ids.append(job1.id)

                # Pre-existing match from Stage 1 & Stage 2
                match = JobMatch(
                    candidate_profile_id=candidate.id,
                    job_id=job1.id,
                    passed_deterministic=True,
                    vector_score=0.895,
                    status="review",
                )
                db.add(match)
                await db.commit()

            # 2. Test LLMMatchingService.analyze_single_match
            async with AsyncSessionLocal() as db:
                service = LLMMatchingService(db=db, provider=mock_provider)
                res = await service.analyze_single_match(
                    candidate_profile_id=candidate_profile_id,
                    job_id=job_ids[0],
                )

                assert res.llm_score == 88
                assert res.status == "shortlisted"
                assert "Python" in res.matched_skills
                assert "pgvector" in res.missing_required_skills
                assert res.recommendation == "strong_match"

            # 3. Verify PostgreSQL JobMatch table was persisted with Stage 3 outputs
            async with AsyncSessionLocal() as db:
                stmt = select(JobMatch).where(
                    JobMatch.candidate_profile_id == candidate_profile_id,
                    JobMatch.job_id == job_ids[0],
                )
                res_match = await db.execute(stmt)
                persisted = res_match.scalar_one()

                assert persisted.llm_score == 88
                assert persisted.status == "shortlisted"
                assert persisted.matched_skills == ["Python", "PyTorch"]
                assert "pgvector" in persisted.missing_skills
                assert "Docker" in persisted.missing_skills
                assert persisted.analysis_summary == "Strong candidate with proven PyTorch and Python background."

            # 4. Test FastAPI HTTP Endpoint POST /api/v1/matching/llm/analyze
            resp = await client.post(
                "/api/v1/matching/llm/analyze",
                json={
                    "candidate_profile_id": str(candidate_profile_id),
                    "job_id": str(job_ids[0]),
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["llm_score"] == 88
            assert data["status"] == "shortlisted"
            assert data["recommendation"] == "strong_match"

            # 5. Test FastAPI HTTP Endpoint POST /api/v1/matching/llm/analyze-batch
            batch_resp = await client.post(
                "/api/v1/matching/llm/analyze-batch",
                json={
                    "candidate_profile_id": str(candidate_profile_id),
                    "limit": 5,
                    "min_vector_score": 0.5,
                },
            )
            assert batch_resp.status_code == 200
            batch_data = batch_resp.json()
            assert batch_data["total_analyzed"] == 1
            assert batch_data["results"][0]["job_id"] == str(job_ids[0])
            assert batch_data["results"][0]["llm_score"] == 88

        finally:
            app.dependency_overrides.clear()
            # 6. Cleanup test records from PostgreSQL
            async with AsyncSessionLocal() as db:
                if candidate_profile_id:
                    await db.execute(
                        delete(JobMatch).where(JobMatch.candidate_profile_id == candidate_profile_id)
                    )
                    await db.execute(
                        delete(CandidateProfile).where(CandidateProfile.id == candidate_profile_id)
                    )
                for jid in job_ids:
                    await db.execute(delete(JobMatch).where(JobMatch.job_id == jid))
                    await db.execute(delete(Job).where(Job.id == jid))
                await db.execute(delete(User).where(User.id == test_user_id))
                await db.commit()
