"""
Test Suite for Candidate Discard Feedback Loop & Rocchio Vector Learning.
Verifies feedback event persistence, Rocchio vector adaptation,
tenant isolation, and discard undo functionality against real PostgreSQL (port 5435).
"""
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, delete

from app.database import AsyncSessionLocal, engine
from app.main import app
from app.models import CandidateProfile, FeedbackEvent, Job, User


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def dispose_db_engine():
    yield
    await engine.dispose()


@pytest.mark.anyio
async def test_feedback_discard_and_rocchio_adaptation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register candidate Alice
        alice_email = f"alice_feed_{uuid.uuid4().hex[:8]}@example.com"
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": alice_email,
                "password": "Password123!",
                "full_name": "Alice Feedback",
            },
        )
        assert reg_res.status_code == 201
        alice_token = reg_res.json()["access_token"]
        alice_headers = {"Authorization": f"Bearer {alice_token}"}
        alice_user_id = uuid.UUID(reg_res.json()["user"]["id"])

        # 2. Seed a test job and CandidateProfile with dummy 384-dim vectors
        job_id = uuid.uuid4()
        profile_id = uuid.uuid4()
        dummy_job_vector = [0.1] * 384
        dummy_profile_vector = [0.2] * 384

        async with AsyncSessionLocal() as db:
            test_job = Job(
                id=job_id,
                source="test",
                title="Legacy PHP Developer",
                company="OldTech Corp",
                location="Remote",
                is_remote=True,
                description_raw="Maintaining monolithic legacy codebase in PHP 5.6",
                skills_required=["PHP", "MySQL"],
                embedding=dummy_job_vector,
            )
            db.add(test_job)

            test_profile = CandidateProfile(
                id=profile_id,
                user_id=alice_user_id,
                headline="Python Engineer",
                summary="Modern backend developer with Python and FastAPI",
                skills=["Python", "FastAPI"],
                embedding=dummy_profile_vector,
            )
            db.add(test_profile)
            await db.commit()

        try:
            # 3. Alice discards the PHP job with reason 'tech_stack_mismatch'
            discard_res = await client.post(
                "/api/v1/feedback/discard",
                headers=alice_headers,
                json={
                    "job_id": str(job_id),
                    "reason_code": "tech_stack_mismatch",
                    "notes": "I do not work with legacy PHP stack",
                    "disliked_skill": "PHP",
                },
            )
            assert discard_res.status_code == 201, discard_res.text
            feedback_data = discard_res.json()
            assert feedback_data["action"] == "discard"
            assert feedback_data["reason_code"] == "tech_stack_mismatch"
            assert feedback_data["disliked_skill"] == "PHP"
            assert feedback_data["vector_updated"] is True
            feedback_id = feedback_data["id"]

            # 4. Verify candidate profile vector was adjusted in PostgreSQL database
            async with AsyncSessionLocal() as db:
                res_p = await db.execute(select(CandidateProfile).where(CandidateProfile.id == profile_id))
                updated_profile = res_p.scalar_one()
                assert updated_profile.embedding is not None
                # Rocchio pushed vector away from discarded vector:
                # profile_vector had 0.2, job_vector had 0.1 -> adjusted elements should differ
                assert list(updated_profile.embedding) != dummy_profile_vector

            # 5. List feedback history
            list_res = await client.get("/api/v1/feedback", headers=alice_headers)
            assert list_res.status_code == 200
            events = list_res.json()
            assert len(events) >= 1
            assert events[0]["job_id"] == str(job_id)

            # 6. Cross-tenant check: Register Bob and ensure Bob cannot delete Alice's feedback
            bob_email = f"bob_feed_{uuid.uuid4().hex[:8]}@example.com"
            bob_reg = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": bob_email,
                    "password": "Password123!",
                    "full_name": "Bob Observer",
                },
            )
            assert bob_reg.status_code == 201
            bob_token = bob_reg.json()["access_token"]
            bob_headers = {"Authorization": f"Bearer {bob_token}"}

            bob_delete = await client.delete(f"/api/v1/feedback/{feedback_id}", headers=bob_headers)
            assert bob_delete.status_code == 403
            assert "forbidden" in bob_delete.json()["detail"].lower()

            # 7. Alice can undo/delete her own discard feedback
            alice_delete = await client.delete(f"/api/v1/feedback/{feedback_id}", headers=alice_headers)
            assert alice_delete.status_code == 204

        finally:
            # Teardown test entities
            async with AsyncSessionLocal() as db:
                await db.execute(delete(FeedbackEvent).where(FeedbackEvent.job_id == job_id))
                await db.execute(delete(CandidateProfile).where(CandidateProfile.id == profile_id))
                await db.execute(delete(Job).where(Job.id == job_id))
                await db.execute(delete(User).where(User.id == alice_user_id))
                await db.commit()
