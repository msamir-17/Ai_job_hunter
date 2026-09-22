import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.database import AsyncSessionLocal, engine
from app.llm.factory import get_llm_provider
from app.main import app
from app.models import CandidateProfile, Resume, User
from app.schemas.resume import ExperienceItem, ResumeDraft
from tests.test_resume_extractor import DummyMockLLMProvider


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def dispose_db_engine():
    yield
    await engine.dispose()


@pytest.mark.anyio
async def test_extract_resume_endpoint_success_persists_json_and_leaves_profile_untouched():
    """
    Integration test verifying that POST /api/v1/resumes/{resume_id}/extract:
    1. Generates structured draft via LLM provider.
    2. Persists JSON into Resume.parsed_json in real PostgreSQL (port 5435).
    3. Leaves CandidateProfile completely UNCHANGED before and after extraction.
    """
    test_user_id = uuid.uuid4()
    test_profile_id = uuid.uuid4()
    test_resume_id = uuid.uuid4()
    test_email = f"extract_test_{test_user_id.hex[:8]}@example.com"

    mock_draft = ResumeDraft(
        headline="Extracted Data Engineer",
        summary="Extracted summary facts",
        skills=["Python", "SQL", "Spark"],
        experience=[ExperienceItem(company="Data Corp", title="Data Engineer")],
        target_titles=["Senior Data Engineer"],
    )
    mock_provider = DummyMockLLMProvider(return_draft=mock_draft)

    app.dependency_overrides[get_llm_provider] = lambda: mock_provider

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        try:
            # 1. Setup User, CandidateProfile, and Resume with raw_text in real DB
            async with AsyncSessionLocal() as db:
                user = User(id=test_user_id, email=test_email, hashed_password="pw", full_name="User")
                db.add(user)

                profile = CandidateProfile(
                    id=test_profile_id,
                    user_id=test_user_id,
                    headline="Original Unchanged Headline",
                    skills=["Original Skill"],
                )
                db.add(profile)

                resume = Resume(
                    id=test_resume_id,
                    candidate_profile_id=test_profile_id,
                    file_name="resume.pdf",
                    raw_text="Jane Doe\nData Engineer\nSkills: Python, SQL, Spark",
                    parsed_json=None,
                )
                db.add(resume)
                await db.commit()

            # Record CandidateProfile state BEFORE extraction
            async with AsyncSessionLocal() as db:
                p_before = (
                    await db.execute(select(CandidateProfile).where(CandidateProfile.id == test_profile_id))
                ).scalar_one()
                headline_before = p_before.headline
                skills_before = list(p_before.skills)

            # 2. Trigger extraction endpoint
            response = await async_client.post(f"/api/v1/resumes/{test_resume_id}/extract")
            assert response.status_code == 200, f"Extract failed: {response.text}"
            res_data = response.json()
            assert res_data["status"] == "draft_generated"
            assert res_data["draft"]["headline"] == "Extracted Data Engineer"
            assert "Spark" in res_data["draft"]["skills"]

            # 3. Verify DB persistence in Resume.parsed_json
            async with AsyncSessionLocal() as db:
                db_resume = (
                    await db.execute(select(Resume).where(Resume.id == test_resume_id))
                ).scalar_one()
                assert db_resume.parsed_json is not None
                assert db_resume.parsed_json["headline"] == "Extracted Data Engineer"

                # 4. Verify CandidateProfile is 100% UNCHANGED
                p_after = (
                    await db.execute(select(CandidateProfile).where(CandidateProfile.id == test_profile_id))
                ).scalar_one()
                assert p_after.headline == headline_before == "Original Unchanged Headline"
                assert p_after.skills == skills_before == ["Original Skill"]

        finally:
            app.dependency_overrides.clear()
            async with AsyncSessionLocal() as db:
                await db.execute(delete(Resume).where(Resume.id == test_resume_id))
                await db.execute(delete(CandidateProfile).where(CandidateProfile.id == test_profile_id))
                await db.execute(delete(User).where(User.id == test_user_id))
                await db.commit()


@pytest.mark.anyio
async def test_extract_resume_re_extraction_is_idempotent():
    """
    Verify re-running extraction updates existing parsed_json without creating duplicate rows.
    """
    test_user_id = uuid.uuid4()
    test_profile_id = uuid.uuid4()
    test_resume_id = uuid.uuid4()
    test_email = f"idempotent_{test_user_id.hex[:8]}@example.com"

    first_draft = ResumeDraft(headline="First Extraction")
    second_draft = ResumeDraft(headline="Second Re-extraction")

    mock_provider = DummyMockLLMProvider(return_draft=first_draft)
    app.dependency_overrides[get_llm_provider] = lambda: mock_provider

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
                    parsed_json=None,
                )
                db.add(resume)
                await db.commit()

            # First extraction
            res1 = await async_client.post(f"/api/v1/resumes/{test_resume_id}/extract")
            assert res1.status_code == 200
            assert res1.json()["draft"]["headline"] == "First Extraction"

            # Update mock for second extraction
            mock_provider.return_draft = second_draft

            # Re-extraction on same resume ID
            res2 = await async_client.post(f"/api/v1/resumes/{test_resume_id}/extract")
            assert res2.status_code == 200
            assert res2.json()["draft"]["headline"] == "Second Re-extraction"

            # Verify total count of Resume rows remains 1
            async with AsyncSessionLocal() as db:
                resumes_count = len(
                    (
                        await db.execute(
                            select(Resume).where(Resume.candidate_profile_id == test_profile_id)
                        )
                    ).scalars().all()
                )
                assert resumes_count == 1

        finally:
            app.dependency_overrides.clear()
            async with AsyncSessionLocal() as db:
                await db.execute(delete(Resume).where(Resume.id == test_resume_id))
                await db.execute(delete(CandidateProfile).where(CandidateProfile.id == test_profile_id))
                await db.execute(delete(User).where(User.id == test_user_id))
                await db.commit()


@pytest.mark.anyio
async def test_extract_resume_not_found():
    random_id = uuid.uuid4()
    mock_provider = DummyMockLLMProvider()
    app.dependency_overrides[get_llm_provider] = lambda: mock_provider

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        try:
            res = await async_client.post(f"/api/v1/resumes/{random_id}/extract")
            assert res.status_code == 404
            assert "not found" in res.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_extract_resume_empty_raw_text():
    test_user_id = uuid.uuid4()
    test_profile_id = uuid.uuid4()
    test_resume_id = uuid.uuid4()
    test_email = f"empty_raw_{test_user_id.hex[:8]}@example.com"

    mock_provider = DummyMockLLMProvider()
    app.dependency_overrides[get_llm_provider] = lambda: mock_provider

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
                    raw_text="   ",  # empty/whitespace
                    parsed_json=None,
                )
                db.add(resume)
                await db.commit()

            res = await async_client.post(f"/api/v1/resumes/{test_resume_id}/extract")
            assert res.status_code == 400
            assert "no raw text available" in res.json()["detail"].lower()

        finally:
            app.dependency_overrides.clear()
            async with AsyncSessionLocal() as db:
                await db.execute(delete(Resume).where(Resume.id == test_resume_id))
                await db.execute(delete(CandidateProfile).where(CandidateProfile.id == test_profile_id))
                await db.execute(delete(User).where(User.id == test_user_id))
                await db.commit()
