import httpx
import pytest
from sqlalchemy import delete
from app.database import AsyncSessionLocal, engine
from app.llm.base import BaseLLMProvider
from app.models import Job
from app.schemas.job import ExtractedJobData, ManualJobSubmissionRequest
from app.services.manual_job_service import ManualJobService


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def dispose_db_engine():
    yield
    await engine.dispose()


class MockLLMProvider(BaseLLMProvider):
    async def generate_structured(self, system_prompt, user_prompt, response_schema):
        return ExtractedJobData(
            title="Senior Python Architect",
            company="Acme Cloud Corp",
            location="Remote",
            is_remote=True,
            salary_min=140000,
            salary_max=180000,
            skills_required=["Python", "FastAPI", "PostgreSQL"],
            summary="Lead core backend distributed services.",
        )


@pytest.mark.anyio
async def test_manual_job_with_raw_text():
    llm = MockLLMProvider()

    async with AsyncSessionLocal() as db:
        service = ManualJobService(db, llm)
        req = ManualJobSubmissionRequest(raw_text="We are hiring a Senior Python Architect at Acme Cloud Corp.")
        job = await service.ingest_manual_job(req)

        try:
            assert job.source == "manual-paste"
            assert job.title == "Senior Python Architect"
            assert job.company == "Acme Cloud Corp"
            assert job.is_remote is True
            assert job.salary_min == 140000
            assert job.dedup_key is not None
            assert "Python" in job.skills_required
        finally:
            await db.execute(delete(Job).where(Job.id == job.id))
            await db.commit()


@pytest.mark.anyio
async def test_manual_job_with_greenhouse_url(monkeypatch):
    class MockResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {
                "id": 555123,
                "title": "Principal Infrastructure Engineer",
                "location": {"name": "Remote, US"},
                "absolute_url": "https://boards.greenhouse.io/stripe/jobs/555123",
                "first_published": "2026-10-21T09:00:00Z",
                "content": "<p>Own planetary financial rails.</p>",
            }

    async def mock_get(self, url, *args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    llm = MockLLMProvider()

    async with AsyncSessionLocal() as db:
        service = ManualJobService(db, llm)
        req = ManualJobSubmissionRequest(url="https://boards.greenhouse.io/stripe/jobs/555123")
        job = await service.ingest_manual_job(req)

        try:
            assert job.source == "greenhouse"
            assert job.external_id == "555123"
            assert job.title == "Principal Infrastructure Engineer"
            assert job.company == "Stripe"
            assert job.is_remote is True
            assert job.apply_url == "https://boards.greenhouse.io/stripe/jobs/555123"
        finally:
            await db.execute(delete(Job).where(Job.id == job.id))
            await db.commit()
