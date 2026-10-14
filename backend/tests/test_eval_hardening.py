"""
Unit tests for Eval Hardening (Phase 5.5).
Verifies:
1. Stratified Train / Test split integrity (zero data leakage).
2. Multi-candidate coverage and Hard Negative trap presence.
3. Anti-Hallucination Verifier Red-Team 100% attack rejection.
4. Empirical threshold calibration functionality.
"""
import pytest
from app.eval.dataset import BENCHMARK_CANDIDATES, EVALUATION_DATASET, get_train_test_split
from app.eval.verifier_red_team import run_verifier_red_team_benchmark
from app.eval.run_benchmark import calibrate_thresholds_on_train


def test_train_test_split_integrity():
    """Verify that Train and Test splits are disjoint and stratify all candidate personas."""
    train_set, test_set = get_train_test_split(random_seed=42)

    assert len(train_set) > 0
    assert len(test_set) > 0

    train_ids = set(j["job_id"] for j in train_set)
    test_ids = set(j["job_id"] for j in test_set)

    # Zero data leakage between splits
    overlap = train_ids.intersection(test_ids)
    assert len(overlap) == 0, f"Data leakage detected! Overlapping jobs: {overlap}"

    # All 6 candidate personas present in both splits
    train_cands = set(j["candidate_id"] for j in train_set)
    test_cands = set(j["candidate_id"] for j in test_set)

    assert len(train_cands) == len(BENCHMARK_CANDIDATES) == 6
    assert len(test_cands) == len(BENCHMARK_CANDIDATES) == 6


def test_hard_negatives_distribution():
    """Verify that hard negatives and challenge traps are present in the dataset."""
    trap_types = set(j.get("trap_type") for j in EVALUATION_DATASET if j.get("trap_type"))

    expected_traps = {"seniority_trap", "domain_divergence", "keyword_stuffer", "geo_trap"}
    for expected in expected_traps:
        assert expected in trap_types, f"Missing expected hard negative trap: '{expected}'"

    # All traps must be labeled with ground_truth_relevance == 0
    for j in EVALUATION_DATASET:
        if j.get("trap_type"):
            assert j["ground_truth_relevance"] == 0


def test_verifier_red_team_full_defense():
    """Verify that FactVerifierService blocks 100% of adversarial attacks with 0 false rejections."""
    results = run_verifier_red_team_benchmark()

    assert results["total_attacks"] >= 5
    assert results["attacks_blocked"] == results["total_attacks"]
    assert results["attack_rejection_rate"] == 1.0
    assert results["control_pass_rate"] == 1.0


def test_empirical_threshold_calibration():
    """Verify that calibration on train split produces data-derived thresholds."""
    train_set, _ = get_train_test_split(random_seed=42)
    calibration = calibrate_thresholds_on_train(train_set)

    assert "best_retrieval_threshold" in calibration
    assert 0.15 <= calibration["best_retrieval_threshold"] <= 0.45
    assert "calibrated_alert_threshold" in calibration
    assert 0.70 <= calibration["calibrated_alert_threshold"] <= 0.90
