import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import CandidateProfile, User
from app.schemas.candidate_profile import (
    CandidateProfileCreate,
    CandidateProfileResponse,
    CandidateProfileUpdate,
)

router = APIRouter(prefix="/api/v1/candidate-profile", tags=["Candidate Profile"])


@router.post(
    "",
    response_model=CandidateProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create candidate profile",
    description="Creates a new candidate profile associated with an existing user.",
)
async def create_candidate_profile(
    payload: CandidateProfileCreate,
    db: AsyncSession = Depends(get_db),
) -> CandidateProfileResponse:
    # 1. Verify user exists
    user_stmt = select(User).where(User.id == payload.user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with id '{payload.user_id}' does not exist.",
        )

    # 2. Check if user already has a candidate profile (one-to-one relationship)
    existing_stmt = select(CandidateProfile).where(
        CandidateProfile.user_id == payload.user_id
    )
    existing_result = await db.execute(existing_stmt)
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Candidate profile already exists for user '{payload.user_id}'.",
        )

    # 3. Create and persist candidate profile
    profile_data = payload.model_dump()
    new_profile = CandidateProfile(id=uuid.uuid4(), **profile_data)
    db.add(new_profile)

    try:
        await db.commit()
        await db.refresh(new_profile)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error occurred while creating profile.",
        )

    return new_profile


@router.get(
    "/{profile_id}",
    response_model=CandidateProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch candidate profile",
    description="Retrieves a candidate profile by its unique profile ID.",
)
async def get_candidate_profile(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CandidateProfileResponse:
    stmt = select(CandidateProfile).where(CandidateProfile.id == profile_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found.",
        )

    return profile


@router.put(
    "/{profile_id}",
    response_model=CandidateProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update candidate profile",
    description="Updates editable candidate profile fields for an existing profile.",
)
async def update_candidate_profile(
    profile_id: UUID,
    payload: CandidateProfileUpdate,
    db: AsyncSession = Depends(get_db),
) -> CandidateProfileResponse:
    stmt = select(CandidateProfile).where(CandidateProfile.id == profile_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    try:
        await db.commit()
        await db.refresh(profile)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database error occurred while updating candidate profile.",
        )

    return profile


@router.delete(
    "/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete candidate profile",
    description="Deletes a candidate profile by its unique profile ID.",
)
async def delete_candidate_profile(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    stmt = select(CandidateProfile).where(CandidateProfile.id == profile_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found.",
        )

    await db.delete(profile)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
