"""
Unit tests for FactSelectorEngine, One-Page Line Budgeting, and Enhanced FactVerifier.
Verifies bullet re-angling per archetype, flagship project prioritization,
anti-leak guardrail, and metric semantic inflation prevention.
"""
import json
from pathlib import Path
import pytest
from app.models import CandidateProfile
from app.schemas.candidate_facts import CandidateTruthVault
from app.schemas.tailoring import TailoredResumeBullet
from app.services.fact_selector import FactSelectorEngine
from app.services.fact_verifier import FactVerifierService


@pytest.fixture
def truth_vault() -> CandidateTruthVault:
    data_path = Path(__file__).parent.parent / "app" / "data" / "candidate_facts.json"
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return CandidateTruthVault.model_validate(data)


def test_flagship_project_is_top_project(truth_vault: CandidateTruthVault):
    """Verify AI Job Hunter is always the top project across all archetypes."""
    for arch in ["genai", "swe", "ai_eng", "data"]:
        resume = FactSelectorEngine.assemble_tailored_resume(
            vault=truth_vault,
            job_title="Software Engineer",
            job_company="TechCorp",
            job_description="Looking for an engineer to build systems.",
            forced_archetype_id=arch,
        )
        assert len(resume.projects) > 0
        assert resume.projects[0].project_name == "AI Job Hunter Co-Pilot"
        assert resume.projects[0].is_flagship is True


def test_phrasing_reangling_across_archetypes(truth_vault: CandidateTruthVault):
    """Verify the exact same fact produces different angle phrasings for GenAI vs SWE."""
    resume_genai = FactSelectorEngine.assemble_tailored_resume(
        vault=truth_vault,
        job_title="LLM Developer",
        job_company="GenAI Labs",
        job_description="LLM and RAG systems.",
        forced_archetype_id="genai",
    )

    resume_swe = FactSelectorEngine.assemble_tailored_resume(
        vault=truth_vault,
        job_title="Backend Developer",
        job_company="Cloud Corp",
        job_description="Backend distributed systems and PostgreSQL.",
        forced_archetype_id="swe",
    )

    # In GenAI, skill category 0 should be GenAI & LLMs
    genai_categories = list(resume_genai.skill_categories.keys())
    assert genai_categories[0] == "GenAI & LLMs"

    # In SWE, skill category 0 should be Backend & Systems
    swe_categories = list(resume_swe.skill_categories.keys())
    assert swe_categories[0] == "Backend & Systems"


def test_one_page_budget_audit(truth_vault: CandidateTruthVault):
    """Verify resume strictly complies with 1-page line budget (<= 42 lines)."""
    resume = FactSelectorEngine.assemble_tailored_resume(
        vault=truth_vault,
        job_title="Full-Stack AI Engineer",
        job_company="FastScale",
        job_description="Full stack python, react, postgresql, and embeddings.",
    )
    audit = resume.budget_audit
    assert audit.is_strictly_one_page is True
    assert audit.estimated_total_lines <= 42


def test_enhanced_fact_verifier_blocks_leaked_phrases(truth_vault: CandidateTruthVault):
    """Verify FactVerifier blocks leaked JD phrases like 'this role' or 'the role cares about'."""
    candidate = CandidateProfile(
        headline=truth_vault.headline,
        summary=truth_vault.headline,
        skills=["Python", "FastAPI", "PostgreSQL"],
    )
    desc, raw_facts = FactVerifierService.generate_candidate_fact_map(candidate)

    leaked_bullet = TailoredResumeBullet(
        bullet_point="Implemented hybrid search which is a core evaluation dimension this role cares about.",
        relevant_skill="Python",
        cited_fact_ids=["fact_skill_01"],
        grounding_rationale="Cites python skill",
    )

    is_valid, violations = FactVerifierService.verify_bullet_grounding(
        leaked_bullet, candidate, raw_facts
    )
    assert is_valid is False
    assert any("Leaked job description" in v for v in violations)


def test_enhanced_fact_verifier_blocks_metric_semantic_inflation(truth_vault: CandidateTruthVault):
    """Verify FactVerifier blocks asserting accuracy when fact verifies tabular recall."""
    candidate = CandidateProfile(
        headline="NLP Engineer",
        summary="Engineered clinical PDF parser with 100% tabular recall.",
        skills=["Python", "NLP"],
    )
    desc, raw_facts = FactVerifierService.generate_candidate_fact_map(candidate)

    inflated_bullet = TailoredResumeBullet(
        bullet_point="Improved measured accuracy from 85% to 100% on lab report table extraction.",
        relevant_skill="Python",
        cited_fact_ids=["fact_skill_01"],
        grounding_rationale="Cites fact",
    )

    is_valid, violations = FactVerifierService.verify_bullet_grounding(
        inflated_bullet, candidate, raw_facts
    )
    assert is_valid is False
    assert any("Semantic inflation" in v for v in violations)


def test_different_resumes_generated_for_different_jobs(truth_vault: CandidateTruthVault):
    """Verify that different jobs receive uniquely tailored headlines, summaries, and prioritized skills."""
    resume_morningstar = FactSelectorEngine.assemble_tailored_resume(
        vault=truth_vault,
        job_title="Software Engineer (Python)",
        job_company="Morningstar",
        job_description="Seeking a Python Backend Engineer to build robust data pipelines and APIs with PostgreSQL.",
        skills_required=["Python", "FastAPI", "PostgreSQL"],
    )

    resume_anthropic = FactSelectorEngine.assemble_tailored_resume(
        vault=truth_vault,
        job_title="Senior AI Systems Engineer",
        job_company="Anthropic",
        job_description="Looking for an engineer to advance LLM evaluation, RAG pipelines, and agent systems.",
        skills_required=["LangChain", "PyTorch", "Ragas Evaluation"],
    )

    # 1. Headlines must be distinctly tailored
    assert "Morningstar" in resume_morningstar.headline
    assert "Software Engineer (Python)" in resume_morningstar.headline
    assert "Anthropic" in resume_anthropic.headline
    assert "Senior AI Systems Engineer" in resume_anthropic.headline
    assert resume_morningstar.headline != resume_anthropic.headline

    # 2. Summaries must explicitly reference their respective companies and roles
    assert "Morningstar" in resume_morningstar.summary
    assert "Anthropic" in resume_anthropic.summary
    assert resume_morningstar.summary != resume_anthropic.summary

    # 3. Target job metadata must match
    assert resume_morningstar.target_company == "Morningstar"
    assert resume_anthropic.target_company == "Anthropic"


def test_load_truth_vault_from_real_candidate_profile():
    """Verify that _load_truth_vault extracts real candidate experiences, skills, and education from DB."""
    from app.api.tailoring import _load_truth_vault
    from app.models import User

    mock_user = User(full_name="Jane Doe", email="jane@example.com")
    candidate = CandidateProfile(
        headline="Senior AI Systems Architect",
        skills=["Python", "Databricks", "FastAPI", "LangChain"],
        experience=[
            {
                "company": "Enterprise Global",
                "title": "Lead AI Engineer",
                "start_date": "2023",
                "end_date": "Present",
                "technologies": ["Python", "Databricks"],
                "responsibilities": [
                    "Engineered enterprise data processing pipeline reducing latency by 40%.",
                ],
            }
        ],
        education=[
            {
                "institution": "National Institute of Tech",
                "degree": "B.Tech",
                "field_of_study": "Computer Science",
                "end_date": "2022",
            }
        ],
    )
    candidate.user = mock_user

    vault = _load_truth_vault(candidate)

    assert vault.candidate_name == "Jane Doe"
    assert vault.email == "jane@example.com"
    assert vault.headline == "Senior AI Systems Architect"
    assert any(f.entity_name == "Enterprise Global" for f in vault.facts)
    assert any("National Institute" in e.entity_name for e in vault.education)
    assert "Python" in vault.skills_inventory.get("Backend & Systems", []) or "Python" in vault.skills_inventory.get("Core Technical Skills", [])
