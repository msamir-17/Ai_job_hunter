import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.database import AsyncSessionLocal, engine
from app.main import app
from app.models import CandidateProfile, Resume, User
from tests.test_resume_parser import create_sample_docx_bytes, create_sample_pdf_bytes


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def dispose_db_engine():
    yield
    await engine.dispose()


@pytest.mark.anyio
async def test_resume_upload_docx_real_db():
    """
    Integration test verifying DOCX upload, text extraction, and Resume entity creation
    against the real Docker PostgreSQL database on port 5435.
    """
    test_user_id = uuid.uuid4()
    test_profile_id = uuid.uuid4()
    test_email = f"resume_test_{test_user_id.hex[:8]}@example.com"
    created_resume_id = None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        try:
            # 1. Create a test User and CandidateProfile directly in real PostgreSQL
            async with AsyncSessionLocal() as db:
                user = User(
                    id=test_user_id,
                    email=test_email,
                    hashed_password="hashed_test_password",
                    full_name="Resume Test User",
                )
                db.add(user)

                profile = CandidateProfile(
                    id=test_profile_id,
                    user_id=test_user_id,
                    headline="Software Engineer",
                )
                db.add(profile)
                await db.commit()

            # 2. Upload valid DOCX file
            docx_bytes = create_sample_docx_bytes(["Alex Smith", "Full Stack Developer", "Skills: Python, FastAPI"])
            files = {
                "file": ("sample_resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            }
            data = {"candidate_profile_id": str(test_profile_id)}

            response = await async_client.post("/api/v1/resumes/upload", data=data, files=files)
            assert response.status_code == 201, f"Upload failed: {response.text}"
            res_json = response.json()
            assert res_json["candidate_profile_id"] == str(test_profile_id)
            assert res_json["file_name"] == "sample_resume.docx"
            assert res_json["status"] == "extracted"
            assert res_json["raw_text_length"] > 0
            created_resume_id = uuid.UUID(res_json["id"])

            # 3. Direct DB verification: confirm raw_text is stored and parsed_json is NULL
            async with AsyncSessionLocal() as db:
                db_stmt = select(Resume).where(Resume.id == created_resume_id)
                db_res = await db.execute(db_stmt)
                db_resume = db_res.scalar_one_or_none()
                assert db_resume is not None
                assert "Alex Smith" in db_resume.raw_text
                assert "Full Stack Developer" in db_resume.raw_text
                assert db_resume.parsed_json is None

        finally:
            # 4. Clean up test records
            async with AsyncSessionLocal() as db:
                if created_resume_id:
                    await db.execute(delete(Resume).where(Resume.id == created_resume_id))
                await db.execute(delete(CandidateProfile).where(CandidateProfile.id == test_profile_id))
                await db.execute(delete(User).where(User.id == test_user_id))
                await db.commit()


@pytest.mark.anyio
async def test_resume_upload_pdf_real_db():
    """
    Integration test verifying PDF upload and text extraction against real Docker PostgreSQL DB.
    """
    test_user_id = uuid.uuid4()
    test_profile_id = uuid.uuid4()
    test_email = f"pdf_test_{test_user_id.hex[:8]}@example.com"
    created_resume_id = None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        try:
            async with AsyncSessionLocal() as db:
                user = User(id=test_user_id, email=test_email, hashed_password="pw", full_name="PDF User")
                db.add(user)
                profile = CandidateProfile(id=test_profile_id, user_id=test_user_id)
                db.add(profile)
                await db.commit()

            pdf_bytes = create_sample_pdf_bytes("PDF Resume Content")
            files = {"file": ("resume.pdf", pdf_bytes, "application/pdf")}
            data = {"candidate_profile_id": str(test_profile_id)}

            response = await async_client.post("/api/v1/resumes/upload", data=data, files=files)
            assert response.status_code == 201
            res_json = response.json()
            assert res_json["file_name"] == "resume.pdf"
            assert res_json["status"] == "extracted"
            created_resume_id = uuid.UUID(res_json["id"])

        finally:
            async with AsyncSessionLocal() as db:
                if created_resume_id:
                    await db.execute(delete(Resume).where(Resume.id == created_resume_id))
                await db.execute(delete(CandidateProfile).where(CandidateProfile.id == test_profile_id))
                await db.execute(delete(User).where(User.id == test_user_id))
                await db.commit()


@pytest.mark.anyio
async def test_resume_upload_nonexistent_candidate_profile():
    random_profile_id = uuid.uuid4()
    docx_bytes = create_sample_docx_bytes(["Test Content"])
    files = {"file": ("resume.docx", docx_bytes, "application/octet-stream")}
    data = {"candidate_profile_id": str(random_profile_id)}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        response = await async_client.post("/api/v1/resumes/upload", data=data, files=files)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_resume_upload_unsupported_file_type():
    test_user_id = uuid.uuid4()
    test_profile_id = uuid.uuid4()
    test_email = f"resume_test_{test_user_id.hex[:8]}@example.com"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        try:
            async with AsyncSessionLocal() as db:
                user = User(id=test_user_id, email=test_email, hashed_password="pw", full_name="User")
                db.add(user)
                profile = CandidateProfile(id=test_profile_id, user_id=test_user_id)
                db.add(profile)
                await db.commit()

            files = {"file": ("script.sh", b"#!/bin/bash\necho hello", "text/x-shellscript")}
            data = {"candidate_profile_id": str(test_profile_id)}

            response = await async_client.post("/api/v1/resumes/upload", data=data, files=files)
            assert response.status_code == 400
            assert "unsupported file format" in response.json()["detail"].lower()

        finally:
            async with AsyncSessionLocal() as db:
                await db.execute(delete(CandidateProfile).where(CandidateProfile.id == test_profile_id))
                await db.execute(delete(User).where(User.id == test_user_id))
                await db.commit()


@pytest.mark.anyio
async def test_resume_upload_exceeds_size_limit():
    test_user_id = uuid.uuid4()
    test_profile_id = uuid.uuid4()
    test_email = f"resume_test_{test_user_id.hex[:8]}@example.com"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        try:
            async with AsyncSessionLocal() as db:
                user = User(id=test_user_id, email=test_email, hashed_password="pw", full_name="User")
                db.add(user)
                profile = CandidateProfile(id=test_profile_id, user_id=test_user_id)
                db.add(profile)
                await db.commit()

            large_bytes = b"a" * (5 * 1024 * 1024 + 1)
            files = {"file": ("large_resume.pdf", large_bytes, "application/pdf")}
            data = {"candidate_profile_id": str(test_profile_id)}

            response = await async_client.post("/api/v1/resumes/upload", data=data, files=files)
            assert response.status_code == 400
            assert "exceeds maximum allowed limit" in response.json()["detail"].lower()

        finally:
            async with AsyncSessionLocal() as db:
                await db.execute(delete(CandidateProfile).where(CandidateProfile.id == test_profile_id))
                await db.execute(delete(User).where(User.id == test_user_id))
                await db.commit()
