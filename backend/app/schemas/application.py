from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

ApplicationStatus = Literal["saved", "applied", "interviewing", "rejected", "offer"]
DocumentType = Literal["tailored_resume_bullets", "cover_letter", "other"]


class GeneratedDocumentCreate(BaseModel):
    """Schema for attaching a tailored document to an application."""

    doc_type: DocumentType = Field(description="Document type ('tailored_resume_bullets' or 'cover_letter')")
    content: str = Field(..., min_length=1, description="Text content of the tailored document")
    is_approved_by_user: bool = Field(
        default=False,
        description="Candidate approval flag confirming review before document usage",
    )


class GeneratedDocumentUpdate(BaseModel):
    """Schema for updating document content or toggling approval."""

    content: str | None = Field(default=None, min_length=1)
    is_approved_by_user: bool | None = None


class GeneratedDocumentResponse(BaseModel):
    """Schema for returning generated document data."""

    id: UUID
    application_id: UUID
    doc_type: str
    content: str
    is_approved_by_user: bool

    model_config = ConfigDict(from_attributes=True)


class ApplicationCreate(BaseModel):
    """Schema for creating a new job application record."""

    user_id: UUID
    job_match_id: UUID
    status: ApplicationStatus = Field(default="saved", description="Initial application status")
    notes: str | None = Field(default=None, description="Personal candidate notes")
    applied_at: datetime | None = Field(default=None, description="Timestamp when application was submitted")


class ApplicationUpdate(BaseModel):
    """Schema for updating an application's status or notes."""

    status: ApplicationStatus | None = None
    notes: str | None = None
    applied_at: datetime | None = None


class ApplicationResponse(BaseModel):
    """Schema for returning full application details including job info and documents."""

    id: UUID
    user_id: UUID
    job_match_id: UUID
    status: str
    applied_at: datetime | None = None
    notes: str | None = None
    job_id: UUID | None = None
    job_title: str | None = None
    job_company: str | None = None
    job_location: str | None = None
    job_is_remote: bool = False
    job_url: str | None = None
    documents: list[GeneratedDocumentResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
