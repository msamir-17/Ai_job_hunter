from app.graph.state import JobHunterState


def should_continue_after_load(state: JobHunterState) -> str:
    """Check if data was successfully loaded."""
    if state.get("error_message"):
        return "save_results"
    return "deterministic_filter"


def should_continue_after_deterministic(state: JobHunterState) -> str:
    """
    Evaluate Stage 1 outcome.
    If hard criteria failed, route to disqualification.
    Otherwise, proceed to Stage 2 vector similarity.
    """
    if not state.get("passed_deterministic", False) or state.get("deterministic_status") == "rejected":
        return "disqualify_job"
    return "vector_similarity"


def should_continue_after_vector(state: JobHunterState) -> str:
    """
    Evaluate Stage 2 outcome.
    If vector similarity is below minimum threshold, mark as low match.
    Otherwise, proceed to Stage 3 LLM skill gap analysis.
    """
    if not state.get("vector_passed", False):
        return "mark_low_match"
    return "llm_gap_analysis"
