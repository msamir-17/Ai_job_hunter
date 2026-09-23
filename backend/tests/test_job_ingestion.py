from typing import Any
import pytest
from sqlalchemy import delete, select
from app.adapters.base import BaseJobSourceAdapter
from app.adapters.manual import ManualJobSourceAdapter
from app.database import AsyncSessionLocal, engine
from app.models import Job
from app.services.job_ingestion import JobIngestionService


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def dispose_db_engine():
    yield
    await engine.dispose()


class CustomMockAdapter(BaseJobSourceAdapter):
    """Custom mock adapter for testing specific edge cases."""

    def __init__(self, source: str, raw_jobs: list[dict[str, Any]]):
        self._source = source
        self._raw_jobs = raw_jobs

    @property
    def source_name(self) -> str:
        return self._source

    async def fetch_jobs(self, limit: int | None = None, **kwargs: Any) -> list[dict[str, Any]]:
        jobs = list(self._raw_jobs)
        if limit is not None and limit > 0:
            jobs = jobs[:limit]
        return jobs


@pytest.mark.anyio
async def test_job_ingestion_manual_adapter_idempotency_real_db():
    """
    Verifies that running ingestion twice with the same source + external_id
    is 100% idempotent and skips duplicate database records.
    """
    test_source = "test_manual_idempotency"
    mock_data = [
        {
            "external_id": "test-idemp-001",
            "title": "Backend AI Developer",
            "company": "Test Company A",
            "location": "Remote",
            "is_remote": True,
            "raw_description": "Building LLM pipelines",
            "skills_required": ["Python", "PostgreSQL"],
            "url": "https://example.com/job/001",
        },
        {
            "external_id": "test-idemp-002",
            "title": "Frontend Engineer",
            "company": "Test Company B",
            "location": "New York, NY",
            "is_remote": False,
            "raw_description": "React and Tailwind app development",
            "skills_required": ["React", "TypeScript"],
            "url": "https://example.com/job/002",
        },
    ]

    adapter = CustomMockAdapter(test_source, mock_data)

    try:
        # First Run: Should insert both jobs cleanly
        async with AsyncSessionLocal() as db:
            service = JobIngestionService(db)
            res_1 = await service.ingest_jobs(adapter)
            assert res_1.fetched == 2
            assert res_1.normalized == 2
            assert res_1.inserted == 2
            assert res_1.skipped_duplicates == 0
            assert res_1.failed == 0

        # Verify DB records were stored with embedding=None
        async with AsyncSessionLocal() as db:
            stmt = select(Job).where(Job.source == test_source)
            db_res = await db.execute(stmt)
            jobs = db_res.scalars().all()
            assert len(jobs) == 2
            for j in jobs:
                assert j.embedding is None

        # Second Run: Idempotent execution - should skip both duplicates
        async with AsyncSessionLocal() as db:
            service = JobIngestionService(db)
            res_2 = await service.ingest_jobs(adapter)
            assert res_2.fetched == 2
            assert res_2.normalized == 2
            assert res_2.inserted == 0
            assert res_2.skipped_duplicates == 2
            assert res_2.failed == 0

    finally:
        # Clean up database records
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Job).where(Job.source == test_source))
            await db.commit()


@pytest.mark.anyio
async def test_job_ingestion_different_sources_same_external_id_allowed_real_db():
    """
    Verifies that (source_A, ext_1) and (source_B, ext_1) are both allowed
    by PostgreSQL unique constraint.
    """
    ext_id = "common-external-id"
    raw_job = {
        "external_id": ext_id,
        "title": "Data Engineer",
        "company": "Cross Source Inc",
        "url": "https://example.com/job/common",
    }

    adapter_a = CustomMockAdapter("source_alpha", [raw_job])
    adapter_b = CustomMockAdapter("source_beta", [raw_job])

    try:
        async with AsyncSessionLocal() as db:
            service = JobIngestionService(db)
            res_a = await service.ingest_jobs(adapter_a)
            assert res_a.inserted == 1

        async with AsyncSessionLocal() as db:
            service = JobIngestionService(db)
            res_b = await service.ingest_jobs(adapter_b)
            assert res_b.inserted == 1

        # Confirm both exist in DB
        async with AsyncSessionLocal() as db:
            stmt = select(Job).where(Job.external_id == ext_id)
            jobs = (await db.execute(stmt)).scalars().all()
            assert len(jobs) == 2
            sources_found = {j.source for j in jobs}
            assert sources_found == {"source_alpha", "source_beta"}

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Job).where(Job.external_id == ext_id))
            await db.commit()


@pytest.mark.anyio
async def test_job_ingestion_partial_batch_failure_resilience_real_db():
    """
    Verifies that a batch containing 1 malformed job and 2 valid jobs
    successfully inserts the 2 valid jobs while recording 1 failure.
    """
    test_source = "test_partial_failure"
    mock_data = [
        {
            "external_id": "valid-001",
            "title": "Valid Engineer 1",
            "company": "Valid Corp",
            "url": "https://example.com/job/valid-1",
        },
        {
            # Malformed job: contradictory salary bounds salary_min > salary_max
            "external_id": "malformed-002",
            "title": "Malformed Engineer",
            "company": "Bad Salary Inc",
            "salary_min": 200000,
            "salary_max": 100000,
        },
        {
            "external_id": "valid-003",
            "title": "Valid Engineer 2",
            "company": "Valid Corp",
            "url": "https://example.com/job/valid-2",
        },
    ]

    adapter = CustomMockAdapter(test_source, mock_data)

    try:
        async with AsyncSessionLocal() as db:
            service = JobIngestionService(db)
            res = await service.ingest_jobs(adapter)

            assert res.fetched == 3
            assert res.normalized == 2
            assert res.inserted == 2
            assert res.failed == 1
            assert len(res.errors) == 1
            assert "cannot exceed salary_max" in res.errors[0]

        # Verify DB only contains the 2 valid jobs
        async with AsyncSessionLocal() as db:
            stmt = select(Job).where(Job.source == test_source)
            jobs = (await db.execute(stmt)).scalars().all()
            assert len(jobs) == 2
            ext_ids = {j.external_id for j in jobs}
            assert ext_ids == {"valid-001", "valid-003"}

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Job).where(Job.source == test_source))
            await db.commit()
