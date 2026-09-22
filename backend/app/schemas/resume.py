from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ResumeResponse(BaseModel):
    """Response schema for returning uploaded resume details."""

    id: UUID
    candidate_profile_id: UUID
    file_name: str
    status: str = "extracted"
    raw_text_length: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
