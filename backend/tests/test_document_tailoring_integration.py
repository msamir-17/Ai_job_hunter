import uuid
from unittest.mock import AsyncMock
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.database import AsyncSessionLocal, engine
from app.llm import BaseLLMProvider, get_llm_provider
from app.main import app
from app.models import CandidateProfile, Job, JobMatch, User
from app.schemas.tailoring import (
    TailoredCoverLetterDraft,
    TailoredResumeBullet,
    TailoredResumeDraft,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def dispose_db_engine():
    yield
    await engine.dispose()


@pytest.mark.anyio
async def test_document_tailoring_and_audit_real_postgres():
    """
    Integration test verifying grounded document tailoring, deterministic
    anti-hallucination verification, and FastAPI REST endpoints against
    real Docker PostgreSQL (port 5435).
    """
    test_user_id = uuid.uuid4()
    test_email = f"tailor_test_{test_user_id.hex[:8]}@example.com"

    candidate_profile_id = None
    job_id = None

    mock_llm_provider = AsyncMock(spec=BaseLLMProvider)

    # Mock response for TailoredResumeDraft
    mock_resume_draft = TailoredResumeDraft(
        target_role="AI Search Engineer",
        company_name="Vector Search Labs",
        bullets=[
            TailoredResumeBullet(
                bullet_point="Engineered scalable PyTorch inference pipelines within FastAPI microservices.",
                relevant_skill="PyTorch",
                source_experience_company="AI Labs",
                grounding_rationale="Derived from ML Intern role at AI Labs.",
            ),
            TailoredResumeBullet(
                bullet_point="Developed Python data preprocessing modules ensuring 100% data integrity.",
                relevant_skill="Python",
                source_experience_company="AI Labs",
                grounding_rationale="Derived from ML Intern role at AI Labs.",
            ),
        ],
    )

    # Mock response for TailoredCoverLetterDraft
    mock_cover_letter = TailoredCoverLetterDraft(
        recipient="Vector Search Labs Hiring Team",
        opening_paragraph="I am excited to apply for the AI Search Engineer position.",
        body_paragraphs=[
            "During my work at AI Labs, I built PyTorch inference pipelines using FastAPI and Python."
        ],
        closing_paragraph="I look forward to discussing my verified experience with your team.",
        full_text=(
            "Dear Hiring Team,\n\nI am excited to apply for the AI Search Engineer role. "
            "At AI Labs, I engineered PyTorch pipelines with Python and FastAPI.\n\nSincerely,\nCandidate"
        ),
        highlighted_skills=["Python", "PyTorch", "FastAPI"],
    )

    # Provider returns resume draft on 1st call, cover letter on 2nd call
    mock_llm_provider.generate_structured.side_effect = [
        mock_resume_draft,
        mock_cover_letter,
    ]

    app.dependency_overrides[get_llm_provider] = lambda: mock_llm_provider
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        try:
            # 1. Setup User, CandidateProfile, Job in real Postgres
            async with AsyncSessionLocal() as db:
                user = User(
                    id=test_user_id,
                    email=test_email,
                    hashed_password="hashed_password",
                    full_name="Tailoring Candidate",
                )
                db.add(user)

                candidate = CandidateProfile(
                    user_id=test_user_id,
                    headline="AI & PyTorch Engineer",
                    skills=["Python", "PyTorch", "FastAPI"],  # Does NOT have Kubernetes or CUDA
                    target_titles=["AI Engineer"],
                    experience=[
                        {
                            "company": "AI Labs",
                            "title": "ML Intern",
                            "description": "Engineered neural models.",
                        }
                    ],
                )
                db.add(candidate)
                await db.commit()
                await db.refresh(candidate)
                candidate_profile_id = candidate.id

                job = Job(
                    source="manual",
                    external_id=f"ext_{uuid.uuid4().hex[:8]}",
                    title="AI Search Engineer",
                    company="Vector Search Labs",
                    description_raw="We need an engineer proficient in Python, PyTorch, and Kubernetes.",
                    is_remote=True,
                    skills_required=["Python", "PyTorch", "Kubernetes"],
                )
                db.add(job)
                await db.commit()
                await db.refresh(job)
                job_id = job.id

            # 2. Test POST /api/v1/tailoring/generate
            resp = await client.post(
                "/api/v1/tailoring/generate",
                json={
                    "candidate_profile_id": str(candidate_profile_id),
                    "job_id": str(job_id),
                },
            )
            assert resp.status_code == 200
            data = resp.json()

            assert data["candidate_profile_id"] == str(candidate_profile_id)
            assert data["job_id"] == str(job_id)
            assert len(data["resume_draft"]["bullets"]) == 2
            assert data["audit_result"]["is_grounded"] is True
            assert len(data["audit_result"]["hallucinated_terms"]) == 0
            assert "python" in data["audit_result"]["verified_terms_used"]
            assert "pytorch" in data["audit_result"]["verified_terms_used"]

            # 3. Test POST /api/v1/tailoring/audit with hallucinated text
            hallucinated_payload = {
                "candidate_profile_id": str(candidate_profile_id),
                "job_id": str(job_id),
                "text_to_audit": "I have 5 years of experience deploying models with Kubernetes clusters.",
            }
            audit_resp = await client.post("/api/v1/tailoring/audit", json=hallucinated_payload)
            assert audit_resp.status_code == 200
            audit_data = audit_resp.json()

            # Kubernetes is in job.skills_required but NOT in candidate profile -> must be flagged!
            assert audit_data["is_grounded"] is False
            assert "kubernetes" in audit_data["hallucinated_terms"]
            assert "Audit FAILED" in audit_data["audit_explanation"]

            # 4. Test POST /api/v1/tailoring/audit with strictly grounded text
            grounded_payload = {
                "candidate_profile_id": str(candidate_profile_id),
                "job_id": str(job_id),
                "text_to_audit": "I built machine learning APIs using Python, PyTorch, and FastAPI.",
            }
            clean_audit_resp = await client.post("/api/v1/tailoring/audit", json=grounded_payload)
            assert clean_audit_resp.status_code == 200
            clean_audit_data = clean_audit_resp.json()

            assert clean_audit_data["is_grounded"] is True
            assert len(clean_audit_data["hallucinated_terms"]) == 0
            assert "python" in clean_audit_data["verified_terms_used"]
            assert "pytorch" in clean_audit_data["verified_terms_used"]

        finally:
            app.dependency_overrides.clear()
            # 5. Cleanup test data from PostgreSQL
            async with AsyncSessionLocal() as db:
                if candidate_profile_id:
                    await db.execute(
                        delete(CandidateProfile).where(CandidateProfile.id == candidate_profile_id)
                    )
                if job_id:
                    await db.execute(delete(Job).where(Job.id == job_id))
                await db.execute(delete(User).where(User.id == test_user_id))
                await db.commit()
