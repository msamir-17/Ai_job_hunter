from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator


class NormalizedJob(BaseModel):
    """
    Internal normalized representation of a job posting.
    
    Fields map directly to the PostgreSQL `Job` model schema without modification.
    """

    source: str = Field(..., min_length=1, max_length=50, description="Job source system name")
    external_id: str = Field(..., min_length=1, max_length=255, description="Unique job ID within source")
    title: str = Field(..., min_length=1, max_length=255, description="Normalized job title")
    company: str = Field(..., min_length=1, max_length=255, description="Company name")
    location: str | None = Field(default=None, max_length=255, description="Job location")
    is_remote: bool = Field(default=False, description="Whether the job is remote")
    salary_min: int | None = Field(default=None, ge=0, description="Minimum annual salary")
    salary_max: int | None = Field(default=None, ge=0, description="Maximum annual salary")
    raw_description: str | None = Field(default=None, description="Untrusted raw job description")
    skills_required: list[str] = Field(default_factory=list, description="Extracted required skills")
    url: str | None = Field(default=None, max_length=1024, description="Job application URL")

    @model_validator(mode="before")
    @classmethod
    def trim_strings_and_clean_empty(cls, data: dict) -> dict:
        """Trim leading/trailing whitespace and convert empty/whitespace strings to None."""
        if not isinstance(data, dict):
            return data

        string_fields = ["source", "external_id", "title", "company", "location", "url"]
        for field in string_fields:
            if field in data and isinstance(data[field], str):
                trimmed = data[field].strip()
                if not trimmed and field not in ("source", "external_id", "title", "company"):
                    data[field] = None
                else:
                    data[field] = trimmed

        # Clean and deduplicate skills array
        if "skills_required" in data and isinstance(data["skills_required"], list):
            cleaned_skills = []
            seen_lower = set()
            for s in data["skills_required"]:
                if isinstance(s, str) and s.strip():
                    item = s.strip()
                    item_lower = item.lower()
                    if item_lower not in seen_lower:
                        seen_lower.add(item_lower)
                        cleaned_skills.append(item)
            data["skills_required"] = cleaned_skills

        return data

    @model_validator(mode="after")
    def validate_salary_bounds_and_url(self) -> "NormalizedJob":
        """Enforce salary bound consistency and basic URL validation."""
        # 1. Salary validation: salary_min cannot exceed salary_max
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min > self.salary_max:
                raise ValueError(
                    f"Contradictory salary bounds: salary_min ({self.salary_min}) cannot exceed salary_max ({self.salary_max})."
                )

        # 2. Basic URL validation
        if self.url is not None and self.url.strip():
            url_lower = self.url.lower()
            if not (url_lower.startswith("http://") or url_lower.startswith("https://")):
                raise ValueError(f"Invalid URL format '{self.url}': URL must start with http:// or https://")

        return self


class IngestionRequest(BaseModel):
    """Request schema for triggering job ingestion."""

    source: str = Field(default="manual", description="Source adapter name ('manual' or 'remotive')")
    limit: int | None = Field(default=20, ge=1, le=500, description="Maximum number of jobs to fetch and ingest")
    use_cache: bool = Field(default=False, description="Use local development cache file if available")


class IngestionResult(BaseModel):
    """Result summary statistics for an ingestion run."""

    source: str
    fetched: int = 0
    normalized: int = 0
    inserted: int = 0
    skipped_duplicates: int = 0
    failed: int = 0
    errors: list[str] = Field(default_factory=list)


class JobResponse(BaseModel):
    """Response schema for returning a stored Job entity."""

    id: UUID
    source: str
    external_id: str | None = None
    title: str
    company: str
    location: str | None = None
    is_remote: bool
    salary_min: int | None = None
    salary_max: int | None = None
    raw_description: str | None = Field(default=None, validation_alias="description_raw")
    skills_required: list[str] | None = None
    url: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
