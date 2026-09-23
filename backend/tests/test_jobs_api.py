import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from app.database import AsyncSessionLocal, engine
from app.main import app
from app.models import Job


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def dispose_db_engine():
    yield
    await engine.dispose()


@pytest.mark.anyio
async def test_jobs_api_ingest_manual_and_list_real_db():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        try:
            # 1. Trigger Manual Ingestion
            ingest_res = await async_client.post(
                "/api/v1/jobs/ingest",
                json={"source": "manual", "limit": 3, "use_cache": False},
            )
            assert ingest_res.status_code == 200
            data = ingest_res.json()
            assert data["source"] == "manual"
            assert data["fetched"] == 3
            assert data["normalized"] == 3
            assert data["inserted"] == 3
            assert data["skipped_duplicates"] == 0
            assert data["failed"] == 0

            # 2. Trigger Second Ingestion (Idempotent: Should skip duplicates)
            ingest_res_2 = await async_client.post(
                "/api/v1/jobs/ingest",
                json={"source": "manual", "limit": 3, "use_cache": False},
            )
            assert ingest_res_2.status_code == 200
            data_2 = ingest_res_2.json()
            assert data_2["inserted"] == 0
            assert data_2["skipped_duplicates"] == 3

            # 3. List Jobs via GET /api/v1/jobs
            list_res = await async_client.get("/api/v1/jobs?source=manual&limit=10")
            assert list_res.status_code == 200
            jobs = list_res.json()
            assert len(jobs) == 3
            first_job_id = jobs[0]["id"]
            assert jobs[0]["source"] == "manual"
            assert jobs[0]["raw_description"] is not None

            # 4. Fetch Single Job via GET /api/v1/jobs/{id}
            detail_res = await async_client.get(f"/api/v1/jobs/{first_job_id}")
            assert detail_res.status_code == 200
            detail = detail_res.json()
            assert detail["id"] == first_job_id
            assert detail["title"] == jobs[0]["title"]

        finally:
            # Clean up test jobs
            async with AsyncSessionLocal() as db:
                await db.execute(delete(Job).where(Job.source == "manual"))
                await db.commit()


@pytest.mark.anyio
async def test_jobs_api_ingest_remotive_cache_real_db():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        try:
            # Trigger Remotive Ingestion using local dev cache
            ingest_res = await async_client.post(
                "/api/v1/jobs/ingest",
                json={"source": "remotive", "limit": 2, "use_cache": True},
            )
            assert ingest_res.status_code == 200
            data = ingest_res.json()
            assert data["source"] == "remotive"
            assert data["fetched"] == 2
            assert data["normalized"] == 2
            assert data["inserted"] == 2

        finally:
            async with AsyncSessionLocal() as db:
                await db.execute(delete(Job).where(Job.source == "remotive"))
                await db.commit()


@pytest.mark.anyio
async def test_jobs_api_get_nonexistent_job_returns_404():
    random_id = uuid.uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        res = await async_client.get(f"/api/v1/jobs/{random_id}")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()
