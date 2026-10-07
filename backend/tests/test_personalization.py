"""
Unit tests for Personalization Service and Rocchio Query Vector Update.
"""
import numpy as np
import pytest
from app.services.personalization import (
    rocchio_vector_update,
    PersonalizationService,
    FeedbackReasonCode,
)


def test_rocchio_vector_update_shift():
    """Test that Rocchio vector update shifts profile vector towards saved jobs."""
    profile_vector = [1.0, 0.0, 0.0]
    saved_vectors = [[1.0, 1.0, 0.0]] # Shifts towards +Y axis
    discarded_vectors = [[1.0, 0.0, 1.0]] # Shifts away from +Z axis

    updated_vec = rocchio_vector_update(profile_vector, saved_vectors, discarded_vectors)
    
    assert len(updated_vec) == 3
    # Y component should increase due to saved jobs
    assert updated_vec[1] > 0.0
    # Z component should be negative/decreased due to discarded jobs
    assert updated_vec[2] < 0.0
    # Vector magnitude should be normalized to 1.0
    assert np.linalg.norm(updated_vec) == pytest.approx(1.0, rel=1e-3)


def test_personalized_match_score_penalty():
    """Test personalized match score applies penalty for past tech stack mismatch feedback."""
    base_score = 0.85
    feedback_history = [
        {
            "action": "discard",
            "reason_code": FeedbackReasonCode.TECH_STACK_MISMATCH,
            "disliked_skill": "PHP"
        }
    ]

    # Job with PHP should receive penalty
    score_with_php = PersonalizationService.calculate_personalized_match_score(
        base_score, feedback_history, job_skills=["Python", "PHP"]
    )
    assert score_with_php < base_score
    assert score_with_php == pytest.approx(0.70, rel=1e-2)

    # Job without PHP should not receive penalty
    score_without_php = PersonalizationService.calculate_personalized_match_score(
        base_score, feedback_history, job_skills=["Python", "FastAPI"]
    )
    assert score_without_php == base_score
