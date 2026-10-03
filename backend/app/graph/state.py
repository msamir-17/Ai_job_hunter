from typing import Any, TypedDict


class JobHunterState(TypedDict, total=False):
    """
    Central state dictionary passed between nodes in the LangGraph matching workflow.
    """

    # Identifiers
    candidate_profile_id: str
    job_id: str

    # Fetched data snapshots
    candidate_data: dict[str, Any]
    job_data: dict[str, Any]

    # Stage 1: Deterministic Filtering Outputs
    passed_deterministic: bool
    deterministic_status: str  # "shortlisted", "review", "rejected"
    deterministic_summary: str

    # Stage 2: Vector Similarity Outputs
    vector_score: float
    vector_passed: bool

    # Stage 3: LLM Skill Gap Analysis Outputs
    llm_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    missing_required_skills: list[str]
    missing_preferred_skills: list[str]
    analysis_summary: str
    recommendation: str

    # Overall State & Outcome
    overall_status: str  # "shortlisted", "review", "rejected"
    current_stage: str
    error_message: str | None
