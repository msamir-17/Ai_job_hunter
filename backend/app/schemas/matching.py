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


class VectorSearchRequest(BaseModel):
    """Request schema for Stage 2 dense vector similarity search."""

    candidate_profile_id: UUID
    limit: int = Field(default=30, ge=1, le=100, description="Maximum semantic matches to return")
    only_passed_deterministic: bool = Field(
        default=True,
        description="If True, only search jobs that passed Stage 1 deterministic filtering",
    )
    min_similarity_threshold: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity cutoff (0.0 to 1.0)",
    )


class JobVectorMatchResult(BaseModel):
    """Single job match outcome enriched with Stage 2 vector similarity score."""

    job_id: UUID
    candidate_profile_id: UUID
    title: str
    company: str
    location: str | None = None
    is_remote: bool = False
    vector_score: float = Field(..., ge=-1.0, le=1.0, description="Cosine similarity score (higher is closer)")
    passed_deterministic: bool = Field(default=False)
    status: str | None = Field(default=None, description="Current match status ('shortlisted', 'review', etc.)")
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class VectorSearchResponse(BaseModel):
    """Stage 2 vector similarity search summary response."""

    candidate_profile_id: UUID
    total_matches: int
    results: list[JobVectorMatchResult]


class SkillGapAnalysis(BaseModel):
    """Structured LLM output for Stage 3 skill gap and match analysis."""

    llm_score: int = Field(ge=0, le=100, description="Match score from 0 to 100 based on factual alignment")
    matched_skills: list[str] = Field(
        default_factory=list,
        description="Verified candidate skills overlapping with role requirements",
    )
    missing_required_skills: list[str] = Field(
        default_factory=list,
        description="Crucial skills or qualifications required by the job that the candidate verifiably lacks",
    )
    missing_preferred_skills: list[str] = Field(
        default_factory=list,
        description="Nice-to-have or bonus skills mentioned in the job description that the candidate lacks",
    )
    analysis_summary: str = Field(
        description="Concise objective rationale explaining the match score and key skill gaps",
    )
    recommendation: str = Field(
        description="Recommendation category: 'strong_match', 'moderate_match', or 'weak_match'",
    )


class AnalyzeJobMatchRequest(BaseModel):
    """Request schema for evaluating a single candidate-job match with LLM."""

    candidate_profile_id: UUID
    job_id: UUID


class BatchAnalyzeMatchesRequest(BaseModel):
    """Request schema for batch LLM analysis of top vector matches."""

    candidate_profile_id: UUID
    job_ids: list[UUID] | None = Field(
        default=None,
        description="Optional list of specific job IDs to analyze. If None, analyzes top vector-ranked matches.",
    )
    limit: int = Field(default=10, ge=1, le=30, description="Max jobs to analyze with LLM (cost control)")
    min_vector_score: float | None = Field(
        default=0.4,
        ge=-1.0,
        le=1.0,
        description="Minimum vector similarity score required to qualify for LLM analysis",
    )


class JobMatchAnalysisResult(BaseModel):
    """Comprehensive outcome of a candidate-job match after Stage 3 LLM evaluation."""

    job_id: UUID
    candidate_profile_id: UUID
    title: str
    company: str
    location: str | None = None
    is_remote: bool = False
    passed_deterministic: bool
    vector_score: float | None = None
    llm_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    missing_required_skills: list[str]
    missing_preferred_skills: list[str]
    analysis_summary: str
    recommendation: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class BatchAnalyzeMatchesResponse(BaseModel):
    """Batch LLM match analysis summary response."""

    candidate_profile_id: UUID
    total_analyzed: int
    results: list[JobMatchAnalysisResult]


class PipelineRunRequest(BaseModel):
    """Request schema for triggering the LangGraph agent matching pipeline end-to-end."""

    candidate_profile_id: UUID
    job_id: UUID


class PipelineRunResponse(BaseModel):
    """Execution state response from the compiled LangGraph agent workflow."""

    candidate_profile_id: UUID
    job_id: UUID
    passed_deterministic: bool = False
    deterministic_status: str | None = None
    vector_score: float | None = None
    vector_passed: bool | None = None
    llm_score: int | None = None
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    analysis_summary: str | None = None
    recommendation: str | None = None
    overall_status: str
    current_stage: str
    error_message: str | None = None



