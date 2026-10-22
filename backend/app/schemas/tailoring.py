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
    audit_status: str = Field(default="PASS", description="Audit status: PASS or FLAGGED")
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


class ATSTailoringRequest(BaseModel):
    """Request schema for generating an ATS tailored resume."""

    candidate_profile_id: UUID
    job_id: UUID
    forced_archetype_id: str | None = Field(
        default=None,
        description="Optional forced archetype lens ('genai', 'swe', 'ai_eng', 'data'). Auto-detected if omitted.",
    )


# -------------------------------------------------------------------------
# Recruiter & ATS Gap Audit + Custom External JD Tailoring Schemas
# -------------------------------------------------------------------------

class RecruiterAuditGapItem(BaseModel):
    missing_tech: str = Field(description="Core technical skill or tool from JD missing or weak in candidate profile")
    missing_action_verbs: str = Field(description="Action verbs and industry keywords recommended to inject")
    recommended_action: str = Field(description="Specific actionable advice to bridge this gap")


class RecruiterAuditResult(BaseModel):
    ats_score: float = Field(ge=0.0, le=10.0, description="Strict ATS match score out of 10")
    shortlist_chance: str = Field(description="'High', 'Medium', or 'Low' shortlist probability")
    gap_table: list[RecruiterAuditGapItem] = Field(default_factory=list, description="Structured 3-column gap finder table")
    hard_truths: list[str] = Field(default_factory=list, description="Brutal honest recruiter feedback on why this resume might be skipped")
    red_flags: list[str] = Field(default_factory=list, description="Detected fresher clichés, missing metrics, or format red flags")
    actionable_suggestions: list[str] = Field(default_factory=list, description="Exact rewrites and keyword modifications to maximize ATS score")
    recruiter_notes: str = Field(default="", description="Brutally honest coaching summary in Hinglish or English")


class ColdOutreachMessage(BaseModel):
    subject: str = Field(description="Email or InMail subject line")
    body: str = Field(description="Punchy, confident 4-line cold outreach to hiring manager")
    target_platform: str = Field(default="LinkedIn", description="'LinkedIn' or 'Email'")


class CustomJDTailoringRequest(BaseModel):
    job_title: str | None = Field(default=None, description="Target job title (auto-extracted from JD if omitted)")
    company_name: str | None = Field(default=None, description="Target company name (auto-extracted if omitted)")
    job_description: str = Field(..., min_length=20, description="Raw pasted job description text or JD link")
    archetype_id: str | None = Field(default=None, description="Optional archetype override ('genai', 'swe', 'ai_eng', 'data'). Auto-detected if omitted.")
    language_tone: str = Field(default="hinglish", description="Recruiter feedback language: 'hinglish' or 'english'")
    save_to_tracker: bool = Field(default=False, description="Whether to persist this custom job into the applications tracker")


class CustomJDTailoringResponse(BaseModel):
    job_title: str
    company_name: str
    tailored_resume: dict = Field(description="Complete ATSTailoredResume structure")
    cover_letter: str | None = None
    recruiter_audit: RecruiterAuditResult
    cold_outreach: ColdOutreachMessage
    job_id: UUID | None = None

