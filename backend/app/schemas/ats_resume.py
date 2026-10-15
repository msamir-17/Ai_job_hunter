"""
Schemas for Rendered ATS-Compliant Tailored Resumes and One-Page Budget Audits.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TailoredProjectItem(BaseModel):
    """A project section entry in the tailored ATS resume."""

    project_name: str
    role_or_title: str
    timeline: str
    is_flagship: bool = False
    bullets: List[str] = Field(default_factory=list)
    cited_fact_ids: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class OnePageBudgetAudit(BaseModel):
    """Line and character count audit verifying single-page compliance."""

    total_characters: int
    estimated_total_lines: int
    max_allowed_lines: int = 42
    is_strictly_one_page: bool
    summary_lines: int
    skills_lines: int
    projects_lines: int
    education_lines: int
    audit_notes: str

    model_config = ConfigDict(extra="ignore")


class ATSTailoredResume(BaseModel):
    """Complete, fully assembled tailored resume ready for ATS rendering and PDF export."""

    candidate_name: str
    headline: str
    email: str
    location: str
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    target_job_title: str
    target_company: str
    archetype_id: str
    archetype_display_name: str
    summary: str
    skill_categories: Dict[str, List[str]] = Field(
        description="Ordered dictionary of skill categories matching the archetype lens",
    )
    projects: List[TailoredProjectItem] = Field(
        description="Selected projects with tailored angle-specific bullets",
    )
    education: List[str] = Field(
        description="Education lines (e.g. 'Bachelor of Technology in Computer Science, Mumbai University (Graduated)')",
    )
    budget_audit: OnePageBudgetAudit

    model_config = ConfigDict(extra="ignore")
