import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.llm import BaseLLMProvider, get_llm_provider
from app.models import CandidateProfile, Resume
from app.schemas.resume import ResumeExtractResponse, ResumeResponse
from app.services.resume_extractor import extract_structured_resume_draft
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
        parsed_json=None,  # Intentionally NULL until extraction is triggered
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


@router.post(
    "/{resume_id}/extract",
    response_model=ResumeExtractResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract structured AI resume draft",
    description="Uses configured LLM provider to extract structured candidate draft JSON into Resume.parsed_json. Leaves CandidateProfile untouched.",
)
async def extract_resume(
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
    provider: BaseLLMProvider = Depends(get_llm_provider),
) -> ResumeExtractResponse:
    # 1. Fetch Resume record by ID
    stmt = select(Resume).where(Resume.id == resume_id)
    result = await db.execute(stmt)
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with id '{resume_id}' not found.",
        )

    # 2. Check that raw_text is present
    if not resume.raw_text or not resume.raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume has no raw text available for extraction. Upload a valid document first.",
        )

    # 4. Perform structured AI extraction
    try:
        draft = await extract_structured_resume_draft(resume.raw_text, provider=provider)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Structured extraction failed: {str(err)}",
        )

    # 5. Persist JSON draft into Resume.parsed_json (CandidateProfile remains untouched)
    resume.parsed_json = draft.model_dump()
    await db.commit()
    await db.refresh(resume)

    return ResumeExtractResponse(
        id=resume.id,
        candidate_profile_id=resume.candidate_profile_id,
        file_name=resume.file_name,
        status="draft_generated",
        draft=draft,
    )
