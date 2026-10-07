"""
Personalization & Feedback Loop Service.
Implements Rocchio Query Vector Updates and Structured Feedback Event Logging.
Dynamically adjusts candidate search vector based on saved/discarded jobs.
"""
import numpy as np
from typing import Dict, List, Any, Tuple, Optional


class FeedbackReasonCode:
    WRONG_SENIORITY = "wrong_seniority"
    WRONG_LOCATION = "wrong_location"
    SALARY_TOO_LOW = "salary_too_low"
    TECH_STACK_MISMATCH = "tech_stack_mismatch"
    CULTURE_FIT = "culture_fit"
    OTHER = "other"


def rocchio_vector_update(
    profile_vector: List[float],
    saved_vectors: List[List[float]],
    discarded_vectors: List[List[float]],
    alpha: float = 0.8,
    beta: float = 0.2,
    gamma: float = 0.1
) -> List[float]:
    """
    Rocchio Query Update Formula:
    q_new = alpha * q_profile + beta * mean(saved_vectors) - gamma * mean(discarded_vectors)

    Adjusts candidate's vector representation towards saved jobs and away from discarded jobs.
    """
    q_vec = np.array(profile_vector, dtype=float)
    dim = len(q_vec)

    # Saved jobs centroid
    if saved_vectors:
        s_matrix = np.array(saved_vectors, dtype=float)
        mean_saved = np.mean(s_matrix, axis=0)
    else:
        mean_saved = np.zeros(dim)

    # Discarded jobs centroid
    if discarded_vectors:
        d_matrix = np.array(discarded_vectors, dtype=float)
        mean_discarded = np.mean(d_matrix, axis=0)
    else:
        mean_discarded = np.zeros(dim)

    # Apply Rocchio formula
    q_new = (alpha * q_vec) + (beta * mean_saved) - (gamma * mean_discarded)

    # Normalize to unit vector
    norm = np.linalg.norm(q_new)
    if norm > 0:
        q_new = q_new / norm

    return q_new.tolist()


class PersonalizationService:
    """Service for feedback logging and dynamic threshold adaptation."""

    @staticmethod
    def calculate_personalized_match_score(
        base_match_score: float,
        feedback_history: List[Dict[str, Any]],
        job_skills: List[str]
    ) -> float:
        """
        Adjust base match score using candidate feedback history.
        Penalizes jobs matching past discard reasons (e.g. tech stack mismatch).
        """
        score = base_match_score
        if not feedback_history:
            return round(score, 4)

        for event in feedback_history:
            if event.get("action") == "discard":
                reason = event.get("reason_code")
                # Penalty for tech stack mismatch
                if reason == FeedbackReasonCode.TECH_STACK_MISMATCH:
                    discarded_skill = event.get("disliked_skill", "").lower()
                    if discarded_skill and any(discarded_skill in s.lower() for s in job_skills):
                        score -= 0.15 # Apply penalty
                elif reason == FeedbackReasonCode.WRONG_LOCATION:
                    score -= 0.10

        return max(0.0, min(1.0, round(score, 4)))
