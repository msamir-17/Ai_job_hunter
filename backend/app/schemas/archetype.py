"""
Schemas for Resume Archetype Lenses and Dynamic Role Configurations.
Defines layout ordering, skill category priority, project budgets, and classification weights.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ArchetypeConfig(BaseModel):
    """
    Configuration specification for a resume archetype lens.
    Controls section layout, skill sorting, and targeted emphasis.
    """

    archetype_id: str = Field(description="Unique identifier: e.g. 'genai', 'swe', 'ai_eng', 'data'")
    display_name: str = Field(description="Human-readable title: e.g. 'Generative AI & LLM Specialist'")
    description: str = Field(description="Short description of the lens focus and target audience")
    section_order: List[str] = Field(
        default=["summary", "skills", "projects", "experience", "education"],
        description="Order in which sections appear in the ATS resume layout",
    )
    skill_category_order: List[str] = Field(
        description="Priority order of skill categories displayed at the top of the resume",
    )
    primary_angle: str = Field(
        description="Preferred phrasing angle from CandidateFact.phrasings ('genai', 'swe', 'ai_eng', 'data')",
    )
    max_projects: int = Field(default=3, description="Maximum number of projects to fit within one-page budget")
    max_bullets_per_flagship: int = Field(default=3, description="Maximum bullets for the flagship project")
    max_bullets_per_standard: int = Field(default=2, description="Maximum bullets for non-flagship projects")
    headline_template: str = Field(description="Professional title headline for candidate header")
    summary_template: str = Field(description="Targeted 2-3 line summary emphasizing role archetype strengths")
    keywords: List[str] = Field(default_factory=list, description="Keywords used for heuristic archetype classification")

    model_config = ConfigDict(extra="ignore")


class ArchetypeClassificationResult(BaseModel):
    """Result of classifying a job description against available archetypes."""

    recommended_archetype_id: str
    confidence_score: float
    archetype_weights: Dict[str, float] = Field(
        description="Continuous weight scores across all archetypes (e.g. {'genai': 0.65, 'swe': 0.35})",
    )
    extracted_keywords: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")
