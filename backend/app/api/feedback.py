"""
Candidate Feedback & Discard Event API Router.
Handles job discard events, structured reason logging, and triggers
Rocchio query vector adaptation on candidate profile embeddings.
"""
from typing import List, Optional
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_current_user_optional
from app.database import get_db
from app.models import Application, CandidateProfile, FeedbackEvent, Job, JobMatch, User
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.personalization import rocchio_vector_update

router = APIRouter(prefix="/api/v1/feedback", tags=["Feedback & Personalization"])


@router.post(
    "/discard",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record job discard feedback and trigger Rocchio vector update",
    description="Logs candidate negative feedback reason and updates candidate profile vector embedding using Rocchio adaptation.",
)
async def discard_job(
    payload: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> FeedbackResponse:
    # 1. Resolve User and CandidateProfile
    if current_user:
        user_id = current_user.id
        stmt_prof = select(CandidateProfile).where(CandidateProfile.user_id == current_user.id)
        res_prof = await db.execute(stmt_prof)
        profile = res_prof.scalar_one_or_none()

        if not profile:
            # Fallback if profile not created yet
            profile = CandidateProfile(
                id=uuid.uuid4(),
                user_id=current_user.id,
                headline=f"{current_user.full_name} | Candidate",
            )
            db.add(profile)
            await db.commit()
            await db.refresh(profile)
    else:
        # Fallback for unauthenticated/demo mode
        if payload.candidate_profile_id:
            stmt_prof = select(CandidateProfile).where(CandidateProfile.id == payload.candidate_profile_id)
            res_prof = await db.execute(stmt_prof)
            profile = res_prof.scalar_one_or_none()
        else:
            stmt_prof = select(CandidateProfile).limit(1)
            res_prof = await db.execute(stmt_prof)
            profile = res_prof.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CandidateProfile not found. Please log in or initialize profile first.",
            )
        user_id = profile.user_id

    # 2. Verify Job exists
    stmt_job = select(Job).where(Job.id == payload.job_id)
    res_job = await db.execute(stmt_job)
    job = res_job.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{payload.job_id}' not found.",
        )

    # 3. Prevent duplicate active discards for the same job and profile
    stmt_existing = select(FeedbackEvent).where(
        FeedbackEvent.candidate_profile_id == profile.id,
        FeedbackEvent.job_id == job.id,
        FeedbackEvent.action == "discard",
    )
    res_existing = await db.execute(stmt_existing)
    existing_feedback = res_existing.scalar_one_or_none()

    if existing_feedback:
        # Update existing reason and notes
        existing_feedback.reason_code = payload.reason_code
        existing_feedback.notes = payload.notes
        existing_feedback.disliked_skill = payload.disliked_skill
        feedback_record = existing_feedback
    else:
        feedback_record = FeedbackEvent(
            id=uuid.uuid4(),
            user_id=user_id,
            candidate_profile_id=profile.id,
            job_id=job.id,
            action="discard",
            reason_code=payload.reason_code,
            notes=payload.notes,
            disliked_skill=payload.disliked_skill,
        )
        db.add(feedback_record)

    await db.commit()
    await db.refresh(feedback_record)

    # 4. Trigger Rocchio Vector Update if vectors are present
    vector_updated = False
    if profile.embedding is not None and job.embedding is not None:
        try:
            # Collect saved vectors (from applications)
            stmt_saved_jobs = (
                select(Job.embedding)
                .join(JobMatch, JobMatch.job_id == Job.id)
                .join(Application, Application.job_match_id == JobMatch.id)
                .where(
                    Application.user_id == user_id,
                    Job.embedding.is_not(None),
                )
            )
            res_saved = await db.execute(stmt_saved_jobs)
            saved_vectors = [row[0] for row in res_saved.all() if row[0] is not None]

            # Collect discarded vectors
            stmt_discarded_jobs = (
                select(Job.embedding)
                .join(FeedbackEvent, FeedbackEvent.job_id == Job.id)
                .where(
                    FeedbackEvent.candidate_profile_id == profile.id,
                    FeedbackEvent.action == "discard",
                    Job.embedding.is_not(None),
                )
            )
            res_discarded = await db.execute(stmt_discarded_jobs)
            discarded_vectors = [row[0] for row in res_discarded.all() if row[0] is not None]

            # Compute adjusted vector using Rocchio
            new_vector = rocchio_vector_update(
                profile_vector=list(profile.embedding),
                saved_vectors=saved_vectors,
                discarded_vectors=discarded_vectors,
                alpha=0.8,
                beta=0.2,
                gamma=0.1,
            )
            profile.embedding = new_vector
            await db.commit()
            vector_updated = True
        except Exception:
            # Allow feedback logging to succeed even if embedding recomputation fails
            await db.rollback()
            vector_updated = False

    return FeedbackResponse(
        id=feedback_record.id,
        user_id=feedback_record.user_id,
        candidate_profile_id=feedback_record.candidate_profile_id,
        job_id=feedback_record.job_id,
        action=feedback_record.action,
        reason_code=feedback_record.reason_code,
        notes=feedback_record.notes,
        disliked_skill=feedback_record.disliked_skill,
        created_at=feedback_record.created_at,
        vector_updated=vector_updated,
        message=f"Job marked as discarded ({feedback_record.reason_code}).",
    )


@router.get(
    "",
    response_model=List[FeedbackResponse],
    status_code=status.HTTP_200_OK,
    summary="List candidate feedback events",
    description="Retrieves history of discarded or saved jobs for the current candidate.",
)
async def list_feedback_events(
    candidate_profile_id: Optional[UUID] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> List[FeedbackResponse]:
    stmt = select(FeedbackEvent).order_by(FeedbackEvent.created_at.desc()).limit(limit)

    if current_user:
        stmt = stmt.where(FeedbackEvent.user_id == current_user.id)
    elif candidate_profile_id:
        stmt = stmt.where(FeedbackEvent.candidate_profile_id == candidate_profile_id)

    rows = (await db.execute(stmt)).scalars().all()
    return [
        FeedbackResponse(
            id=r.id,
            user_id=r.user_id,
            candidate_profile_id=r.candidate_profile_id,
            job_id=r.job_id,
            action=r.action,
            reason_code=r.reason_code,
            notes=r.notes,
            disliked_skill=r.disliked_skill,
            created_at=r.created_at,
            vector_updated=False,
            message="Feedback event record",
        )
        for r in rows
    ]


@router.delete(
    "/{feedback_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Undo or remove a feedback event",
    description="Removes a discard record, allowing the candidate to un-discard a job.",
)
async def delete_feedback_event(
    feedback_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    stmt = select(FeedbackEvent).where(FeedbackEvent.id == feedback_id)
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback record with ID '{feedback_id}' not found.",
        )

    if current_user and record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot delete feedback of another candidate.",
        )

    await db.delete(record)
    await db.commit()
    return None
