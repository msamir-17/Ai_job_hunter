"""
Tests for Native PDF Generation Service and Endpoints (Phase 6).
Verifies:
1. Valid binary PDF output with %PDF- header.
2. Single-page ATS budget enforcement.
3. Content extraction parity using pypdf.
4. XML / special character escaping safety (&, <, >).
5. API endpoint streaming response and headers.
"""
import io
import uuid
import pypdf
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.ats_resume import ATSTailoredResume, TailoredProjectItem, OnePageBudgetAudit
from app.services.pdf_generator import generate_ats_resume_pdf


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _create_mock_tailored_resume() -> ATSTailoredResume:
    return ATSTailoredResume(
        candidate_name="Mohammad Samir Khan",
        headline="AI/ML Engineer & Systems Developer",
        email="samir.dev@example.com",
        location="Mumbai, India (Open to Remote)",
        github_url="https://github.com/msamir-17",
        linkedin_url="https://linkedin.com/in/msamir-17",
        target_job_title="Senior AI Engineer",
        target_company="Anthropic & Google Tech",
        archetype_id="genai",
        archetype_display_name="Generative AI & LLM Systems",
        summary="Engineered low-latency RAG architectures using FastAPI, PostgreSQL pgvector, and transformer models. Dedicated to zero-hallucination verification pipelines.",
        skill_categories={
            "AI & LLMs": ["PyTorch", "Transformers", "LangChain", "RAG", "Prompt Engineering"],
            "Backend & DB": ["Python", "FastAPI", "PostgreSQL", "pgvector", "SQLAlchemy"],
            "Cloud & DevOps": ["Docker", "Linux", "Git", "CI/CD"],
        },
        projects=[
            TailoredProjectItem(
                project_name="AI Job Hunter Co-Pilot",
                role_or_title="Lead AI Engineer",
                timeline="2024 - Present",
                is_flagship=True,
                bullets=[
                    "Engineered multi-tier retrieval pipeline with BM25 keyword matching and pgvector dense similarity, achieving NDCG@10 of 0.9991.",
                    "Implemented zero-hallucination fact citation audit dropping unverified claims with 100% precision.",
                ],
                cited_fact_ids=["fact_01", "fact_02"],
            ),
            TailoredProjectItem(
                project_name="Clinical Tabular PDF Parser",
                role_or_title="ML Research Engineer",
                timeline="2023 - 2024",
                is_flagship=False,
                bullets=[
                    "Built layout-aware table extraction pipeline increasing extraction recall from 85% to 100% on medical forms.",
                ],
                cited_fact_ids=["fact_03"],
            ),
        ],
        education=[
            "Bachelor of Technology in Computer Science, Mumbai University (2024)",
        ],
        budget_audit=OnePageBudgetAudit(
            total_characters=1850,
            estimated_total_lines=34,
            max_allowed_lines=42,
            is_strictly_one_page=True,
            summary_lines=3,
            skills_lines=4,
            projects_lines=18,
            education_lines=2,
            audit_notes="Budget verified: Strictly 1 page",
        ),
    )


def test_generate_ats_resume_pdf_structure():
    """Verify generated PDF byte stream is a valid, single-page PDF document."""
    resume = _create_mock_tailored_resume()
    pdf_bytes = generate_ats_resume_pdf(resume)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")

    # Parse with pypdf
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 1, f"Expected strictly 1 page, got {len(reader.pages)}"

    # Check text content in the generated PDF
    page_text = reader.pages[0].extract_text()
    assert "MOHAMMAD SAMIR KHAN" in page_text.upper()
    assert "AI/ML Engineer" in page_text
    assert "PyTorch" in page_text
    assert "AI Job Hunter Co-Pilot" in page_text
    assert "Mumbai University" in page_text


def test_generate_ats_resume_pdf_special_characters():
    """Verify special XML characters like &, <, > do not crash the PDF generator."""
    resume = _create_mock_tailored_resume()
    resume.candidate_name = "Samir <Dev> & Co"
    resume.summary = "Built R&D pipelines where throughput > 100 req/s & latency < 50ms."

    pdf_bytes = generate_ats_resume_pdf(resume)
    assert pdf_bytes.startswith(b"%PDF-")

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 1
    page_text = reader.pages[0].extract_text()
    assert "Samir <Dev> & Co".upper() in page_text.upper() or "SAMIR" in page_text.upper()


@pytest.mark.anyio
async def test_convert_ats_resume_json_to_pdf_endpoint():
    """Verify POST /api/v1/tailoring/ats-resume/download-from-data enforces auth and streams valid PDF."""
    from app.api.deps import get_current_user
    from app.models import User

    resume = _create_mock_tailored_resume()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Unauthenticated request must return 401 Unauthorized
        unauth_resp = await client.post(
            "/api/v1/tailoring/ats-resume/download-from-data",
            json=resume.model_dump(),
        )
        assert unauth_resp.status_code == 401

        # 2. Authenticated user successfully generates PDF
        mock_user = User(
            id=uuid.uuid4(),
            email="pdf_user@example.com",
            hashed_password="pw",
            full_name="Mohammad Samir Khan",
        )
        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            response = await client.post(
                "/api/v1/tailoring/ats-resume/download-from-data",
                json=resume.model_dump(),
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            assert "Content-Disposition" in response.headers
            assert "Mohammad_Samir_Khan_ATS_Resume.pdf" in response.headers["Content-Disposition"]

            content = response.content
            assert content.startswith(b"%PDF-")

            reader = pypdf.PdfReader(io.BytesIO(content))
            assert len(reader.pages) == 1
        finally:
            app.dependency_overrides.pop(get_current_user, None)

