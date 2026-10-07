from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.llm import BaseLLMProvider, get_llm_provider
from app.models import CandidateProfile, Job, JobMatch
from app.schemas.matching import (
    AnalyzeJobMatchRequest,
    BatchAnalyzeMatchesRequest,
    BatchAnalyzeMatchesResponse,
    BatchFilterResponse,
    BatchJevEvalRequest,
    BatchJevEvalResponse,
    FilterJobRequest,
    JobFilterResult,
    JobMatchAnalysisResult,
    PipelineRunRequest,
    PipelineRunResponse,
    VectorSearchRequest,
    VectorSearchResponse,
)
from app.graph.workflow import run_matching_pipeline
from app.services.deterministic_filter import DeterministicFilterService
from app.services.jev_matching import JevMatchingService
from app.services.llm_matching import LLMMatchingService
from app.services.vector_search import VectorSearchService

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


@router.post(
    "/vector/search",
    response_model=VectorSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search top semantic matches via pgvector cosine similarity",
    description="Compares CandidateProfile dense vector against job embeddings in PostgreSQL using cosine distance (<=>). Ranks closest matches and persists vector_score into JobMatch.",
)
async def search_jobs_by_vector(
    payload: VectorSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> VectorSearchResponse:
    service = VectorSearchService(db=db)
    try:
        results = await service.search_and_persist_matches(payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return VectorSearchResponse(
        candidate_profile_id=payload.candidate_profile_id,
        total_matches=len(results),
        results=results,
    )


@router.post(
    "/llm/analyze",
    response_model=JobMatchAnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Stage 3 LLM skill gap and match analysis for a single job",
    description="Compares CandidateProfile against Job description using active LLM provider to extract matched skills, missing skills, match score (0-100), and rationale.",
)
async def analyze_single_job_match(
    payload: AnalyzeJobMatchRequest,
    db: AsyncSession = Depends(get_db),
    provider: BaseLLMProvider = Depends(get_llm_provider),
) -> JobMatchAnalysisResult:
    service = LLMMatchingService(db=db, provider=provider)
    try:
        result = await service.analyze_single_match(
            candidate_profile_id=payload.candidate_profile_id,
            job_id=payload.job_id,
        )
        return result
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM match analysis failed: {str(err)}",
        )


@router.post(
    "/llm/analyze-batch",
    response_model=BatchAnalyzeMatchesResponse,
    status_code=status.HTTP_200_OK,
    summary="Stage 3 LLM batch skill gap analysis for top vector matches",
    description="Evaluates top shortlisted / vector-ranked jobs for a candidate using the active LLM provider.",
)
async def analyze_batch_job_matches(
    payload: BatchAnalyzeMatchesRequest,
    db: AsyncSession = Depends(get_db),
    provider: BaseLLMProvider = Depends(get_llm_provider),
) -> BatchAnalyzeMatchesResponse:
    service = LLMMatchingService(db=db, provider=provider)
    try:
        results = await service.analyze_batch_matches(
            candidate_profile_id=payload.candidate_profile_id,
            job_ids=payload.job_ids,
            limit=payload.limit,
            min_vector_score=payload.min_vector_score,
        )
        return BatchAnalyzeMatchesResponse(
            candidate_profile_id=payload.candidate_profile_id,
            total_analyzed=len(results),
            results=results,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch LLM analysis failed: {str(err)}",
        )


@router.post(
    "/pipeline/run",
    response_model=PipelineRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute full LangGraph agent matching pipeline end-to-end",
    description="Orchestrates Stage 1 Deterministic Filtering -> Stage 2 Vector Similarity -> Stage 3 LLM Skill Gap Analysis via stateful LangGraph workflow.",
)
async def run_pipeline_for_job_match(
    payload: PipelineRunRequest,
    db: AsyncSession = Depends(get_db),
    provider: BaseLLMProvider = Depends(get_llm_provider),
) -> PipelineRunResponse:
    final_state = await run_matching_pipeline(
        db=db,
        candidate_profile_id=payload.candidate_profile_id,
        job_id=payload.job_id,
        llm_provider=provider,
    )

    if final_state.get("error_message"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=final_state["error_message"],
        )

    # Fetch saved JobMatch ORM ID
    stmt_match = select(JobMatch.id).where(
        JobMatch.candidate_profile_id == payload.candidate_profile_id,
        JobMatch.job_id == payload.job_id,
    )
    match_res = await db.execute(stmt_match)
    job_match_id = match_res.scalar_one_or_none()

    return PipelineRunResponse(
        id=job_match_id,
        candidate_profile_id=payload.candidate_profile_id,
        job_id=payload.job_id,
        passed_deterministic=final_state.get("passed_deterministic", False),
        deterministic_status=final_state.get("deterministic_status"),
        vector_score=final_state.get("vector_score"),
        vector_passed=final_state.get("vector_passed"),
        llm_score=final_state.get("llm_score"),
        matched_skills=final_state.get("matched_skills", []),
        missing_skills=final_state.get("missing_skills", []),
        analysis_summary=final_state.get("analysis_summary"),
        recommendation=final_state.get("recommendation"),
        overall_status=final_state.get("overall_status", "review"),
        current_stage=final_state.get("current_stage", "completed"),
        error_message=final_state.get("error_message"),
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
            "vector_score": m.vector_score,
            "llm_score": m.llm_score,
            "status": m.status,
            "matched_skills": m.matched_skills or [],
            "missing_skills": m.missing_skills or [],
            "analysis_summary": m.analysis_summary,
        })

    return output


@router.post(
    "/jev/evaluate",
    response_model=BatchJevEvalResponse,
    status_code=status.HTTP_200_OK,
    summary="Stage 2.5 Jev System One Fast-Pass Matching Filter",
    description="Fast evaluation (~100ms/job) filtering candidates and enforcing experience ceiling preferences using Jev.",
)
async def evaluate_matches_with_jev(
    payload: BatchJevEvalRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchJevEvalResponse:
    # 1. Fetch CandidateProfile
    stmt_candidate = select(CandidateProfile).where(CandidateProfile.id == payload.candidate_profile_id)
    res_candidate = await db.execute(stmt_candidate)
    candidate = res_candidate.scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CandidateProfile with ID {payload.candidate_profile_id} not found.",
        )

    # 2. Fetch Jobs
    if payload.job_ids:
        stmt_jobs = select(Job).where(Job.id.in_(payload.job_ids))
    else:
        # Default to jobs that passed Stage 1 deterministic filtering
        stmt_matches = (
            select(JobMatch.job_id)
            .where(
                JobMatch.candidate_profile_id == payload.candidate_profile_id,
                JobMatch.passed_deterministic.is_(True),
            )
            .limit(30)
        )
        res_match_ids = await db.execute(stmt_matches)
        job_ids = list(res_match_ids.scalars().all())
        if not job_ids:
            return BatchJevEvalResponse(
                candidate_profile_id=candidate.id,
                total_evaluated=0,
                passed_count=0,
                results=[],
            )
        stmt_jobs = select(Job).where(Job.id.in_(job_ids))

    res_jobs = await db.execute(stmt_jobs)
    jobs = list(res_jobs.scalars().all())

    # 3. Evaluate with Jev
    jev_service = JevMatchingService(confidence_threshold=payload.confidence_threshold)
    results = await jev_service.evaluate_batch(
        candidate=candidate,
        jobs=jobs,
        max_experience_years=payload.max_experience_years,
    )

    passed_count = sum(1 for r in results if r.passed_jev_filter)

    return BatchJevEvalResponse(
        candidate_profile_id=candidate.id,
        total_evaluated=len(results),
        passed_count=passed_count,
        results=results,
    )

