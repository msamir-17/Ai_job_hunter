from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.llm import BaseLLMProvider, get_llm_provider
from app.models import CandidateProfile, Job
from app.schemas.tailoring import (
    AntiHallucinationAuditResult,
    DocumentAuditRequest,
    DocumentTailoringRequest,
    DocumentTailoringResponse,
)
from app.services.document_tailoring import DocumentTailoringService

router = APIRouter(prefix="/api/v1/tailoring", tags=["Document Tailoring & Grounding"])


@router.post(
    "/generate",
    response_model=DocumentTailoringResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate grounded resume bullets and cover letter draft",
    description="Generates job-tailored resume bullets and cover letter strictly derived from verified candidate profile data, and runs an anti-hallucination audit.",
)
async def generate_tailored_documents(
    payload: DocumentTailoringRequest,
    db: AsyncSession = Depends(get_db),
    provider: BaseLLMProvider = Depends(get_llm_provider),
) -> DocumentTailoringResponse:
    service = DocumentTailoringService(db=db, provider=provider)
    try:
        response = await service.generate_application_package(
            candidate_profile_id=payload.candidate_profile_id,
            job_id=payload.job_id,
        )
        return response
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document tailoring failed: {str(err)}",
        )


@router.post(
    "/audit",
    response_model=AntiHallucinationAuditResult,
    status_code=status.HTTP_200_OK,
    summary="Audit arbitrary document text against candidate profile facts",
    description="Deterministically audits resume bullet points or cover letters to ensure zero unverified skills or tools are claimed.",
)
async def audit_document_text(
    payload: DocumentAuditRequest,
    db: AsyncSession = Depends(get_db),
) -> AntiHallucinationAuditResult:
    # 1. Fetch CandidateProfile
    stmt_cand = select(CandidateProfile).where(CandidateProfile.id == payload.candidate_profile_id)
    candidate = (await db.execute(stmt_cand)).scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CandidateProfile with ID '{payload.candidate_profile_id}' not found.",
        )

    # 2. Fetch Job if job_id provided
    job: Job | None = None
    if payload.job_id:
        stmt_job = select(Job).where(Job.id == payload.job_id)
        job = (await db.execute(stmt_job)).scalar_one_or_none()

    service = DocumentTailoringService(db=db)
    result = service.audit_text_for_hallucinations(
        text=payload.text_to_audit,
        candidate=candidate,
        job=job,
    )
    return result
