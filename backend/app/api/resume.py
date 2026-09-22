import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import CandidateProfile, Resume
from app.schemas.resume import ResumeResponse
from app.services.resume_parser import parse_resume_file

router = APIRouter(prefix="/api/v1/resumes", tags=["Resumes"])


@router.post(
    "/upload",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and extract text from resume",
    description="Validates PDF/DOCX resume file, extracts raw text, and persists a Resume record.",
)
async def upload_resume(
    candidate_profile_id: UUID = Form(..., description="ID of the candidate profile"),
    file: UploadFile = File(..., description="Resume document (.pdf or .docx)"),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    # 1. Verify candidate profile exists
    stmt = select(CandidateProfile).where(CandidateProfile.id == candidate_profile_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate profile with id '{candidate_profile_id}' not found.",
        )

    # 2. Read in-memory file content
    try:
        content = await file.read()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded file content.",
        )

    filename = file.filename or "uploaded_resume"

    # 3. Validate and extract text using resume parser service
    try:
        raw_text = parse_resume_file(filename, content)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )

    # 4. Create and persist Resume database record
    new_resume = Resume(
        id=uuid.uuid4(),
        candidate_profile_id=candidate_profile_id,
        file_name=filename,
        raw_text=raw_text,
        parsed_json=None,  # Intentionally NULL for Step 1
    )
    db.add(new_resume)
    await db.commit()
    await db.refresh(new_resume)

    return ResumeResponse(
        id=new_resume.id,
        candidate_profile_id=new_resume.candidate_profile_id,
        file_name=new_resume.file_name,
        status="extracted",
        raw_text_length=len(new_resume.raw_text or ""),
        created_at=new_resume.created_at,
    )
