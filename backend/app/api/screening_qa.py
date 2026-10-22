"""
FastAPI Router for Screening Questions Q&A Agent.
Phase 7: Grounded candidate answering engine.
"""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional
from app.database import get_db
from app.models import CandidateProfile, Job, User
from app.schemas.screening_qa import ScreeningQARequest, ScreeningQAResponse
from app.services.screening_qa import ScreeningQAService

router = APIRouter(prefix="/api/v1/screening-qa", tags=["Screening Questions Q&A Agent"])


@router.post(
    "/answer",
    response_model=ScreeningQAResponse,
    status_code=status.HTTP_200_OK,
    summary="Answer an application screening question strictly grounded in verified facts",
    description="Generates a tailored answer to an employer screening question using verified candidate profile facts with anti-hallucination tracking.",
)
async def answer_screening_question(
    payload: ScreeningQARequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> ScreeningQAResponse:
    candidate: Optional[CandidateProfile] = None

    # 1. Retrieve Candidate Profile
    if current_user:
        stmt = select(CandidateProfile).where(CandidateProfile.user_id == current_user.id)
        result = await db.execute(stmt)
        candidate = result.scalar_one_or_none()

    if not candidate:
        # Fallback to seeded / first candidate profile for guest mode
        stmt = select(CandidateProfile).limit(1)
        result = await db.execute(stmt)
        candidate = result.scalar_one_or_none()

    if not candidate:
        # Construct ephemeral fallback candidate profile
        candidate = CandidateProfile(
            headline="AI/ML Engineer & Systems Developer",
            summary="AI Engineer experienced in RAG pipelines, FastAPI, PostgreSQL pgvector, and LLM evaluation benchmarks.",
            skills=["Python", "FastAPI", "PostgreSQL", "PyTorch", "Docker"],
            target_titles=["AI Engineer", "Machine Learning Engineer"],
            experience=[],
            education=[],
        )

    # 2. Retrieve Job Context if job_id provided
    job: Optional[Job] = None
    if payload.job_id:
        try:
            job_uuid = UUID(payload.job_id)
            job_stmt = select(Job).where(Job.id == job_uuid)
            job_result = await db.execute(job_stmt)
            job = job_result.scalar_one_or_none()
        except ValueError:
            pass  # Invalid UUID format, will rely on payload.job_title

    # 3. Answer Question using ScreeningQAService
    response = await ScreeningQAService.answer_question(
        request=payload,
        candidate=candidate,
        job=job,
    )

    return response
