"""
Test Suite for Worker Daemon, Scheduled Ingestion, Queue Depths, and Dead-Letter Queue.
Verifies asynchronous queue processing with SKIP LOCKED, retry limits, and status endpoints.
"""
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, delete

from app.database import AsyncSessionLocal, engine
from app.main import app
from app.models import CandidateProfile, Job, JobMatch, User, WorkerHeartbeat
from app.services.job_queue import AsyncJobQueueWorker, PipelineStatus
from app.worker import JobHunterWorkerDaemon


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def dispose_db_engine():
    yield
    await engine.dispose()


@pytest.mark.anyio
async def test_pipeline_status_constants():
    """Verify state machine status constants including DEAD_LETTER."""
    assert PipelineStatus.INGESTED == "ingested"
    assert PipelineStatus.FILTERED == "filtered"
    assert PipelineStatus.SCORED == "scored"
    assert PipelineStatus.TAILORED == "tailored"
    assert PipelineStatus.NOTIFIED == "notified"
    assert PipelineStatus.FAILED == "failed"
    assert PipelineStatus.DEAD_LETTER == "dead_letter"


@pytest.mark.anyio
async def test_get_queue_depths_and_enqueue():
    """Verify queue depths counting and candidate job match enqueueing."""
    async with AsyncSessionLocal() as session:
        # Create a candidate
        test_user = User(
            id=uuid.uuid4(),
            email=f"worker_cand_{uuid.uuid4().hex[:8]}@example.com",
            hashed_password="hash",
            full_name="Worker Candidate",
        )
        session.add(test_user)
        await session.flush()

        candidate = CandidateProfile(
            id=uuid.uuid4(),
            user_id=test_user.id,
            skills=["Python", "FastAPI"],
            experience=[{"years": 3.0}],
        )
        session.add(candidate)

        # Create 2 jobs
        job1 = Job(
            id=uuid.uuid4(),
            source="manual",
            external_id=f"wk_job_{uuid.uuid4().hex[:8]}",
            title="Backend Engineer",
            company="Tech Corp",
            is_remote=True,
            description_raw="We need Python and FastAPI.",
            skills_required=["Python"],
        )
        job2 = Job(
            id=uuid.uuid4(),
            source="manual",
            external_id=f"wk_job_{uuid.uuid4().hex[:8]}",
            title="Senior Architect",
            company="Cloud Inc",
            is_remote=True,
            description_raw="Kubernetes and Go required.",
            skills_required=["Go", "Kubernetes"],
        )
        session.add_all([job1, job2])
        await session.commit()

        # Enqueue matches
        enqueued = await AsyncJobQueueWorker.enqueue_jobs_for_candidates(session, [job1.id, job2.id])
        assert enqueued >= 2

        # Check queue depths
        depths = await AsyncJobQueueWorker.get_queue_depths(session)
        assert depths[PipelineStatus.INGESTED] >= 2

        # Process batch
        worker = AsyncJobQueueWorker(session)
        processed = await worker.process_batch(batch_size=10)
        assert processed >= 2

        # Clean up
        await session.execute(delete(JobMatch).where(JobMatch.job_id.in_([job1.id, job2.id])))
        await session.execute(delete(Job).where(Job.id.in_([job1.id, job2.id])))
        await session.execute(delete(CandidateProfile).where(CandidateProfile.id == candidate.id))
        await session.execute(delete(User).where(User.id == test_user.id))
        await session.commit()


@pytest.mark.anyio
async def test_retry_count_and_dead_letter_queue():
    """Verify that failing jobs increment retry_count and transition to DEAD_LETTER at max retries."""
    async with AsyncSessionLocal() as session:
        # Create a candidate
        test_user = User(
            id=uuid.uuid4(),
            email=f"retry_cand_{uuid.uuid4().hex[:8]}@example.com",
            hashed_password="hash",
            full_name="Retry Candidate",
        )
        session.add(test_user)
        await session.flush()

        candidate = CandidateProfile(
            id=uuid.uuid4(),
            user_id=test_user.id,
            skills=["Python"],
        )
        session.add(candidate)

        job = Job(
            id=uuid.uuid4(),
            source="manual",
            external_id=f"fail_job_{uuid.uuid4().hex[:8]}",
            title="Test Error Job",
            company="Error Corp",
            is_remote=True,
        )
        session.add(job)
        await session.flush()

        # Create a JobMatch with simulated retry count at max_retries - 1
        match = JobMatch(
            id=uuid.uuid4(),
            candidate_profile_id=candidate.id,
            job_id=job.id,
            status=PipelineStatus.INGESTED,
            retry_count=2, # Next failure will push it to 3 (max_retries)
        )
        session.add(match)
        await session.commit()

        # Create a worker that will raise an error during evaluation
        worker = AsyncJobQueueWorker(session)
        # Mock evaluate_job to raise RuntimeError
        original_eval = worker.filter_service.evaluate_job
        worker.filter_service.evaluate_job = lambda c, j: (_ for _ in ()).throw(RuntimeError("Simulated LLM network timeout"))

        try:
            processed = await worker.process_batch(batch_size=1, max_retries=3, match_id=match.id)
            assert processed == 0

            # Reload match from DB
            re_stmt = select(JobMatch).where(JobMatch.id == match.id)
            res = await session.execute(re_stmt)
            updated_match = res.scalar_one()

            # Should be transitioned to DEAD_LETTER
            assert updated_match.status == PipelineStatus.DEAD_LETTER
            assert updated_match.retry_count == 3
            assert "Simulated LLM network timeout" in (updated_match.last_error or "")
        finally:
            worker.filter_service.evaluate_job = original_eval

            # Cleanup
            await session.execute(delete(JobMatch).where(JobMatch.id == match.id))
            await session.execute(delete(Job).where(Job.id == job.id))
            await session.execute(delete(CandidateProfile).where(CandidateProfile.id == candidate.id))
            await session.execute(delete(User).where(User.id == test_user.id))
            await session.commit()


@pytest.mark.anyio
async def test_worker_daemon_single_iteration_and_heartbeat():
    """Verify that JobHunterWorkerDaemon runs cleanly in --once mode and updates heartbeats."""
    test_worker_id = f"test-worker-{uuid.uuid4().hex[:6]}"
    daemon = JobHunterWorkerDaemon(worker_id=test_worker_id)

    # Run single pass
    await daemon.start(run_once=True)
    assert daemon.is_running is False

    # Check heartbeat record in DB
    async with AsyncSessionLocal() as session:
        stmt = select(WorkerHeartbeat).where(WorkerHeartbeat.worker_id == test_worker_id)
        res = await session.execute(stmt)
        hb = res.scalar_one_or_none()

        assert hb is not None
        assert hb.worker_id == test_worker_id
        assert hb.status == "stopped"

        # Cleanup
        await session.execute(delete(WorkerHeartbeat).where(WorkerHeartbeat.worker_id == test_worker_id))
        await session.commit()


@pytest.mark.anyio
async def test_worker_api_endpoints():
    """Verify GET /worker/status and POST /worker/trigger-cycle endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET worker status
        status_res = await client.get("/api/v1/jobs/worker/status")
        assert status_res.status_code == 200
        data = status_res.json()
        assert "queue_depths" in data
        assert "ingested" in data["queue_depths"]
        assert "scored" in data["queue_depths"]
        assert "active_worker_count" in data

        # 2. Trigger on-demand cycle
        trigger_res = await client.post("/api/v1/jobs/worker/trigger-cycle?limit=5&source=manual")
        assert trigger_res.status_code == 200
        trigger_data = trigger_res.json()
        assert "queue_depths" in trigger_data
