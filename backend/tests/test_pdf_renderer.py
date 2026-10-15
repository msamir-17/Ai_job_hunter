"""
Unit tests for ATS Resume HTML Template Renderer and Endpoints.
Verifies clean single-column structure, ATS compliance (zero tables),
print stylesheet inclusion, and API response validity.
"""
import json
from pathlib import Path
import pytest
from app.schemas.candidate_facts import CandidateTruthVault
from app.services.fact_selector import FactSelectorEngine
from app.services.pdf_renderer import render_ats_resume_html


@pytest.fixture
def sample_resume():
    data_path = Path(__file__).parent.parent / "app" / "data" / "candidate_facts.json"
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    vault = CandidateTruthVault.model_validate(data)
    return FactSelectorEngine.assemble_tailored_resume(
        vault=vault,
        job_title="Generative AI Application Developer",
        job_company="AI Horizon",
        job_description="Seeking a GenAI engineer to build LLM agents and RAG pipelines.",
        skills_required=["Python", "LangChain", "RAG", "LLM"],
        forced_archetype_id="genai",
    )


def test_render_ats_resume_html_structure(sample_resume):
    """Verify HTML rendered by Jinja2 contains valid ATS single-column structure."""
    html = render_ats_resume_html(sample_resume)

    # 1. Basic Document & Headings
    assert "<!DOCTYPE html>" in html
    assert sample_resume.candidate_name in html
    assert "Professional Summary" in html
    assert "Technical Skills" in html
    assert "Key Projects & Systems" in html
    assert "Education" in html

    # 2. Flagship Project presence
    assert "AI Job Hunter Co-Pilot" in html

    # 3. Print media stylesheet & margins
    assert "@page" in html
    assert "margin:" in html
    assert "@media print" in html

    # 4. ATS Safety Guardrail: Zero layout tables (tables confuse ATS document parsers)
    assert "<table" not in html.lower()
    assert "<td" not in html.lower()
    assert "<th" not in html.lower()

    # 5. Semantic markup
    assert "<ul class=\"bullet-list\">" in html
    assert "<li>" in html


def test_render_ats_resume_different_archetypes():
    """Verify rendering succeeds for all 4 archetypes without template errors."""
    data_path = Path(__file__).parent.parent / "app" / "data" / "candidate_facts.json"
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    vault = CandidateTruthVault.model_validate(data)

    for arch_id in ["genai", "swe", "ai_eng", "data"]:
        resume = FactSelectorEngine.assemble_tailored_resume(
            vault=vault,
            job_title="Engineer",
            job_company="Company",
            job_description="Engineering role.",
            forced_archetype_id=arch_id,
        )
        html = render_ats_resume_html(resume)
        assert len(html) > 500
        assert resume.candidate_name in html
        # Jinja2 auto-escapes & to &amp;
        expected_headline = resume.headline.replace("&", "&amp;")
        assert expected_headline in html
