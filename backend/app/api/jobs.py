from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters import (
    AdzunaJobSourceAdapter,
    GreenhouseJobSourceAdapter,
    JobSpyJobSourceAdapter,
    LeverJobSourceAdapter,
    ManualJobSourceAdapter,
    RemotiveJobSourceAdapter,
)
from app.database import get_db
from app.llm import BaseLLMProvider, get_llm_provider
from app.models import Job, WorkerHeartbeat
from app.schemas.job import (
    IngestionRequest,
    IngestionResult,
    JobResponse,
    ManualJobSubmissionRequest,
    WorkerHeartbeatResponse,
    WorkerStatusResponse,
)
from app.services.job_ingestion import JobIngestionService
from app.services.job_queue import AsyncJobQueueWorker
from app.services.manual_job_service import ManualJobService

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


@router.post(
    "/ingest",
    response_model=IngestionResult,
    status_code=status.HTTP_200_OK,
    summary="Trigger job ingestion pipeline",
    description="Fetches raw jobs from selected adapter ('manual', 'remotive', 'adzuna', 'greenhouse', 'lever', 'jobspy', 'linkedin', 'indeed'), normalizes, validates, and idempotently persists into PostgreSQL.",
)
async def ingest_jobs(
    payload: IngestionRequest,
    db: AsyncSession = Depends(get_db),
) -> IngestionResult:
    source_key = payload.source.lower().strip()

    if source_key == "manual":
        adapter = ManualJobSourceAdapter()
    elif source_key == "remotive":
        adapter = RemotiveJobSourceAdapter()
    elif source_key == "adzuna":
        adapter = AdzunaJobSourceAdapter()
    elif source_key == "greenhouse":
        adapter = GreenhouseJobSourceAdapter()
    elif source_key == "lever":
        adapter = LeverJobSourceAdapter()
    elif source_key in ("jobspy", "linkedin", "indeed", "glassdoor"):
        sites = [source_key] if source_key != "jobspy" else ["linkedin", "indeed", "glassdoor"]
        adapter = JobSpyJobSourceAdapter(
            sites=sites,
            search_term=payload.search_term or "Software Engineer",
            location=payload.location or "Remote",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported job source adapter '{payload.source}'. Supported sources: 'manual', 'remotive', 'adzuna', 'greenhouse', 'lever', 'jobspy', 'linkedin', 'indeed'.",
        )

    service = JobIngestionService(db)
    try:
        result = await service.ingest_jobs(
            adapter=adapter,
            limit=payload.limit,
            use_cache=payload.use_cache,
        )
        return result
    except FileNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(err)}",
        )


@router.post(
    "/manual",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit custom job posting via text paste or URL",
    description="Resolves direct ATS links (Greenhouse, Lever) or parses raw job text using structured LLM extraction.",
)
async def submit_manual_job(
    payload: ManualJobSubmissionRequest,
    db: AsyncSession = Depends(get_db),
    llm_provider: BaseLLMProvider = Depends(get_llm_provider),
) -> JobResponse:
    service = ManualJobService(db, llm_provider)
    try:
        job = await service.ingest_manual_job(payload)
        return JobResponse.model_validate(job)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed processing manual job submission: {str(err)}",
        )


@router.get(

    "",
    response_model=list[JobResponse],
    status_code=status.HTTP_200_OK,
    summary="List normalized jobs",
    description="Retrieves a list of normalized job records stored in PostgreSQL with optional filtering.",
)
async def list_jobs(
    source: str | None = Query(default=None, description="Filter by job source"),
    is_remote: bool | None = Query(default=None, description="Filter by remote work status"),
    limit: int = Query(default=20, ge=1, le=100, description="Page size limit"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
    db: AsyncSession = Depends(get_db),
) -> list[JobResponse]:
    stmt = select(Job)
    if source:
        stmt = stmt.where(Job.source == source.strip())
    if is_remote is not None:
        stmt = stmt.where(Job.is_remote == is_remote)

    stmt = stmt.order_by(Job.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    jobs = result.scalars().all()
    return [JobResponse.model_validate(j) for j in jobs]


@router.get(
    "/worker/status",
    response_model=WorkerStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Worker Daemon & Pipeline Queue Status",
    description="Inspects background worker heartbeats, health vitality, and queue depths across all pipeline stages.",
)
async def get_worker_status(
    db: AsyncSession = Depends(get_db),
) -> WorkerStatusResponse:
    depths = await AsyncJobQueueWorker.get_queue_depths(db)

    stmt = select(WorkerHeartbeat).order_by(WorkerHeartbeat.last_heartbeat_at.desc())
    res = await db.execute(stmt)
    records = res.scalars().all()

    now_utc = datetime.now(timezone.utc)
    worker_responses = []
    active_count = 0

    for r in records:
        ts = r.last_heartbeat_at
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age = (now_utc - ts).total_seconds()
        alive = age < 30.0 and r.status != "stopped"
        if alive:
            active_count += 1

        worker_responses.append(
            WorkerHeartbeatResponse(
                worker_id=r.worker_id,
                status=r.status,
                last_heartbeat_at=r.last_heartbeat_at,
                jobs_processed=r.jobs_processed,
                current_stage=r.current_stage,
                is_alive=alive,
                age_seconds=round(age, 1),
            )
        )

    return WorkerStatusResponse(
        queue_depths=depths,
        workers=worker_responses,
        active_worker_count=active_count,
    )


@router.post(
    "/worker/trigger-cycle",
    response_model=WorkerStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger On-Demand Ingestion & Worker Processing Cycle",
    description="Executes an immediate job ingestion and queue processing cycle, returning updated metrics.",
)
async def trigger_worker_cycle(
    limit: int = Query(default=15, ge=1, le=100),
    source: str = Query(default="manual"),
    db: AsyncSession = Depends(get_db),
) -> WorkerStatusResponse:
    source_lower = source.strip().lower()
    if source_lower == "remotive":
        adapter = RemotiveJobSourceAdapter()
    elif source_lower == "adzuna":
        adapter = AdzunaJobSourceAdapter()
    elif source_lower == "greenhouse":
        adapter = GreenhouseJobSourceAdapter()
    elif source_lower == "lever":
        adapter = LeverJobSourceAdapter()
    elif source_lower in ("jobspy", "linkedin", "indeed", "glassdoor"):
        sites = [source_lower] if source_lower != "jobspy" else ["linkedin", "indeed", "glassdoor"]
        adapter = JobSpyJobSourceAdapter(sites=sites)
    else:
        adapter = ManualJobSourceAdapter()

    # 1. Ingest jobs
    service = JobIngestionService(db)
    ingest_result = await service.ingest_jobs(adapter=adapter, limit=limit)

    # 2. Enqueue for candidates if jobs inserted
    if ingest_result.inserted > 0:
        recent_stmt = (
            select(Job.id)
            .where(Job.source == adapter.source_name)
            .order_by(Job.created_at.desc())
            .limit(ingest_result.inserted)
        )
        recent_jobs = await db.execute(recent_stmt)
        job_ids = list(recent_jobs.scalars().all())
        await AsyncJobQueueWorker.enqueue_jobs_for_candidates(db, job_ids)

    # 3. Process a batch from queue
    worker = AsyncJobQueueWorker(db)
    await worker.process_batch(batch_size=20)

    # Return refreshed status
    return await get_worker_status(db=db)


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch job details",
    description="Retrieves a single normalized job record by its unique UUID.",
)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    stmt = select(Job).where(Job.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id '{job_id}' not found.",
        )

    return JobResponse.model_validate(job)
