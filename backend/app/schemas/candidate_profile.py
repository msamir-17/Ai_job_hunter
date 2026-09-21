from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CandidateProfileBase(BaseModel):
    """Base schema with common candidate profile fields."""

    headline: str | None = Field(default=None, max_length=255)
    summary: str | None = None
    skills: list[Any] | None = None
    experience: list[Any] | None = None
    education: list[Any] | None = None
    target_titles: list[str] | None = None


class CandidateProfileCreate(CandidateProfileBase):
    """Request schema for creating a new candidate profile."""

    user_id: UUID


class CandidateProfileUpdate(CandidateProfileBase):
    """Request schema for updating an existing candidate profile."""

    pass


class CandidateProfileResponse(CandidateProfileBase):
    """Response schema for returning candidate profile data."""

    id: UUID
    user_id: UUID

    model_config = ConfigDict(from_attributes=True)
