from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import CandidateProfile, JobMatch
from app.schemas.matching import BatchFilterResponse, FilterJobRequest, JobFilterResult
from app.services.deterministic_filter import DeterministicFilterService

router = APIRouter(prefix="/api/v1/matching", tags=["Matching & Filtering"])


@router.post(
    "/deterministic/filter",
    response_model=BatchFilterResponse,
    status_code=status.HTTP_200_OK,
    summary="Filter jobs deterministically for a candidate profile",
    description="Compares CandidateProfile against ingested jobs using zero-cost Python rules (experience gap, role normalization, work mode). Persists results into PostgreSQL job_matches.",
)
async def filter_jobs_deterministically(
    payload: FilterJobRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchFilterResponse:
    service = DeterministicFilterService(config=payload.config)

    try:
        results = await service.filter_and_persist_jobs(
            db=db,
            candidate_profile_id=payload.candidate_profile_id,
            limit=payload.limit,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    shortlisted_count = sum(1 for r in results if r.overall_status == "shortlisted")
    review_count = sum(1 for r in results if r.overall_status == "review")
    rejected_count = sum(1 for r in results if r.overall_status == "rejected")

    return BatchFilterResponse(
        candidate_profile_id=payload.candidate_profile_id,
        total_evaluated=len(results),
        shortlisted_count=shortlisted_count,
        review_count=review_count,
        rejected_count=rejected_count,
        results=results,
    )


@router.get(
    "/candidate/{candidate_profile_id}/matches",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get stored job matches for a candidate profile",
    description="Retrieve paginated job matches evaluated for a candidate, with optional filtering by match status ('shortlisted', 'review', 'rejected').",
)
async def get_candidate_job_matches(
    candidate_profile_id: UUID,
    status_filter: str | None = Query(default=None, alias="status", description="Filter by status: 'shortlisted', 'review', or 'rejected'"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    # Verify candidate exists
    stmt_candidate = select(CandidateProfile).where(CandidateProfile.id == candidate_profile_id)
    res_candidate = await db.execute(stmt_candidate)
    if not res_candidate.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CandidateProfile with ID {candidate_profile_id} not found.",
        )

    stmt_matches = (
        select(JobMatch)
        .options(selectinload(JobMatch.job))
        .where(JobMatch.candidate_profile_id == candidate_profile_id)
    )

    if status_filter:
        s_clean = status_filter.strip().lower()
        stmt_matches = stmt_matches.where(JobMatch.status == s_clean)

    stmt_matches = stmt_matches.limit(limit).offset(offset)
    res_matches = await db.execute(stmt_matches)
    matches = res_matches.scalars().all()

    output = []
    for m in matches:
        output.append({
            "id": m.id,
            "candidate_profile_id": m.candidate_profile_id,
            "job_id": m.job_id,
            "job_title": m.job.title if m.job else None,
            "job_company": m.job.company if m.job else None,
            "job_location": m.job.location if m.job else None,
            "job_is_remote": m.job.is_remote if m.job else False,
            "passed_deterministic": m.passed_deterministic,
            "status": m.status,
            "matched_skills": m.matched_skills or [],
            "missing_skills": m.missing_skills or [],
            "analysis_summary": m.analysis_summary,
        })

    return output
