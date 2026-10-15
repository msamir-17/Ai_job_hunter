"""
Unit tests for Candidate Truth Vault Schema and Dataset Integrity.
Verifies that candidate_facts.json conforms strictly to CandidateTruthVault,
contains zero empty phrasings, correctly highlights the AI Job Hunter flagship project,
and enforces all senior review requirements (metric names, dates, faithfulness).
"""
import json
from pathlib import Path
import pytest
from app.schemas.candidate_facts import CandidateTruthVault, FactCategory


@pytest.fixture
def truth_vault() -> CandidateTruthVault:
    data_path = Path(__file__).parent.parent / "app" / "data" / "candidate_facts.json"
    assert data_path.exists(), f"candidate_facts.json not found at {data_path}"
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return CandidateTruthVault.model_validate(data)


def test_truth_vault_schema_validation(truth_vault: CandidateTruthVault):
    """Ensure data strictly adheres to CandidateTruthVault schema."""
    assert truth_vault.candidate_name == "Mohd Samir"
    assert len(truth_vault.facts) >= 8
    assert len(truth_vault.education) >= 1
    assert "GenAI & LLMs" in truth_vault.skills_inventory
    assert "Backend & Systems" in truth_vault.skills_inventory


def test_flagship_project_is_ai_job_hunter(truth_vault: CandidateTruthVault):
    """Verify AI Job Hunter is set as the flagship project with multiple facts."""
    flagship_facts = truth_vault.get_flagship_facts()
    assert len(flagship_facts) >= 3, "AI Job Hunter should have at least 3 core facts"
    for fact in flagship_facts:
        assert fact.entity_name == "AI Job Hunter Co-Pilot"
        assert fact.is_flagship is True


def test_all_facts_have_valid_phrasings(truth_vault: CandidateTruthVault):
    """Ensure every fact has non-empty phrasings for relevant angles."""
    for fact in truth_vault.facts:
        assert fact.fact_id, "Fact must have non-empty fact_id"
        assert len(fact.phrasings) >= 1, f"Fact {fact.fact_id} must have at least one phrasing"
        assert "default" in fact.phrasings, f"Fact {fact.fact_id} must have a default phrasing"
        for angle, text in fact.phrasings.items():
            assert len(text.strip()) > 20, f"Phrasing for {fact.fact_id}:{angle} is too short"
            # Verify no leaked phrases
            assert "this role" not in text.lower(), f"Leak detected in {fact.fact_id}:{angle}"
            assert "the role cares" not in text.lower(), f"Leak detected in {fact.fact_id}:{angle}"


def test_metric_consistency_and_naming(truth_vault: CandidateTruthVault):
    """Verify metric naming consistency (e.g. tabular_recall, not accuracy for tables)."""
    mediai_fact = truth_vault.get_fact("mediai_tabular_recall")
    assert mediai_fact is not None
    assert len(mediai_fact.metrics) == 1
    metric = mediai_fact.metrics[0]
    assert metric.metric_name == "tabular_recall"
    assert "accuracy" not in metric.metric_name
    assert metric.baseline == "85%"
    assert metric.achieved == "100%"

    # Verify Faithfulness on 50-case suite
    hunter_verifier = truth_vault.get_fact("job_hunter_fact_verifier")
    assert hunter_verifier is not None
    faithfulness_metric = next(m for m in hunter_verifier.metrics if m.metric_name == "faithfulness")
    assert faithfulness_metric.achieved == "1.0"
    assert "50-case" in faithfulness_metric.context


def test_education_status_graduated(truth_vault: CandidateTruthVault):
    """Verify education date is marked as Graduated (not graduating June 2026)."""
    assert len(truth_vault.education) > 0
    edu = truth_vault.education[0]
    assert edu.end_date == "Graduated"
    assert "Graduated" in edu.phrasings["default"]
    assert "2026" not in edu.end_date


def test_skills_inventory_clean_of_buzzwords(truth_vault: CandidateTruthVault):
    """Verify unproven buzzwords like 'Multi-Agent Concepts' are not present."""
    all_skills = [s.lower() for cat in truth_vault.skills_inventory.values() for s in cat]
    assert "multi-agent concepts" not in all_skills
