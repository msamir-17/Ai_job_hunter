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
    profile_data = payload.model_dump(exclude={"full_name", "email", "phone", "location"})
    new_profile = CandidateProfile(id=uuid.uuid4(), **profile_data)
    db.add(new_profile)

    try:
        await db.commit()
        await db.refresh(new_profile)
        new_profile.full_name = user.full_name
        new_profile.email = user.email
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error occurred while creating profile.",
        )

    return new_profile



@router.get(
    "",
    response_model=list[CandidateProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="List candidate profiles",
    description="Retrieves a list of candidate profiles stored in PostgreSQL.",
)
async def list_candidate_profiles(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
) -> list[CandidateProfileResponse]:
    stmt = select(CandidateProfile).order_by(CandidateProfile.id.desc()).limit(limit)
    result = await db.execute(stmt)
    profiles = result.scalars().all()
    return list(profiles)


@router.get(
    "/active",
    response_model=CandidateProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get or initialize active candidate profile",
    description="Returns the active candidate profile, or creates a default demo user and profile if none exists.",
)

async def get_or_create_active_profile(
    db: AsyncSession = Depends(get_db),
) -> CandidateProfileResponse:
    stmt = select(CandidateProfile).order_by(CandidateProfile.id.desc()).limit(1)
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()
    if existing:
        # Load user details if attached
        user_stmt = select(User).where(User.id == existing.user_id)
        u_res = await db.execute(user_stmt)
        u = u_res.scalar_one_or_none()
        if u:
            existing.full_name = u.full_name
            existing.email = u.email
        return existing


    # Create default user
    demo_user = User(
        id=uuid.uuid4(),
        email="candidate@aijobhunter.local",
        hashed_password="demo_password_hash",
        full_name="Job Seeker",
    )
    db.add(demo_user)
    await db.flush()

    # Create candidate profile
    new_profile = CandidateProfile(
        id=uuid.uuid4(),
        user_id=demo_user.id,
        headline="AI & Machine Learning Engineer",
        summary="Candidate profile ready for resume upload and grounding.",
        skills=["Python", "PyTorch", "FastAPI", "PostgreSQL", "Machine Learning"],
        target_titles=["AI Engineer", "ML Engineer", "Software Engineer"],
    )
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
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

    update_data = payload.model_dump(exclude_unset=True, exclude={"full_name", "email", "phone", "location"})
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
