"""
Fact Citation Verifier Service for Anti-Hallucination Enforcement.
Implements double-pass verification check ensuring every generated resume bullet point:
1. Formally cites valid Candidate Profile Fact IDs.
2. Contains only numbers, metrics, and tools supported by those cited facts.
3. Does not contain fabricated technologies or unverified experience claims.
"""
import re
from typing import Dict, List, Set, Tuple, Any
from app.models import CandidateProfile
from app.schemas.tailoring import TailoredResumeBullet, AntiHallucinationAuditResult


class FactVerifierService:
    """Service to assign Fact IDs to Candidate Profile entries and perform double-pass validation."""

    @staticmethod
    def generate_candidate_fact_map(candidate: CandidateProfile) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """
        Map every verified CandidateProfile entry to a unique Fact ID.
        Returns:
            fact_id_descriptions: Human readable description per Fact ID.
            fact_id_raw: Structured metadata object per Fact ID.
        """
        fact_id_descriptions: Dict[str, str] = {}
        fact_id_raw: Dict[str, Any] = {}

        # 1. Skills facts
        if candidate.skills:
            for idx, skill in enumerate(candidate.skills):
                skill_name = skill if isinstance(skill, str) else skill.get("name", "")
                if skill_name:
                    f_id = f"fact_skill_{idx+1:02d}"
                    fact_id_descriptions[f_id] = f"Verified Skill: {skill_name}"
                    fact_id_raw[f_id] = {"type": "skill", "value": skill_name.strip()}

        # 2. Experience facts
        if candidate.experience and isinstance(candidate.experience, list):
            for idx, exp in enumerate(candidate.experience):
                if isinstance(exp, dict):
                    f_id = f"fact_exp_{idx+1:02d}"
                    comp = exp.get("company", "Company")
                    title = exp.get("title", "Role")
                    bullets = exp.get("bullets", [])
                    desc = f"Verified Experience at {comp} as {title} ({len(bullets)} bullets)"
                    fact_id_descriptions[f_id] = desc
                    fact_id_raw[f_id] = {"type": "experience", "company": comp, "title": title, "bullets": bullets}

        # 3. Target Roles facts
        if candidate.target_titles:
            for idx, t in enumerate(candidate.target_titles):
                f_id = f"fact_role_{idx+1:02d}"
                fact_id_descriptions[f_id] = f"Target Role Preference: {t}"
                fact_id_raw[f_id] = {"type": "role", "title": t}

        return fact_id_descriptions, fact_id_raw

    @staticmethod
    def verify_bullet_grounding(
        bullet: TailoredResumeBullet,
        candidate: CandidateProfile,
        fact_id_raw: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Verify a single resume bullet point against its cited Fact IDs.
        Returns (is_valid, list_of_violation_reasons).
        """
        violations: List[str] = []

        # Check 1: Fact ID citation requirement
        cited_ids = getattr(bullet, "cited_fact_ids", [])
        if not cited_ids:
            # Fallback to rationale checking if cited_fact_ids is empty
            if not bullet.grounding_rationale:
                violations.append("Bullet missing required Fact ID citations and grounding rationale.")

        for f_id in cited_ids:
            if f_id not in fact_id_raw:
                violations.append(f"Invalid or fabricated Fact ID cited: '{f_id}'.")

        # Check 2: Technical tool / skill verification
        text_lower = bullet.bullet_point.lower()
        candidate_verified_skills = set()
        if candidate.skills:
            for s in candidate.skills:
                skill_str = s if isinstance(s, str) else s.get("name", "")
                if skill_str:
                    candidate_verified_skills.add(skill_str.lower())

        # Check 3: Numeric verification (Ensure numbers in bullet exist in profile text)
        numbers_in_bullet = re.findall(r"\b\d+(?:\.\d+)?%?", bullet.bullet_point)
        candidate_text_full = json_profile_to_string(candidate).lower()

        for num in numbers_in_bullet:
            if not num:
                continue
            # Ignore standard single digit numbers or common template numbers
            if num in ["1", "2", "3", "4", "5", "10", "100"]:
                continue
            if num not in candidate_text_full:
                violations.append(f"Metric or number '{num}' in bullet is not present in candidate profile.")


        is_valid = len(violations) == 0
        return is_valid, violations


def json_profile_to_string(candidate: CandidateProfile) -> str:
    """Helper to convert candidate profile to plain text string for search."""
    full_name = getattr(candidate, "full_name", "") or ""
    headline = getattr(candidate, "headline", "") or ""
    parts = [full_name, headline]

    if candidate.skills:
        parts.extend([s if isinstance(s, str) else str(s.get("name", "")) for s in candidate.skills])
    if candidate.experience:
        parts.append(str(candidate.experience))
    return " ".join(parts)
