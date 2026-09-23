from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters import ManualJobSourceAdapter, RemotiveJobSourceAdapter
from app.database import get_db
from app.models import Job
from app.schemas.job import IngestionRequest, IngestionResult, JobResponse
from app.services.job_ingestion import JobIngestionService

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


@router.post(
    "/ingest",
    response_model=IngestionResult,
    status_code=status.HTTP_200_OK,
    summary="Trigger job ingestion pipeline",
    description="Fetches raw jobs from selected adapter ('manual' or 'remotive'), normalizes, validates, and idempotently persists into PostgreSQL.",
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
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported job source adapter '{payload.source}'. Supported sources: 'manual', 'remotive'.",
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
