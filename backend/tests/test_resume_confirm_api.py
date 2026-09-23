import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.database import AsyncSessionLocal, engine
from app.main import app
from app.models import CandidateProfile, Resume, User
from app.schemas.resume import ExperienceItem, ResumeDraft


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def dispose_db_engine():
    yield
    await engine.dispose()


@pytest.mark.anyio
async def test_confirm_resume_draft_updates_profile_and_preserves_existing_data():
    """
    Integration test verifying that POST /api/v1/resumes/{resume_id}/confirm:
    1. Merges confirmed ResumeDraft into CandidateProfile in real PostgreSQL (port 5435).
    2. Preserves existing verified candidate skills, experience, education, and target titles.
    3. Keeps Resume.parsed_json distinct.
    """
    test_user_id = uuid.uuid4()
    test_profile_id = uuid.uuid4()
    test_resume_id = uuid.uuid4()
    test_email = f"confirm_test_{test_user_id.hex[:8]}@example.com"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        try:
            # 1. Setup existing User, CandidateProfile, and Resume in DB
            async with AsyncSessionLocal() as db:
                user = User(id=test_user_id, email=test_email, hashed_password="pw", full_name="User")
                db.add(user)

                profile = CandidateProfile(
                    id=test_profile_id,
                    user_id=test_user_id,
                    headline="Original Headline",
                    summary="Original Summary",
                    skills=["Python", "PyTorch", "LangGraph"],
                    experience=[{"company": "Tech Corp", "title": "ML Engineer", "description": "NLP work"}],
                    education=[{"institution": "MIT", "degree": "B.S.", "field_of_study": "CS"}],
                    target_titles=["AI Engineer"],
                )
                db.add(profile)

                resume = Resume(
                    id=test_resume_id,
                    candidate_profile_id=test_profile_id,
                    file_name="resume.pdf",
                    raw_text="Raw Resume Content",
                    parsed_json={"headline": "Draft Headline", "skills": ["python", "SQL"]},
                )
                db.add(resume)
                await db.commit()

            # 2. Confirmed payload reviewed by user
            confirm_payload = {
                "headline": "Confirmed Senior AI Lead",
                "skills": ["python", "PYTHON", "SQL", "Docker"],
                "experience": [
                    {
                        "company": "Tech Corp",
                        "title": "ML Engineer",
                        "description": "Updated NLP & LLM work",
                        "achievements": ["Reduced latency 40%"],
                    },
                    {
                        "company": "New GenAI Corp",
                        "title": "Staff AI Engineer",
                        "description": "GenAI RAG pipeline",
                    },
                ],
                "education": [
                    {
                        "institution": "Stanford",
                        "degree": "M.S.",
                        "field_of_study": "Artificial Intelligence",
                    }
                ],
                "target_titles": ["ai engineer", "GenAI Architect"],
            }

            response = await async_client.post(
                f"/api/v1/resumes/{test_resume_id}/confirm", json=confirm_payload
            )
            assert response.status_code == 200, f"Confirm failed: {response.text}"
            data = response.json()

            # 3. Verify response merged fields
            assert data["headline"] == "Confirmed Senior AI Lead"
            assert data["summary"] == "Original Summary"  # Preserved since draft summary was null
            assert data["skills"] == ["Python", "PyTorch", "LangGraph", "SQL", "Docker"]  # Case-insensitive deduplication
            assert len(data["experience"]) == 2
            assert data["experience"][0]["company"] == "Tech Corp"
            assert data["experience"][0]["description"] == "Updated NLP & LLM work"
            assert data["experience"][1]["company"] == "New GenAI Corp"
            assert len(data["education"]) == 2
            assert data["education"][0]["institution"] == "MIT"
            assert data["education"][1]["institution"] == "Stanford"
            assert data["target_titles"] == ["AI Engineer", "GenAI Architect"]

            # 4. Verify DB persistence in CandidateProfile and Resume.parsed_json isolation
            async with AsyncSessionLocal() as db:
                db_profile = (
                    await db.execute(select(CandidateProfile).where(CandidateProfile.id == test_profile_id))
                ).scalar_one()
                assert db_profile.skills == ["Python", "PyTorch", "LangGraph", "SQL", "Docker"]

                db_resume = (
                    await db.execute(select(Resume).where(Resume.id == test_resume_id))
                ).scalar_one()
                assert db_resume.parsed_json == {"headline": "Draft Headline", "skills": ["python", "SQL"]}

        finally:
            async with AsyncSessionLocal() as db:
                await db.execute(delete(Resume).where(Resume.id == test_resume_id))
                await db.execute(delete(CandidateProfile).where(CandidateProfile.id == test_profile_id))
                await db.execute(delete(User).where(User.id == test_user_id))
                await db.commit()


@pytest.mark.anyio
async def test_confirm_resume_nonexistent_resume():
    random_id = uuid.uuid4()
    payload = ResumeDraft(headline="Headline").model_dump()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        response = await async_client.post(f"/api/v1/resumes/{random_id}/confirm", json=payload)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_confirm_resume_invalid_payload_returns_422():
    test_user_id = uuid.uuid4()
    test_profile_id = uuid.uuid4()
    test_resume_id = uuid.uuid4()
    test_email = f"invalid_payload_{test_user_id.hex[:8]}@example.com"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        try:
            async with AsyncSessionLocal() as db:
                user = User(id=test_user_id, email=test_email, hashed_password="pw", full_name="User")
                db.add(user)
                profile = CandidateProfile(id=test_profile_id, user_id=test_user_id)
                db.add(profile)
                resume = Resume(
                    id=test_resume_id,
                    candidate_profile_id=test_profile_id,
                    file_name="resume.pdf",
                    raw_text="Sample text",
                )
                db.add(resume)
                await db.commit()

            invalid_payload = {"skills": "Not a list"}  # Malformed type

            response = await async_client.post(
                f"/api/v1/resumes/{test_resume_id}/confirm", json=invalid_payload
            )
            assert response.status_code == 422  # Pydantic validation error

        finally:
            async with AsyncSessionLocal() as db:
                await db.execute(delete(Resume).where(Resume.id == test_resume_id))
                await db.execute(delete(CandidateProfile).where(CandidateProfile.id == test_profile_id))
                await db.execute(delete(User).where(User.id == test_user_id))
                await db.commit()
