import json
import re
import uuid
from pathlib import Path
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_user_optional
from app.core.archetypes import list_available_archetypes
from app.database import get_db
from app.llm import BaseLLMProvider, get_llm_provider
from app.models import CandidateProfile, Job, JobMatch, User
from app.schemas.archetype import ArchetypeConfig
from app.schemas.ats_resume import ATSTailoredResume
from app.schemas.candidate_facts import CandidateFact, CandidateTruthVault, FactCategory
from app.schemas.tailoring import (
    AntiHallucinationAuditResult,
    ATSTailoringRequest,
    ConfirmSkillsAndTailorRequest,
    CustomJDTailoringRequest,
    CustomJDTailoringResponse,
    DocumentAuditRequest,
    DocumentTailoringRequest,
    DocumentTailoringResponse,
    PreTailoringAuditRequest,
    PreTailoringAuditResponse,
)
from app.services.custom_jd_service import CustomJDTailoringService
from app.services.document_tailoring import DocumentTailoringService
from app.services.fact_selector import FactSelectorEngine
from app.services.pdf_renderer import render_ats_resume_html
from app.services.pdf_generator import generate_ats_resume_pdf

router = APIRouter(prefix="/api/v1/tailoring", tags=["Document Tailoring & Grounding"])

FACTS_DATA_PATH = Path(__file__).parent.parent / "data" / "candidate_facts.json"


async def _verify_candidate_ownership(
    db: AsyncSession,
    candidate_profile_id: UUID,
    current_user: User,
) -> CandidateProfile:
    """Verify that candidate profile exists and is owned by the authenticated user."""
    stmt = select(CandidateProfile).where(CandidateProfile.id == candidate_profile_id)
    res = await db.execute(stmt)
    candidate = res.scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CandidateProfile with ID '{candidate_profile_id}' not found.",
        )
    if candidate.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not own this candidate profile.",
        )
    return candidate


def _categorize_skill(skill_name: str) -> str:
    s = skill_name.lower()
    if any(k in s for k in ["genai", "llm", "rag", "langchain", "langgraph", "prompt", "transformers", "agent"]):
        return "GenAI & LLMs"
    if any(k in s for k in ["machine learning", "ml", "pytorch", "tensorflow", "scikit", "model", "nlp", "vision", "deep learning"]):
        return "AI & Machine Learning"
    if any(k in s for k in ["fastapi", "django", "flask", "rest", "api", "asyncio", "microservice", "backend", "system"]):
        return "Backend & Systems"
    if any(k in s for k in ["sql", "postgres", "mysql", "redis", "mongodb", "database", "pgvector", "vector", "search", "bm25", "elasticsearch"]):
        return "Databases & Search"
    if any(k in s for k in ["docker", "kubernetes", "aws", "azure", "gcp", "cloud", "devops", "ci/cd", "git", "linux", "mlops", "databricks"]):
        return "DevOps & Cloud Practices"
    return "Core Technical Skills"


def _load_truth_vault(candidate: CandidateProfile | None = None) -> CandidateTruthVault:
    """Helper to load candidate verified facts, merging profile attributes."""
    vault: CandidateTruthVault | None = None
    if FACTS_DATA_PATH.exists():
        try:
            with open(FACTS_DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            vault = CandidateTruthVault.model_validate(data)
        except Exception:
            vault = None

    if not vault:
        vault = CandidateTruthVault(
            candidate_name="Candidate",
            headline="AI/ML Engineer & Systems Developer",
            email="candidate@example.com",
            location="India",
        )

    if candidate:
        if candidate.user:
            if candidate.user.full_name:
                vault.candidate_name = candidate.user.full_name
            if candidate.user.email:
                vault.email = candidate.user.email

        if candidate.headline:
            vault.headline = candidate.headline

        # Populate skills_inventory from verified profile skills
        if candidate.skills and len(candidate.skills) > 0:
            skills_inv: dict[str, list[str]] = {}
            for item in candidate.skills:
                skill_name = item if isinstance(item, str) else item.get("name", "")
                if not skill_name or not skill_name.strip():
                    continue
                skill_name = skill_name.strip()
                cat = _categorize_skill(skill_name)
                if cat not in skills_inv:
                    skills_inv[cat] = []
                if skill_name not in skills_inv[cat]:
                    skills_inv[cat].append(skill_name)
            if skills_inv:
                vault.skills_inventory = skills_inv

        # Populate education from verified profile education
        if candidate.education and len(candidate.education) > 0:
            edu_facts: list[CandidateFact] = []
            for idx, edu in enumerate(candidate.education):
                inst = edu.get("institution", "") if isinstance(edu, dict) else getattr(edu, "institution", "")
                deg = edu.get("degree", "") if isinstance(edu, dict) else getattr(edu, "degree", "")
                field = edu.get("field_of_study", "") if isinstance(edu, dict) else getattr(edu, "field_of_study", "")
                start = edu.get("start_date", "") if isinstance(edu, dict) else getattr(edu, "start_date", "")
                end = edu.get("end_date", "") if isinstance(edu, dict) else getattr(edu, "end_date", "")

                title_part = f"{deg}, {field}".strip(", ") if field else (deg or "Degree")
                dates_part = f"Graduated: {end}" if end else (start or "")
                phrasing = f"{title_part} — {inst} — {dates_part}".strip(" —")

                edu_facts.append(
                    CandidateFact(
                        fact_id=f"edu_db_{idx}",
                        category=FactCategory.EDUCATION,
                        entity_name=inst or "Institution",
                        role_or_title=title_part,
                        start_date=start,
                        end_date=end,
                        tags=["education", deg.lower() if deg else "", field.lower() if field else ""],
                        phrasings={"default": phrasing, "genai": phrasing, "swe": phrasing, "ai_eng": phrasing, "data": phrasing},
                        is_flagship=False,
                    )
                )
            if edu_facts:
                vault.education = edu_facts

        # Populate facts from verified profile experience
        if candidate.experience and len(candidate.experience) > 0:
            exp_facts: list[CandidateFact] = []
            for e_idx, exp in enumerate(candidate.experience):
                company = exp.get("company", "") if isinstance(exp, dict) else getattr(exp, "company", "")
                title = exp.get("title", "") if isinstance(exp, dict) else getattr(exp, "title", "")
                start = exp.get("start_date", "") if isinstance(exp, dict) else getattr(exp, "start_date", "")
                end = exp.get("end_date", "") if isinstance(exp, dict) else getattr(exp, "end_date", "")
                techs = exp.get("technologies", []) if isinstance(exp, dict) else getattr(exp, "technologies", [])
                if isinstance(techs, str):
                    techs = [t.strip() for t in techs.split(",") if t.strip()]

                achievements = (
                    exp.get("responsibilities") or exp.get("achievements") or []
                    if isinstance(exp, dict)
                    else (getattr(exp, "responsibilities", None) or getattr(exp, "achievements", None) or [])
                )
                if isinstance(achievements, str):
                    achievements = [a.strip() for a in achievements.splitlines() if a.strip()]

                tags = [t.lower() for t in (techs or [])] + [title.lower(), company.lower()]

                for a_idx, ach in enumerate(achievements):
                    if not ach or not str(ach).strip():
                        continue
                    ach_text = str(ach).strip()
                    exp_facts.append(
                        CandidateFact(
                            fact_id=f"exp_{e_idx}_{a_idx}",
                            category=FactCategory.EXPERIENCE,
                            entity_name=company or "Organization",
                            role_or_title=title or "Engineer",
                            start_date=start,
                            end_date=end,
                            tags=tags,
                            phrasings={
                                "default": ach_text,
                                "genai": ach_text,
                                "swe": ach_text,
                                "ai_eng": ach_text,
                                "data": ach_text,
                            },
                            is_flagship=(e_idx == 0),
                        )
                    )
            if exp_facts:
                vault.facts = exp_facts

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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    provider: BaseLLMProvider = Depends(get_llm_provider),
) -> DocumentTailoringResponse:
    await _verify_candidate_ownership(db, payload.candidate_profile_id, current_user)
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AntiHallucinationAuditResult:
    # 1. Fetch CandidateProfile and verify ownership
    candidate = await _verify_candidate_ownership(db, payload.candidate_profile_id, current_user)

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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ATSTailoredResume:
    # 1. Fetch CandidateProfile and verify ownership
    candidate = await _verify_candidate_ownership(db, payload.candidate_profile_id, current_user)

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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    resume = await generate_ats_resume(payload=payload, current_user=current_user, db=db)
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    resume = await generate_ats_resume(payload=payload, current_user=current_user, db=db)
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
    current_user: User = Depends(get_current_user),
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


@router.post(
    "/custom-jd/tailor",
    response_model=CustomJDTailoringResponse,
    status_code=status.HTTP_200_OK,
    summary="Tailor resume, audit gaps, and generate cold outreach for external raw JD",
    description="Parses external JD, runs recruiter 6-sec red flag scan and ATS score, assembles 1-page ATS resume, and generates 4-line hiring manager cold message.",
)
async def tailor_custom_external_jd(
    payload: CustomJDTailoringRequest,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> CustomJDTailoringResponse:
    # 1. Fetch CandidateProfile for authenticated user if logged in
    candidate = None
    if current_user:
        try:
            stmt_cand = select(CandidateProfile).where(CandidateProfile.user_id == current_user.id)
            candidate = (await db.execute(stmt_cand)).scalar_one_or_none()
        except Exception:
            candidate = None

    vault = _load_truth_vault(candidate)

    # 2. Execute Recruiter Tailoring & Gap Audit
    response = CustomJDTailoringService.tailor_custom_jd(
        vault=vault,
        request=payload,
    )

    # 3. Optional: Persist to Application Tracker
    if payload.save_to_tracker and current_user:
        try:
            new_job = Job(
                source="custom_paste",
                external_id=f"custom_{current_user.id}_{uuid.uuid4().hex[:8]}",
                title=response.job_title,
                company=response.company_name,
                description_raw=payload.job_description,
                skills_required=response.recruiter_audit.gap_table and [g.missing_tech for g in response.recruiter_audit.gap_table] or [],
                is_active=True,
            )
            db.add(new_job)
            await db.flush()

            # Link JobMatch if candidate exists in DB
            if candidate and candidate.id:
                match = JobMatch(
                    candidate_profile_id=candidate.id,
                    job_id=new_job.id,
                    overall_score=response.recruiter_audit.ats_score / 10.0,
                    status="saved",
                )
                db.add(match)

            await db.commit()
            await db.refresh(new_job)
            response.job_id = new_job.id
        except Exception:
            pass

    return response


@router.post(
    "/pre-audit",
    response_model=PreTailoringAuditResponse,
    status_code=status.HTTP_200_OK,
    summary="Interactive Pre-Tailoring Skill Interview",
    description="Analyzes the target JD against the truth vault, detects missing skills, and asks the user in conversational Hinglish if they know them before tailoring.",
)
async def pre_tailoring_audit(
    payload: PreTailoringAuditRequest,
) -> PreTailoringAuditResponse:
    vault = _load_truth_vault()
    return CustomJDTailoringService.generate_pre_tailoring_interview(
        vault=vault,
        request=payload,
    )


@router.post(
    "/confirm-and-tailor",
    response_model=CustomJDTailoringResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm skills and tailor resume",
    description="Merges user-confirmed missing skills into the candidate truth vault without hallucination, and generates the tailored resume and recruiter review.",
)
async def confirm_skills_and_tailor(
    payload: ConfirmSkillsAndTailorRequest,
) -> CustomJDTailoringResponse:
    vault = _load_truth_vault()

    # Merge confirmed skills into vault
    updated_vault = CustomJDTailoringService.merge_confirmed_skills(
        vault=vault,
        confirmed_skills=payload.confirmed_skills,
    )

    tailoring_request = CustomJDTailoringRequest(
        job_description=payload.job_description,
        job_title=payload.job_title,
        company_name=payload.company_name,
        language_tone=payload.language_tone,
        save_to_tracker=False,
    )

    # Run tailoring with updated vault
    return CustomJDTailoringService.tailor_custom_jd(
        vault=updated_vault,
        request=tailoring_request,
    )




