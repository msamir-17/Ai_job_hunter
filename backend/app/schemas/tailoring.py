from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class TailoredResumeBullet(BaseModel):
    """A single resume bullet point tailored specifically for a job description."""

    bullet_point: str = Field(description="Impact-driven bullet point (Action + Context + Result)")
    relevant_skill: str = Field(description="Verified candidate skill highlighted in this bullet")
    source_experience_company: str | None = Field(
        default=None,
        description="Company or project from candidate's verified experience where this occurred",
    )
    grounding_rationale: str = Field(
        description="Explicit explanation of which verified candidate fact this bullet is grounded in",
    )
    cited_fact_ids: list[str] = Field(
        default_factory=list,
        description="Verified Candidate Profile Fact IDs (e.g. ['fact_exp_01', 'fact_skill_02']) supporting this bullet",
    )



class TailoredResumeDraft(BaseModel):
    """Collection of tailored resume bullets for a target job."""

    target_role: str
    company_name: str
    bullets: list[TailoredResumeBullet] = Field(
        default_factory=list,
        description="List of 3-5 tailored bullet points grounded strictly in candidate profile facts",
    )


class TailoredCoverLetterDraft(BaseModel):
    """Structured cover letter tailored to a job posting."""

    recipient: str = Field(default="Hiring Team")
    opening_paragraph: str = Field(description="Hook and statement of interest in the specific company/role")
    body_paragraphs: list[str] = Field(
        default_factory=list,
        description="2-3 paragraphs connecting candidate's verified achievements to role needs",
    )
    closing_paragraph: str = Field(description="Call to action and expression of enthusiasm")
    full_text: str = Field(description="Complete plain-text assembled cover letter")
    highlighted_skills: list[str] = Field(
        default_factory=list,
        description="Verified candidate skills emphasized in the letter",
    )


class AntiHallucinationAuditResult(BaseModel):
    """Deterministic audit report checking generated text against candidate facts."""

    is_grounded: bool = Field(description="True if zero unverified technical skills were hallucinated")
    hallucinated_terms: list[str] = Field(
        default_factory=list,
        description="Technical skills or tools asserted in the text that are NOT in the candidate profile",
    )
    verified_terms_used: list[str] = Field(
        default_factory=list,
        description="Verified candidate profile skills found in the generated text",
    )
    audit_explanation: str = Field(description="Audit summary and compliance confirmation")


class DocumentTailoringRequest(BaseModel):
    """Request schema for generating tailored application materials."""

    candidate_profile_id: UUID
    job_id: UUID


class DocumentAuditRequest(BaseModel):
    """Request schema for auditing arbitrary text against candidate profile facts."""

    candidate_profile_id: UUID
    text_to_audit: str = Field(..., min_length=1, description="Resume text or cover letter to verify")
    job_id: UUID | None = Field(default=None, description="Optional job ID for contextual skill checking")


class DocumentTailoringResponse(BaseModel):
    """Complete tailored application package with anti-hallucination verification."""

    candidate_profile_id: UUID
    job_id: UUID
    resume_draft: TailoredResumeDraft
    cover_letter: TailoredCoverLetterDraft
    audit_result: AntiHallucinationAuditResult
    is_approved_by_user: bool = False

    model_config = ConfigDict(from_attributes=True)
