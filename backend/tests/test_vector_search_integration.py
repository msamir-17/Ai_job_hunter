import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.database import AsyncSessionLocal, engine
from app.main import app
from app.models import Application, CandidateProfile, Job, JobMatch, User
from app.services.embedding import EmbeddingService
from app.services.vector_search import VectorSearchService
from app.schemas.matching import VectorSearchRequest


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def dispose_db_engine():
    yield
    await engine.dispose()


@pytest.mark.anyio
async def test_vector_similarity_search_real_postgres():
    """
    Integration test verifying pgvector Stage 2 cosine similarity search,
    deterministic stage gating, and FastAPI HTTP endpoint against the real
    Docker PostgreSQL database on port 5435.
    """
    test_user_id = uuid.uuid4()
    test_email = f"vector_test_{test_user_id.hex[:8]}@example.com"

    candidate_profile_id = None
    job_ids = []

    def make_unit_vector(angle_rad: float) -> list[float]:
        import math
        vec = [0.0] * 384
        vec[0] = math.cos(angle_rad)
        vec[1] = math.sin(angle_rad)
        return vec

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        try:
            # 1. Setup User, CandidateProfile, and 3 Jobs in real Postgres (port 5435)
            async with AsyncSessionLocal() as db:
                user = User(
                    id=test_user_id,
                    email=test_email,
                    hashed_password="hashed_test_password",
                    full_name="Vector Search Test Candidate",
                )
                db.add(user)

                cand_vec = make_unit_vector(0.0)  # Reference candidate vector

                candidate = CandidateProfile(
                    user_id=test_user_id,
                    headline="AI & PyTorch Engineer",
                    skills=["Python", "PyTorch", "Transformers", "LLMs", "Vector Search"],
                    target_titles=["AI Engineer", "Machine Learning Engineer"],
                    embedding=cand_vec,
                )
                db.add(candidate)
                await db.commit()
                await db.refresh(candidate)
                candidate_profile_id = candidate.id

                # Job A: Highly relevant AI / NLP role (Passed Stage 1)
                text_a = "Staff AI & LLM Engineer building PyTorch neural search pipelines."
                vec_a = make_unit_vector(0.3)  # cos(0.3) ~= 0.9553 (very high similarity)
                job_a = Job(
                    source="manual",
                    external_id=f"ext_{uuid.uuid4().hex[:8]}",
                    title="Staff AI & LLM Engineer",
                    company="Neural Systems",
                    description_raw=text_a,
                    is_remote=True,
                    skills_required=["Python", "PyTorch", "LLMs"],
                    embedding=vec_a,
                )

                # Job B: Moderately relevant Python Backend role (Passed Stage 1)
                text_b = "Backend Python Developer building REST APIs with PostgreSQL."
                vec_b = make_unit_vector(0.9)  # cos(0.9) ~= 0.6216 (medium similarity)
                job_b = Job(
                    source="manual",
                    external_id=f"ext_{uuid.uuid4().hex[:8]}",
                    title="Backend Python Developer",
                    company="Cloud APIs",
                    description_raw=text_b,
                    is_remote=True,
                    skills_required=["Python", "PostgreSQL"],
                    embedding=vec_b,
                )

                # Job C: Completely unrelated Healthcare role (Disqualified in Stage 1)
                text_c = "Registered Nurse for emergency healthcare and clinical patient care."
                vec_c = make_unit_vector(2.5)  # cos(2.5) ~= -0.8011 (distant similarity)
                job_c = Job(
                    source="manual",
                    external_id=f"ext_{uuid.uuid4().hex[:8]}",
                    title="Emergency Registered Nurse",
                    company="City Hospital",
                    description_raw=text_c,
                    is_remote=False,
                    skills_required=["Patient Care", "BLS"],
                    embedding=vec_c,
                )

                db.add_all([job_a, job_b, job_c])
                await db.commit()
                await db.refresh(job_a)
                await db.refresh(job_b)
                await db.refresh(job_c)
                job_ids = [job_a.id, job_b.id, job_c.id]

                # Create pre-existing JobMatch records to simulate Stage 1 deterministic outcomes
                match_a = JobMatch(
                    candidate_profile_id=candidate.id,
                    job_id=job_a.id,
                    passed_deterministic=True,
                    status="shortlisted",
                    matched_skills=["Python", "PyTorch"],
                )
                match_b = JobMatch(
                    candidate_profile_id=candidate.id,
                    job_id=job_b.id,
                    passed_deterministic=True,
                    status="review",
                    matched_skills=["Python"],
                )
                match_c = JobMatch(
                    candidate_profile_id=candidate.id,
                    job_id=job_c.id,
                    passed_deterministic=False,
                    status="rejected",
                    matched_skills=[],
                )
                db.add_all([match_a, match_b, match_c])
                await db.commit()

            # 2. Test VectorSearchService with only_passed_deterministic=True
            async with AsyncSessionLocal() as db:
                service = VectorSearchService(db=db)
                req = VectorSearchRequest(
                    candidate_profile_id=candidate_profile_id,
                    limit=10,
                    only_passed_deterministic=True,
                )
                results = await service.search_and_persist_matches(req)

                # Job C must be excluded because passed_deterministic is False
                assert len(results) == 2
                res_job_ids = [r.job_id for r in results]
                assert job_ids[0] in res_job_ids
                assert job_ids[1] in res_job_ids
                assert job_ids[2] not in res_job_ids

                # Job A (AI/LLM) must have higher cosine similarity than Job B (General Backend)
                assert results[0].job_id == job_ids[0]
                assert results[0].vector_score > results[1].vector_score
                assert results[0].vector_score > 0.6  # Highly semantically aligned

            # 3. Verify vector_score was persisted in PostgreSQL JobMatch table
            async with AsyncSessionLocal() as db:
                stmt = select(JobMatch).where(
                    JobMatch.candidate_profile_id == candidate_profile_id,
                    JobMatch.job_id == job_ids[0],
                )
                res = await db.execute(stmt)
                persisted_match = res.scalar_one()
                assert persisted_match.vector_score is not None
                assert persisted_match.vector_score > 0.6

            # 4. Test FastAPI HTTP Endpoint POST /api/v1/matching/vector/search
            endpoint_payload = {
                "candidate_profile_id": str(candidate_profile_id),
                "limit": 100,
                "only_passed_deterministic": False,
                "min_similarity_threshold": 0.0,
            }
            resp = await client.post("/api/v1/matching/vector/search", json=endpoint_payload)
            assert resp.status_code == 200
            data = resp.json()

            assert data["candidate_profile_id"] == str(candidate_profile_id)
            assert data["total_matches"] >= 3
            # Filter results to our 3 test jobs
            test_job_str_ids = [str(jid) for jid in job_ids]
            test_results = [r for r in data["results"] if r["job_id"] in test_job_str_ids]
            assert len(test_results) == 3
            # Closest semantic match is Job A, followed by Job B, with Nurse role last
            assert test_results[0]["job_id"] == str(job_ids[0])
            assert test_results[1]["job_id"] == str(job_ids[1])
            assert test_results[2]["job_id"] == str(job_ids[2])
            assert test_results[0]["vector_score"] > test_results[1]["vector_score"] > test_results[2]["vector_score"]

        finally:
            # 5. Cleanup test data from PostgreSQL
            async with AsyncSessionLocal() as db:
                if candidate_profile_id:
                    m_res = await db.execute(
                        select(JobMatch.id).where(JobMatch.candidate_profile_id == candidate_profile_id)
                    )
                    m_ids = list(m_res.scalars().all())
                    if m_ids:
                        await db.execute(delete(Application).where(Application.job_match_id.in_(m_ids)))
                        await db.execute(delete(JobMatch).where(JobMatch.id.in_(m_ids)))
                    await db.execute(
                        delete(CandidateProfile).where(CandidateProfile.id == candidate_profile_id)
                    )
                for jid in job_ids:
                    m_res = await db.execute(select(JobMatch.id).where(JobMatch.job_id == jid))
                    m_ids = list(m_res.scalars().all())
                    if m_ids:
                        await db.execute(delete(Application).where(Application.job_match_id.in_(m_ids)))
                        await db.execute(delete(JobMatch).where(JobMatch.id.in_(m_ids)))
                    await db.execute(delete(Job).where(Job.id == jid))
                await db.execute(delete(User).where(User.id == test_user_id))
                await db.commit()
