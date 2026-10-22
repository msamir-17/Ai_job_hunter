"""
Pydantic schemas for the Application Screening Questions Q&A Agent.
Strictly grounded in verified candidate profile facts with anti-hallucination tracking.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ScreeningQARequest(BaseModel):
    question: str = Field(..., description="The screening or application question asked by the employer / ATS.")
    job_id: Optional[str] = Field(None, description="Optional UUID of the job being applied for.")
    job_title: Optional[str] = Field(None, description="Target job title if job_id not provided.")
    company_name: Optional[str] = Field(None, description="Target company name if job_id not provided.")
    job_description: Optional[str] = Field(None, description="Raw job description or custom context.")
    max_length_words: Optional[int] = Field(150, description="Target maximum word count for the generated answer.")


class ScreeningQAResponse(BaseModel):
    question: str = Field(..., description="Original screening question.")
    answer: str = Field(..., description="Tailored response strictly grounded in verified candidate facts.")
    cited_fact_ids: List[str] = Field(default_factory=list, description="List of Fact IDs formally cited.")
    missing_facts: List[str] = Field(default_factory=list, description="Skills or criteria inquired about that are absent from verified candidate facts.")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score reflecting fact grounding coverage.")
    is_grounded: bool = Field(True, description="True if no unverified claims or hallucinations were introduced.")
    rationale: str = Field("", description="Explanation of why this answer was constructed and which facts support it.")
