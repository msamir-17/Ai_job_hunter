from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class FilterConfig(BaseModel):
    """Configuration settings for deterministic job filtering."""

    max_allowed_experience_gap: float = Field(
        default=2.0,
        ge=0.0,
        le=10.0,
        description="Maximum allowed experience gap in years before hard rejection",
    )
    synonym_mappings: dict[str, list[str]] | None = Field(
        default=None,
        description="Optional title synonym mappings to override defaults",
    )


class FilterJobRequest(BaseModel):
    """Request schema for triggering deterministic filtering."""

    candidate_profile_id: UUID
    limit: int = Field(default=100, ge=1, le=500, description="Maximum jobs to evaluate")
    config: FilterConfig = Field(default_factory=FilterConfig)


class RuleResult(BaseModel):
    """Individual rule evaluation breakdown."""

    rule_name: str
    status: str  # "pass", "review", "reject"
    reason_code: str
    explanation: str


class JobFilterResult(BaseModel):
    """Detailed deterministic filtering outcome for a single job."""

    job_id: UUID
    candidate_profile_id: UUID
    title: str
    company: str
    overall_status: str  # "shortlisted", "review", "rejected"
    passed_deterministic: bool
    rule_results: list[RuleResult]
    summary_explanation: str
    matched_skills: list[str]
    missing_skills: list[str]

    model_config = ConfigDict(from_attributes=True)


class BatchFilterResponse(BaseModel):
    """Batch deterministic filtering summary response."""

    candidate_profile_id: UUID
    total_evaluated: int
    shortlisted_count: int
    review_count: int
    rejected_count: int
    results: list[JobFilterResult]
