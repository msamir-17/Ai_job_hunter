import json
import re
from pathlib import Path
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.archetypes import list_available_archetypes
from app.database import get_db
from app.llm import BaseLLMProvider, get_llm_provider
from app.models import CandidateProfile, Job
from app.schemas.archetype import ArchetypeConfig
from app.schemas.ats_resume import ATSTailoredResume
from app.schemas.candidate_facts import CandidateTruthVault
from app.schemas.tailoring import (
    AntiHallucinationAuditResult,
    ATSTailoringRequest,
    DocumentAuditRequest,
    DocumentTailoringRequest,
    DocumentTailoringResponse,
)
from app.services.document_tailoring import DocumentTailoringService
from app.services.fact_selector import FactSelectorEngine
from app.services.pdf_renderer import render_ats_resume_html
from app.services.pdf_generator import generate_ats_resume_pdf

router = APIRouter(prefix="/api/v1/tailoring", tags=["Document Tailoring & Grounding"])

FACTS_DATA_PATH = Path(__file__).parent.parent / "data" / "candidate_facts.json"


def _load_truth_vault(candidate: CandidateProfile) -> CandidateTruthVault:
    """Helper to load candidate truth vault data, merging profile attributes."""
    if FACTS_DATA_PATH.exists():
        with open(FACTS_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        vault = CandidateTruthVault.model_validate(data)
    else:
        vault = CandidateTruthVault(
            candidate_name=getattr(candidate, "full_name", "") or "Mohd Samir",
            headline=candidate.headline or "AI/ML Engineer",
            email="samir.dev@example.com",
            location="Mumbai, India",
        )

    # If candidate profile has headline, prefer it
    if candidate.headline:
        vault.headline = candidate.headline
    return vault


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


@router.get(
    "/archetypes",
    response_model=list[ArchetypeConfig],
    status_code=status.HTTP_200_OK,
    summary="List available resume archetype lenses",
    description="Returns all pre-configured archetype presets (genai, swe, ai_eng, data) with their layout priority and keywords.",
)
async def get_available_archetypes() -> list[ArchetypeConfig]:
    return list_available_archetypes()


@router.post(
    "/ats-resume",
    response_model=ATSTailoredResume,
    status_code=status.HTTP_200_OK,
    summary="Assemble ATS-compliant tailored resume with one-page line budget audit",
    description="Selects candidate facts, pre-approved angle phrasings, and prioritized skills based on the target job and archetype lens.",
)
async def generate_ats_resume(
    payload: ATSTailoringRequest,
    db: AsyncSession = Depends(get_db),
) -> ATSTailoredResume:
    # 1. Fetch CandidateProfile
    stmt_cand = select(CandidateProfile).where(CandidateProfile.id == payload.candidate_profile_id)
    candidate = (await db.execute(stmt_cand)).scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CandidateProfile with ID '{payload.candidate_profile_id}' not found.",
        )

    # 2. Fetch Job
    stmt_job = select(Job).where(Job.id == payload.job_id)
    job = (await db.execute(stmt_job)).scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{payload.job_id}' not found.",
        )

    vault = _load_truth_vault(candidate)
    resume = FactSelectorEngine.assemble_tailored_resume(
        vault=vault,
        job_title=job.title,
        job_company=job.company,
        job_description=job.description_raw or "",
        skills_required=job.skills_required,
        forced_archetype_id=payload.forced_archetype_id,
    )
    return resume


@router.post(
    "/ats-resume/html",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
    summary="Render standalone ATS printable HTML resume",
    description="Renders an ATS-compliant tailored resume into standalone HTML with embedded print stylesheet for browser printing or PDF conversion.",
)
async def render_ats_resume_document(
    payload: ATSTailoringRequest,
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    resume = await generate_ats_resume(payload=payload, db=db)
    html_content = render_ats_resume_html(resume)
    return HTMLResponse(content=html_content, status_code=200)


@router.post(
    "/ats-resume/pdf",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Download ATS-compliant tailored resume as binary PDF",
    description="Generates an ATS-compliant tailored resume from database models and compiles to a pixel-perfect binary PDF.",
)
async def export_ats_resume_pdf(
    payload: ATSTailoringRequest,
    db: AsyncSession = Depends(get_db),
) -> Response:
    resume = await generate_ats_resume(payload=payload, db=db)
    pdf_bytes = generate_ats_resume_pdf(resume)
    clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", resume.candidate_name)
    filename = f"{clean_name}_ATS_Resume.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.post(
    "/ats-resume/download-from-data",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Directly convert existing ATSTailoredResume data to downloadable PDF",
    description="Takes currently rendered client-side ATSTailoredResume JSON data and compiles to a binary PDF attachment.",
)
async def convert_ats_resume_json_to_pdf(
    resume: ATSTailoredResume,
) -> Response:
    pdf_bytes = generate_ats_resume_pdf(resume)
    clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", resume.candidate_name)
    filename = f"{clean_name}_ATS_Resume.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )

