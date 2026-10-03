import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.database import AsyncSessionLocal, engine
from app.main import app
from app.models import Application, CandidateProfile, GeneratedDocument, Job, JobMatch, User


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def dispose_db_engine():
    yield
    await engine.dispose()


@pytest.mark.anyio
async def test_applications_lifecycle_real_postgres():
    """
    Integration test verifying Application tracking CRUD, document attachment,
    approval toggle, and cascade deletion against real Docker PostgreSQL (port 5435).
    """
    test_user_id = uuid.uuid4()
    test_email = f"app_test_{test_user_id.hex[:8]}@example.com"

    candidate_profile_id = None
    job_id = None
    job_match_id = None
    application_id = None

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        try:
            # 1. Setup User, CandidateProfile, Job, and JobMatch in real Postgres
            async with AsyncSessionLocal() as db:
                user = User(
                    id=test_user_id,
                    email=test_email,
                    hashed_password="hashed_password",
                    full_name="App Tracker Candidate",
                )
                db.add(user)

                candidate = CandidateProfile(
                    user_id=test_user_id,
                    headline="AI Engineer",
                    skills=["Python", "PyTorch"],
                )
                db.add(candidate)
                await db.commit()
                await db.refresh(candidate)
                candidate_profile_id = candidate.id

                job = Job(
                    source="manual",
                    external_id=f"ext_{uuid.uuid4().hex[:8]}",
                    title="Senior AI Engineer",
                    company="Neural Search Labs",
                    description_raw="Building neural search with PyTorch.",
                    is_remote=True,
                    url="https://neuralsearch.ai/careers/ai-eng",
                )
                db.add(job)
                await db.commit()
                await db.refresh(job)
                job_id = job.id

                match = JobMatch(
                    candidate_profile_id=candidate.id,
                    job_id=job.id,
                    passed_deterministic=True,
                    vector_score=0.92,
                    llm_score=89,
                    status="shortlisted",
                )
                db.add(match)
                await db.commit()
                await db.refresh(match)
                job_match_id = match.id

            # 2. Test POST /api/v1/applications (Create application with status 'saved')
            app_create_payload = {
                "user_id": str(test_user_id),
                "job_match_id": str(job_match_id),
                "status": "saved",
                "notes": "Target company for Q4 applications.",
            }
            create_resp = await client.post("/api/v1/applications", json=app_create_payload)
            assert create_resp.status_code == 201
            app_data = create_resp.json()

            assert app_data["status"] == "saved"
            assert app_data["job_title"] == "Senior AI Engineer"
            assert app_data["job_company"] == "Neural Search Labs"
            assert app_data["job_url"] == "https://neuralsearch.ai/careers/ai-eng"
            application_id = uuid.UUID(app_data["id"])

            # 3. Test GET /api/v1/applications?status=saved (List for Kanban column)
            list_resp = await client.get("/api/v1/applications?status=saved")
            assert list_resp.status_code == 200
            list_data = list_resp.json()
            assert any(item["id"] == str(application_id) for item in list_data)

            # 4. Test POST /api/v1/applications/{id}/documents (Attach tailored resume bullets)
            doc_create_payload = {
                "doc_type": "tailored_resume_bullets",
                "content": "Engineered PyTorch neural models processing 1M tokens/sec.",
                "is_approved_by_user": False,
            }
            doc_resp = await client.post(
                f"/api/v1/applications/{application_id}/documents",
                json=doc_create_payload,
            )
            assert doc_resp.status_code == 201
            doc_data = doc_resp.json()
            assert doc_data["doc_type"] == "tailored_resume_bullets"
            assert doc_data["is_approved_by_user"] is False
            document_id = doc_data["id"]

            # 5. Test PATCH /api/v1/applications/{id}/documents/{doc_id} (Candidate approval toggle)
            doc_patch_payload = {
                "is_approved_by_user": True,
            }
            patch_doc_resp = await client.patch(
                f"/api/v1/applications/{application_id}/documents/{document_id}",
                json=doc_patch_payload,
            )
            assert patch_doc_resp.status_code == 200
            updated_doc = patch_doc_resp.json()
            assert updated_doc["is_approved_by_user"] is True

            # 6. Test PATCH /api/v1/applications/{id} (Move status to 'applied', auto-stamps applied_at)
            app_patch_payload = {
                "status": "applied",
                "notes": "Submitted application manually on external careers site.",
            }
            patch_app_resp = await client.patch(
                f"/api/v1/applications/{application_id}",
                json=app_patch_payload,
            )
            assert patch_app_resp.status_code == 200
            updated_app = patch_app_resp.json()
            assert updated_app["status"] == "applied"
            assert updated_app["applied_at"] is not None  # Auto-stamped timestamp
            assert len(updated_app["documents"]) == 1
            assert updated_app["documents"][0]["is_approved_by_user"] is True

            # 7. Test DELETE /api/v1/applications/{id} (Cascade delete)
            del_resp = await client.delete(f"/api/v1/applications/{application_id}")
            assert del_resp.status_code == 204

            # Verify application and attached document are deleted in PostgreSQL
            async with AsyncSessionLocal() as db:
                check_app = (await db.execute(
                    select(Application).where(Application.id == application_id)
                )).scalar_one_or_none()
                assert check_app is None

                check_doc = (await db.execute(
                    select(GeneratedDocument).where(GeneratedDocument.application_id == application_id)
                )).scalar_one_or_none()
                assert check_doc is None

        finally:
            # 8. Cleanup remaining entities
            async with AsyncSessionLocal() as db:
                if application_id:
                    await db.execute(delete(Application).where(Application.id == application_id))
                if job_match_id:
                    await db.execute(delete(JobMatch).where(JobMatch.id == job_match_id))
                if candidate_profile_id:
                    await db.execute(
                        delete(CandidateProfile).where(CandidateProfile.id == candidate_profile_id)
                    )
                if job_id:
                    await db.execute(delete(Job).where(Job.id == job_id))
                await db.execute(delete(User).where(User.id == test_user_id))
                await db.commit()
