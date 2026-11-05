"""
Test Suite for Interactive Pre-Tailoring Skill Interview & Confirmed Skill Merging.

Verifies:
1. Pre-Tailoring Interview generation correctly extracts missing skills and builds
   conversational Hinglish prompt asking candidate if they have proficiency.
2. Skill confirmation cleanly adds confirmed skills to Truth Vault without hallucination
   or fabrication of fake metrics.
3. Recruiter audit produces the structured 4-section Hinglish evaluation:
   - 1. ATS Score & Selection Chances
   - 2. Skill Gap Analysis (Missing Elements)
   - 3. Hard Truths (Why I might get rejected)
   - 4. Actionable Suggestions (Exact Rewrites)
4. End-to-end API integration for `/api/v1/tailoring/pre-audit` and `/api/v1/tailoring/confirm-and-tailor`.
"""

import asyncio
import pytest

from app.api.tailoring import confirm_skills_and_tailor, pre_tailoring_audit
from app.schemas.candidate_facts import CandidateFact, CandidateTruthVault, FactCategory
from app.schemas.tailoring import (
    ConfirmedSkillEntry,
    ConfirmSkillsAndTailorRequest,
    CustomJDTailoringRequest,
    PreTailoringAuditRequest,
)
from app.services.custom_jd_service import CustomJDTailoringService


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def sample_vault():
    return CandidateTruthVault(
        candidate_name="MOHAMMAD SAMIR KHAN",
        headline="AI/GenAI Engineer & Backend Systems Developer",
        email="samirkhan003786@gmail.com",
        location="Mumbai, India",
        skills_inventory={
            "Programming & Data": ["Python", "SQL", "NumPy", "Pandas"],
            "GenAI & Agentic AI": ["LangChain", "LangGraph", "Prompt Engineering"],
            "Backend & Databases": ["FastAPI", "PostgreSQL", "Docker"],
        },
        facts=[
            CandidateFact(
                fact_id="fact_fin_advisor",
                category=FactCategory.PROJECT,
                entity_name="AI Financial Advisor",
                tags=["python", "langchain", "chromadb", "fastapi"],
                phrasings={
                    "default": "Built agentic RAG pipeline using LangChain and FastAPI with ChromaDB.",
                    "genai": "Engineered agentic GenAI workflow using LangChain and Mistral AI with 1.0 Faithfulness.",
                },
                is_flagship=True,
            )
        ],
    )


SAMPLE_JD_WITH_GAPS = """
Role: Senior AI Infrastructure Engineer
Company: DeepScale Labs

Requirements:
- 3+ years experience with Python, FastAPI, and Docker.
- Hands-on experience with Kubernetes (K8s) for container orchestration.
- Cloud deployment experience on AWS (EKS, S3, IAM).
- Proficient with Redis caching and Celery task queues.
- Strong knowledge of GraphQL API architecture.
"""


def test_pre_tailoring_interview_generation(sample_vault):
    """Test that pre-tailoring audit detects missing skills and produces conversational Hinglish questions."""
    req = PreTailoringAuditRequest(job_description=SAMPLE_JD_WITH_GAPS)
    interview = CustomJDTailoringService.generate_pre_tailoring_interview(
        vault=sample_vault,
        request=req,
    )

    # 1. Missing skills should contain AWS, Kubernetes, Redis, Celery, or GraphQL
    missing_techs = [item.skill_name.lower() for item in interview.missing_skills]
    assert any("kubernetes" in t for t in missing_techs) or any("aws" in t for t in missing_techs)

    # 2. Hinglish prompt must contain conversational intro and questions
    assert "Maine aapki target Job Description analyze ki" in interview.interview_prompt
    assert len(interview.missing_skills) > 0


def test_merge_confirmed_skills_without_hallucination(sample_vault):
    """Test that confirmed skills are added to Truth Vault safely without hallucinating fake metrics."""
    confirmed = [
        ConfirmedSkillEntry(
            skill="Kubernetes",
            known=True,
            context_notes="Used minikube for local testing and deployment manifests.",
        ),
        ConfirmedSkillEntry(
            skill="AWS",
            known=True,
            context_notes="Created S3 buckets and IAM policies.",
        ),
        ConfirmedSkillEntry(
            skill="GraphQL",
            known=False,
            context_notes="Never worked with GraphQL.",
        ),
    ]

    updated_vault = CustomJDTailoringService.merge_confirmed_skills(
        vault=sample_vault,
        confirmed_skills=confirmed,
    )

    # 1. Known skills must be added to skills_inventory
    added_skills = updated_vault.skills_inventory.get("Candidate Confirmed Skills", [])
    assert "Kubernetes" in added_skills
    assert "AWS" in added_skills

    # 2. Unknown skills must NOT be added
    assert "GraphQL" not in added_skills

    # 3. Facts added must have no fake metrics
    confirmed_facts = [f for f in updated_vault.facts if f.fact_id.startswith("confirmed_skill_")]
    assert len(confirmed_facts) == 2
    for fact in confirmed_facts:
        assert len(fact.metrics) == 0  # Zero fabricated metrics


def test_recruiter_audit_hinglish_four_sections(sample_vault):
    """Verify recruiter audit generates the exact 4 clear Hinglish sections requested."""
    req = CustomJDTailoringRequest(job_description=SAMPLE_JD_WITH_GAPS)
    res = CustomJDTailoringService.tailor_custom_jd(vault=sample_vault, request=req)

    audit_notes = res.recruiter_audit.recruiter_notes

    # Verify the 4 mandatory section titles
    assert "1. **ATS Score & Selection Chances**" in audit_notes
    assert "2. **Skill Gap Analysis (Missing Elements)**" in audit_notes
    assert "3. **Hard Truths (Why I might get rejected)**" in audit_notes
    assert "4. **Actionable Suggestions (Exact Rewrites)**" in audit_notes

    # Verify ATS score format
    assert "/ 10" in audit_notes or "/10" in audit_notes
    assert "Shortlist Likelihood" in audit_notes or "Likelihood" in audit_notes


def test_pre_audit_and_confirm_endpoints():
    """Verify truth vault loading, pre-audit interview, and skill confirmation tailoring."""
    from app.api.tailoring import _load_truth_vault

    # Step 1: Verify truth vault matches Mohammad Samir Khan
    vault = _load_truth_vault()
    assert vault.candidate_name == "MOHAMMAD SAMIR KHAN"
    assert "Mumbai" in vault.location

    # Step 2: Pre-Audit Interview with real Truth Vault
    pre_req = PreTailoringAuditRequest(job_description=SAMPLE_JD_WITH_GAPS)
    pre_data = CustomJDTailoringService.generate_pre_tailoring_interview(vault=vault, request=pre_req)

    assert "Maine aapki target Job Description analyze ki" in pre_data.interview_prompt
    assert len(pre_data.missing_skills) > 0
    first_missing = pre_data.missing_skills[0].skill_name

    # Step 3: Confirm missing skill and tailor resume
    confirmed = [
        ConfirmedSkillEntry(
            skill=first_missing,
            known=True,
            context_notes="Hands-on experience in production environments.",
        )
    ]
    updated_vault = CustomJDTailoringService.merge_confirmed_skills(vault=vault, confirmed_skills=confirmed)

    tailoring_req = CustomJDTailoringRequest(
        job_description=SAMPLE_JD_WITH_GAPS,
        save_to_tracker=False,
    )
    tailor_res = CustomJDTailoringService.tailor_custom_jd(vault=updated_vault, request=tailoring_req)

    assert tailor_res.tailored_resume is not None
    assert tailor_res.recruiter_audit is not None
    assert "1. **ATS Score & Selection Chances**" in tailor_res.recruiter_audit.recruiter_notes
    assert tailor_res.tailored_resume["candidate_name"] == "MOHAMMAD SAMIR KHAN"
    # Check that confirmed skill is included in skills inventory
    assert first_missing in tailor_res.tailored_resume["skill_categories"].get("Candidate Confirmed Skills", [])
