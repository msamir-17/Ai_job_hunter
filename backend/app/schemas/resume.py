from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExperienceItem(BaseModel):
    """Represents a work experience entry extracted from a resume."""

    company: str | None = None
    title: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    achievements: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    """Represents an education entry extracted from a resume."""

    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None


class ResumeDraft(BaseModel):
    """
    Structured unverified draft extracted from raw resume text by AI.

    NOTE: This is an UNVERIFIED DRAFT. It must be reviewed and confirmed by
    the candidate before being merged into the verified CandidateProfile.
    """

    headline: str | None = None
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    target_titles: list[str] = Field(default_factory=list)


class ResumeResponse(BaseModel):
    """Response schema for returning uploaded resume details."""

    id: UUID
    candidate_profile_id: UUID
    file_name: str
    status: str = "extracted"
    raw_text_length: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeExtractResponse(BaseModel):
    """Response schema for returning the extracted unverified resume draft."""

    id: UUID
    candidate_profile_id: UUID
    file_name: str
    status: str = "draft_generated"
    draft: ResumeDraft
