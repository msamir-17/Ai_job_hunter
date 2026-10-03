import math
import uuid
from unittest.mock import AsyncMock
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.database import AsyncSessionLocal, engine
from app.graph.workflow import run_matching_pipeline
from app.llm import BaseLLMProvider, get_llm_provider
from app.main import app
from app.models import CandidateProfile, Job, JobMatch, User
from app.schemas.matching import SkillGapAnalysis


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def dispose_db_engine():
    yield
    await engine.dispose()


def make_unit_vector(angle_rad: float) -> list[float]:
    vec = [0.0] * 384
    vec[0] = math.cos(angle_rad)
    vec[1] = math.sin(angle_rad)
    return vec


@pytest.mark.anyio
async def test_langgraph_pipeline_real_postgres():
    """
    Integration test verifying the compiled LangGraph agent workflow
    against the real Docker PostgreSQL database on port 5435.
    """
    test_user_id = uuid.uuid4()
    test_email = f"graph_test_{test_user_id.hex[:8]}@example.com"

    candidate_profile_id = None
    job_id = None

    mock_llm_provider = AsyncMock(spec=BaseLLMProvider)
    mock_llm_provider.generate_structured.return_value = SkillGapAnalysis(
        llm_score=91,
        matched_skills=["Python", "PyTorch"],
        missing_required_skills=["pgvector"],
        missing_preferred_skills=["Docker"],
        analysis_summary="Grounded match: Candidate excels in PyTorch and Python.",
        recommendation="strong_match",
    )

    app.dependency_overrides[get_llm_provider] = lambda: mock_llm_provider
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        try:
            # 1. Setup User, CandidateProfile, and Job in real Postgres
            async with AsyncSessionLocal() as db:
                user = User(
                    id=test_user_id,
                    email=test_email,
                    hashed_password="hashed_password",
                    full_name="LangGraph Pipeline Candidate",
                )
                db.add(user)

                cand_vec = make_unit_vector(0.0)
                candidate = CandidateProfile(
                    user_id=test_user_id,
                    headline="AI & Machine Learning Engineer",
                    skills=["Python", "PyTorch", "FastAPI"],
                    target_titles=["AI Engineer", "ML Engineer"],
                    experience=[
                        {
                            "title": "Machine Learning Intern",
                            "company": "AI Labs",
                            "start_date": "2023-01-01",
                            "end_date": "2024-01-01",
                            "description": "Trained models in PyTorch.",
                        }
                    ],
                    embedding=cand_vec,
                )
                db.add(candidate)
                await db.commit()
                await db.refresh(candidate)
                candidate_profile_id = candidate.id

                job_vec = make_unit_vector(0.2)  # cos(0.2) ~= 0.98 (very close)
                job = Job(
                    source="manual",
                    external_id=f"ext_{uuid.uuid4().hex[:8]}",
                    title="AI Engineer",
                    company="Neural Search Corp",
                    description_raw="Seeking AI Engineer with 1 year experience in PyTorch and Python.",
                    is_remote=True,
                    skills_required=["Python", "PyTorch", "pgvector"],
                    embedding=job_vec,
                )
                db.add(job)
                await db.commit()
                await db.refresh(job)
                job_id = job.id

            # 2. Execute run_matching_pipeline end-to-end
            async with AsyncSessionLocal() as db:
                final_state = await run_matching_pipeline(
                    db=db,
                    candidate_profile_id=candidate_profile_id,
                    job_id=job_id,
                    llm_provider=mock_llm_provider,
                )

                assert final_state["passed_deterministic"] is True
                assert final_state["vector_passed"] is True
                assert final_state["vector_score"] > 0.9
                assert final_state["llm_score"] == 91
                assert final_state["overall_status"] == "shortlisted"
                assert final_state["current_stage"] == "completed"

            # 3. Verify JobMatch persistence in PostgreSQL
            async with AsyncSessionLocal() as db:
                stmt = select(JobMatch).where(
                    JobMatch.candidate_profile_id == candidate_profile_id,
                    JobMatch.job_id == job_id,
                )
                res = await db.execute(stmt)
                persisted_match = res.scalar_one()

                assert persisted_match.passed_deterministic is True
                assert persisted_match.vector_score > 0.9
                assert persisted_match.llm_score == 91
                assert persisted_match.status == "shortlisted"
                assert "Python" in persisted_match.matched_skills

            # 4. Test HTTP Endpoint POST /api/v1/matching/pipeline/run
            resp = await client.post(
                "/api/v1/matching/pipeline/run",
                json={
                    "candidate_profile_id": str(candidate_profile_id),
                    "job_id": str(job_id),
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["passed_deterministic"] is True
            assert data["llm_score"] == 91
            assert data["overall_status"] == "shortlisted"
            assert data["current_stage"] == "completed"

        finally:
            app.dependency_overrides.clear()
            # 5. Clean up PostgreSQL test records
            async with AsyncSessionLocal() as db:
                if candidate_profile_id:
                    await db.execute(
                        delete(JobMatch).where(JobMatch.candidate_profile_id == candidate_profile_id)
                    )
                    await db.execute(
                        delete(CandidateProfile).where(CandidateProfile.id == candidate_profile_id)
                    )
                if job_id:
                    await db.execute(delete(JobMatch).where(JobMatch.job_id == job_id))
                    await db.execute(delete(Job).where(Job.id == job_id))
                await db.execute(delete(User).where(User.id == test_user_id))
                await db.commit()
