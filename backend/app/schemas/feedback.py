"""
Pydantic Schemas for Candidate Discard Feedback and Preference Logging.
"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    """Payload for submitting job discard feedback."""
    job_id: UUID = Field(..., description="UUID of the discarded job")
    candidate_profile_id: UUID | None = Field(default=None, description="Optional profile ID; defaults to current user profile")
    reason_code: str = Field(..., description="Structured reason code (e.g. wrong_seniority, wrong_location, salary_too_low, tech_stack_mismatch, culture_fit, other)")
    notes: str | None = Field(default=None, description="Optional candidate notes or feedback explanation")
    disliked_skill: str | None = Field(default=None, description="Optional specific technology disliked by candidate (e.g. PHP, Java)")


class FeedbackResponse(BaseModel):
    """Response returned upon logging feedback event."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    candidate_profile_id: UUID
    job_id: UUID
    action: str
    reason_code: str
    notes: str | None = None
    disliked_skill: str | None = None
    created_at: datetime
    vector_updated: bool = False
    message: str = "Feedback recorded successfully"
