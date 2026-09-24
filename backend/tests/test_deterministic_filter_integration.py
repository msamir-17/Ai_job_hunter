import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.database import AsyncSessionLocal, engine
from app.main import app
from app.models import CandidateProfile, Job, JobMatch, User


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def dispose_db_engine():
    yield
    await engine.dispose()


@pytest.mark.anyio
async def test_deterministic_filtering_real_postgres():
    """
    Integration test verifying deterministic filtering service & FastAPI endpoints
    against the real Docker PostgreSQL database on port 5435.
    """
    test_user_id = uuid.uuid4()
    test_email = f"filter_test_{test_user_id.hex[:8]}@example.com"

    candidate_profile_id = None
    job_ids = []

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        try:
            # 1. Setup User & CandidateProfile in real Postgres (port 5435)
            async with AsyncSessionLocal() as db:
                user = User(
                    id=test_user_id,
                    email=test_email,
                    hashed_password="hashed_test_password",
                    full_name="Filter Integration Candidate",
                )
                db.add(user)

                candidate = CandidateProfile(
                    user_id=test_user_id,
                    headline="Fresher AI Engineer",
                    skills=["Python", "FastAPI", "PyTorch"],
                    experience=[
                        {
                            "company": "Tech Corp",
                            "title": "AI Intern",
                            "start_date": "2023-01-01",
                            "end_date": "2024-01-01",  # 1 year verified experience
                        }
                    ],
                    target_titles=["AI Engineer", "Machine Learning Engineer"],
                )
                db.add(candidate)
                await db.commit()
                await db.refresh(candidate)
                candidate_profile_id = candidate.id

                # 2. Insert Job postings in real Postgres
                j1 = Job(
                    source="manual",
                    external_id=f"ext_{uuid.uuid4().hex[:8]}",
                    title="AI Engineer (1 yr exp required)",
                    company="Company Shortlist",
                    description_raw="Requires 1 year experience with Python.",
                    is_remote=True,
                    skills_required=["Python", "FastAPI"],
                )
                j2 = Job(
                    source="manual",
                    external_id=f"ext_{uuid.uuid4().hex[:8]}",
                    title="Machine Learning Engineer (3 yrs exp)",
                    company="Company Review",
                    description_raw="Requires 3 years of experience in ML.",
                    is_remote=True,
                    skills_required=["Python", "PyTorch", "Kubernetes"],
                )
                j3 = Job(
                    source="manual",
                    external_id=f"ext_{uuid.uuid4().hex[:8]}",
                    title="Senior AI Engineer",
                    company="Company Reject",
                    description_raw="Requires 6 years of experience.",
                    is_remote=True,
                    skills_required=["Python", "PyTorch"],
                )

                db.add_all([j1, j2, j3])
                await db.commit()
                await db.refresh(j1)
                await db.refresh(j2)
                await db.refresh(j3)
                job_ids = [j1.id, j2.id, j3.id]

            # 3. Call POST /api/v1/matching/deterministic/filter
            payload = {
                "candidate_profile_id": str(candidate_profile_id),
                "limit": 100,
                "config": {
                    "max_allowed_experience_gap": 2.0,
                },
            }

            filter_resp = await async_client.post("/api/v1/matching/deterministic/filter", json=payload)
            assert filter_resp.status_code == 200, f"Filter failed: {filter_resp.text}"
            res_data = filter_resp.json()

            assert res_data["candidate_profile_id"] == str(candidate_profile_id)
            assert res_data["total_evaluated"] >= 3

            # Verify individual job results in batch output
            job_results = {r["job_id"]: r for r in res_data["results"]}

            j1_res = job_results[str(j1.id)]
            assert j1_res["overall_status"] == "shortlisted"
            assert j1_res["passed_deterministic"] is True
            assert "Python" in j1_res["matched_skills"]

            j2_res = job_results[str(j2.id)]
            assert j2_res["overall_status"] == "review"
            assert j2_res["passed_deterministic"] is True  # REVIEW is True
            assert "Kubernetes" in j2_res["missing_skills"]

            j3_res = job_results[str(j3.id)]
            assert j3_res["overall_status"] == "rejected"
            assert j3_res["passed_deterministic"] is False  # REJECTED is False

            # 4. Call GET /api/v1/matching/candidate/{candidate_profile_id}/matches
            get_matches_resp = await async_client.get(
                f"/api/v1/matching/candidate/{candidate_profile_id}/matches"
            )
            assert get_matches_resp.status_code == 200
            matches_data = get_matches_resp.json()
            assert len(matches_data) >= 3

            # Query with status filter = "shortlisted"
            get_shortlisted_resp = await async_client.get(
                f"/api/v1/matching/candidate/{candidate_profile_id}/matches?status=shortlisted"
            )
            assert get_shortlisted_resp.status_code == 200
            shortlisted_data = get_shortlisted_resp.json()
            assert any(m["job_id"] == str(j1.id) for m in shortlisted_data)
            assert all(m["status"] == "shortlisted" for m in shortlisted_data)

            # 5. Test idempotency: re-running filter updates existing JobMatch records without duplicate errors
            rerun_resp = await async_client.post("/api/v1/matching/deterministic/filter", json=payload)
            assert rerun_resp.status_code == 200

        finally:
            # Clean up test database records from real PostgreSQL
            async with AsyncSessionLocal() as db:
                if candidate_profile_id:
                    await db.execute(delete(JobMatch).where(JobMatch.candidate_profile_id == candidate_profile_id))
                    await db.execute(delete(CandidateProfile).where(CandidateProfile.id == candidate_profile_id))
                for jid in job_ids:
                    await db.execute(delete(Job).where(Job.id == jid))
                await db.execute(delete(User).where(User.id == test_user_id))
                await db.commit()
