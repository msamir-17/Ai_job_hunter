"""
Unit & Integration Test Suite for Custom External JD Tailoring & Recruiter Audit Engine.
Verifies:
1. Smart extraction of Role and Company from raw unformatted JD text.
2. Recruiter & ATS Gap Audit (ATS Score out of 10, Shortlist odds, 3-column gap table, Cliché detection).
3. Grounded 1-page ATS Resume assembly with single-page budget compliance.
4. 4-Line Hiring Manager Cold Outreach generation.
5. End-to-end API endpoint execution with guest & authenticated user support.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.candidate_facts import CandidateFact, CandidateTruthVault, FactCategory
from app.schemas.tailoring import CustomJDTailoringRequest, CustomJDTailoringResponse
from app.services.custom_jd_service import CustomJDTailoringService


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def sample_vault():
    return CandidateTruthVault(
        candidate_name="Mohd Samir Khan",
        headline="AI/ML Engineer & Systems Developer",
        email="samir.dev@example.com",
        location="Mumbai, India",
        skills_inventory={
            "Core Backend": ["Python", "FastAPI", "PostgreSQL", "Docker"],
            "AI & ML": ["PyTorch", "Sentence-Transformers"],
        },
        facts=[
            CandidateFact(
                fact_id="fact_01",
                category=FactCategory.PROJECT,
                entity_name="Cognitive AI Engine",
                tags=["python", "fastapi", "docker", "postgresql"],
                phrasings={"default": "Engineered high-throughput FastAPI service with pgvector search.", "genai": "Architected RAG retrieval pipelines."},
                is_flagship=True,
            )
        ],
    )


SAMPLE_RAW_JD = """
Job Title: Senior Staff AI Platform Engineer
Company: Anthropic AI
Location: San Francisco, CA (Remote Friendly)

About the Role:
We are looking for a Senior Staff AI Platform Engineer to build scalable microservices and high-throughput vector retrieval systems.
You will work with Python, FastAPI, PostgreSQL, and PyTorch. Experience with Kubernetes, Docker, and AWS is required.
We value engineers who take end-to-end ownership and write testable code daily.
"""


def test_smart_extract_job_details():
    title, company, skills = CustomJDTailoringService.smart_extract_job_details(SAMPLE_RAW_JD)

    assert "AI Platform Engineer" in title or "Staff" in title
    assert company == "Anthropic AI"
    assert "Python" in skills
    assert "Fastapi" in skills or "FastAPI" in [s.title() for s in skills]
    assert "Docker" in skills
    assert "Kubernetes" in skills


def test_perform_recruiter_audit(sample_vault):
    skills_required = ["Python", "Fastapi", "Docker", "Kubernetes", "Aws"]
    audit = CustomJDTailoringService.perform_recruiter_audit(
        vault=sample_vault,
        target_title="Senior Staff AI Platform Engineer",
        target_company="Anthropic AI",
        jd_text=SAMPLE_RAW_JD,
        skills_required=skills_required,
        language_tone="hinglish",
    )

    # 1. ATS Score & Shortlist Probability
    assert 5.0 <= audit.ats_score <= 10.0
    assert audit.shortlist_chance in {"High", "Medium", "Low"}

    # 2. 3-Column Gap Table
    assert len(audit.gap_table) > 0
    missing_techs = [g.missing_tech.lower() for g in audit.gap_table]
    assert any("kubernetes" in m for m in missing_techs) or any("aws" in m for m in missing_techs)

    # 3. Recruiter Notes in Hinglish
    assert "ATS Score" in audit.recruiter_notes
    assert "Anthropic AI" in audit.recruiter_notes

    # 4. Actionable Suggestions
    assert len(audit.actionable_suggestions) >= 3


def test_generate_cold_outreach(sample_vault):
    outreach = CustomJDTailoringService.generate_cold_outreach(
        vault=sample_vault,
        target_title="Staff AI Engineer",
        target_company="Anthropic AI",
        jd_text=SAMPLE_RAW_JD,
    )

    assert "Anthropic AI" in outreach.subject
    assert "Staff AI Engineer" in outreach.subject
    # Must be structured as 4 distinct numbered/pointed lines
    lines = [line for line in outreach.body.splitlines() if line.strip().startswith(("1.", "2.", "3.", "4."))]
    assert len(lines) == 4


def test_tailor_custom_jd_end_to_end(sample_vault):
    req = CustomJDTailoringRequest(
        job_description=SAMPLE_RAW_JD,
        archetype_id="genai",
        language_tone="hinglish",
        save_to_tracker=False,
    )

    res = CustomJDTailoringService.tailor_custom_jd(vault=sample_vault, request=req)

    assert isinstance(res, CustomJDTailoringResponse)
    assert res.job_title != ""
    assert res.company_name != ""
    assert "budget_audit" in res.tailored_resume
    # Verify strict 1-page budget check
    assert res.tailored_resume["budget_audit"]["is_strictly_one_page"] is True
    assert res.recruiter_audit.ats_score > 0
    assert len(res.cold_outreach.body) > 50


@pytest.mark.anyio
async def test_custom_jd_api_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "job_description": SAMPLE_RAW_JD,
            "language_tone": "hinglish",
            "save_to_tracker": False,
        }
        res = await client.post("/api/v1/tailoring/custom-jd/tailor", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "tailored_resume" in data
        assert "recruiter_audit" in data
        assert "cold_outreach" in data
        assert data["recruiter_audit"]["ats_score"] > 0
