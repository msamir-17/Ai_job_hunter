"""
Pydantic Schemas for Authentication and User Account Management.
"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class UserRegisterRequest(BaseModel):
    """Schema for new candidate account registration."""
    email: str = Field(description="Unique candidate email address")
    password: str = Field(min_length=8, max_length=128, description="Account password (min 8 characters)")
    full_name: str = Field(min_length=2, max_length=128, description="Candidate's full legal name")


class UserLoginRequest(BaseModel):
    """Schema for candidate login."""
    email: str = Field(description="Registered candidate email address")
    password: str = Field(description="Account password")


class UserResponse(BaseModel):
    """Public candidate user identity representation."""
    id: UUID
    email: str
    full_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Authentication response returning signed JWT access token and user metadata."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
