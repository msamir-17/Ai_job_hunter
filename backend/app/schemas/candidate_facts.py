"""
Schemas for Candidate Truth Vault and Multi-Angle Fact Inventory.
Provides structured representation of verified candidate achievements, metrics,
and pre-approved phrasing variations per role angle (genai, ai_eng, swe, data).
"""
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class FactCategory(str, Enum):
    PROJECT = "project"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    SKILL = "skill"
    CERTIFICATION = "certification"


class FactMetric(BaseModel):
    """Structured metric detail associated with a verified candidate fact."""

    metric_name: str = Field(description="Normalized name of metric: e.g. latency, tabular_recall, accuracy, throughput")
    baseline: Optional[str] = Field(default=None, description="Starting baseline value: e.g. ~40s, 85%")
    achieved: str = Field(description="Achieved value: e.g. ~20s, 100%, 1.0, 50%")
    unit: Optional[str] = Field(default=None, description="Unit of measurement: e.g. %, seconds, requests/sec")
    context: Optional[str] = Field(default=None, description="Evaluation context: e.g. 50-case Ragas suite, 100 concurrent users")

    model_config = ConfigDict(extra="ignore")


class CandidateFact(BaseModel):
    """
    A single immutable ground-truth fact about candidate experience, project, or skill.
    Contains pre-approved phrasing variations for different archetype angles.
    """

    fact_id: str = Field(description="Unique deterministic identifier: e.g. job_hunter_verifier, advisor_latency")
    category: FactCategory = Field(description="Category of the fact")
    entity_name: str = Field(description="Name of the project, company, or institution")
    role_or_title: Optional[str] = Field(default=None, description="Role title, project type, or degree")
    start_date: Optional[str] = Field(default=None, description="Start date: e.g. 2024-01 or Jun 2024")
    end_date: Optional[str] = Field(default=None, description="End date: e.g. 2024-06, Graduated, or Present")
    tags: List[str] = Field(default_factory=list, description="Keywords for matching: e.g. ['backend', 'genai', 'latency']")
    metrics: List[FactMetric] = Field(default_factory=list, description="Verified metrics verified in this fact")
    phrasings: Dict[str, str] = Field(
        default_factory=dict,
        description="Pre-approved phrasing variants keyed by angle: 'genai', 'ai_eng', 'swe', 'data', 'default'",
    )
    is_flagship: bool = Field(default=False, description="Whether this entity is a flagship showcase item (top of resume)")

    model_config = ConfigDict(extra="ignore")


class CandidateTruthVault(BaseModel):
    """Master container for candidate profile facts, projects, education, and skills."""

    candidate_name: str
    headline: str
    email: str
    location: str
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    education: List[CandidateFact] = Field(default_factory=list)
    skills_inventory: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Categorized skills inventory: e.g. {'Backend': [...], 'GenAI/LLM': [...]}",
    )
    facts: List[CandidateFact] = Field(default_factory=list)

    def get_fact(self, fact_id: str) -> Optional[CandidateFact]:
        """Lookup fact by its unique fact_id."""
        for f in self.facts:
            if f.fact_id == fact_id:
                return f
        for e in self.education:
            if e.fact_id == fact_id:
                return e
        return None

    def get_flagship_facts(self) -> List[CandidateFact]:
        """Return facts belonging to flagship projects."""
        return [f for f in self.facts if f.is_flagship]

    model_config = ConfigDict(extra="ignore")
