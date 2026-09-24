import datetime
import json
import re
import uuid
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CandidateProfile, Job, JobMatch
from app.schemas.matching import FilterConfig, JobFilterResult, RuleResult

# Default title synonym clusters
DEFAULT_SYNONYM_MAPPINGS: dict[str, list[str]] = {
    "machine learning engineer": [
        "ml engineer",
        "ai engineer",
        "ai/ml engineer",
        "data scientist",
        "applied scientist",
        "ml developer",
        "ai developer",
    ],
    "ai engineer": [
        "machine learning engineer",
        "ml engineer",
        "ai/ml engineer",
        "ai developer",
        "applied ai engineer",
        "generative ai engineer",
    ],
    "software engineer": [
        "software developer",
        "backend engineer",
        "backend developer",
        "python engineer",
        "python developer",
        "full stack engineer",
        "swe",
    ],
    "backend engineer": [
        "backend developer",
        "software engineer",
        "python developer",
        "python engineer",
        "api developer",
    ],
}

# False positive patterns that must NOT be mistaken for required experience
FALSE_POSITIVE_PATTERNS = [
    r"\b\d+\s*days?\s*a\s*week\b",
    r"\b\d+\s*hours?\b",
    r"\$\s*\d+",
    r"\b\d+k\b",
    r"\bversion\s*\d+",
    r"\bpython\s*\d+",
    r"\btop\s*\d+\b",
    r"\b24/7\b",
    r"\b\d+\s*years?\s*ago\b",
]

# Anchored regex patterns for required experience
ANCHORED_EXP_PATTERNS = [
    r"(?i)(?:requires?|requiring|minimum|min|at\s+least)?\s*(\d+)\+?\s*(?:-\s*(\d+))?\s*(?:years?|yrs?)(?:\s*(?:of\s*)?(?:hands-on\s*|relevant\s*|work\s*|industry\s*|professional\s*)?(?:experience|exp)?)?",
    r"(?i)(?:experience|exp)\s*:\s*(\d+)\+?\s*(?:\s*-\s*(\d+))?\s*(?:years?|yrs?)",
]


def parse_date(date_str: Any) -> datetime.date | None:
    """Parse YYYY-MM-DD, YYYY-MM, or YYYY string into a datetime.date object."""
    if not date_str or not isinstance(date_str, str):
        return None
    cleaned = date_str.strip()
    if not cleaned:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            dt = datetime.datetime.strptime(cleaned, fmt)
            return dt.date()
        except ValueError:
            continue
    return None


def calculate_candidate_experience_years(experience_entries: list[dict[str, Any]] | None) -> float:
    """
    Calculate total non-overlapping verified candidate experience in years.

    End-Date Validation Rules:
    1. Ongoing Roles: If end_date is None, empty (""), or explicitly ongoing ("Present", "Current", "Now"), evaluate end_date as today's date.
    2. Invalid Non-Empty End-Dates: If end_date is a non-empty string that fails date parsing (e.g. "InvalidDate"), SKIP the experience entry entirely. Do NOT substitute today's date.
    3. Invalid Date Range (start_date > end_date): SKIP the experience entry entirely.
    4. Internships: Counted by actual calendar duration if dates are valid.
    5. Freshers / empty experience: 0.0 years.
    """
    if not experience_entries:
        return 0.0

    today = datetime.date.today()
    intervals: list[tuple[datetime.date, datetime.date]] = []

    for entry in experience_entries:
        if not isinstance(entry, dict):
            continue
        start = parse_date(entry.get("start_date"))
        if not start:
            continue

        end_raw = entry.get("end_date")
        if end_raw is None or str(end_raw).strip() == "" or str(end_raw).strip().lower() in ("present", "current", "now"):
            end = today
        else:
            end = parse_date(str(end_raw))
            if not end:
                # Invalid non-empty end date -> SKIP interval entirely. Do NOT fall back to today's date.
                continue

        if start > end:
            # Invalid date range -> SKIP interval entirely.
            continue

        intervals.append((start, end))

    if not intervals:
        return 0.0

    # Sort intervals by start date ascending
    intervals.sort(key=lambda x: x[0])

    # Merge overlapping or contiguous intervals
    merged: list[tuple[datetime.date, datetime.date]] = [intervals[0]]
    for current in intervals[1:]:
        prev_start, prev_end = merged[-1]
        curr_start, curr_end = current
        if curr_start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, curr_end))
        else:
            merged.append(current)

    total_days = sum((end - start).days for start, end in merged)
    return round(total_days / 365.25, 2)


def extract_job_required_experience(title: str, description_raw: str | None) -> float | None:
    """
    Extract minimum required experience in years from job title and description.

    Conflict-Resolution & Precedence Hierarchy:
    1. EXPLICIT NUMERIC IN TITLE: Search title for explicit numeric experience (e.g. "2+ years").
    2. EXPLICIT NUMERIC IN DESCRIPTION: Search description_raw for explicit numeric experience.
       (Explicit numeric values ALWAYS override seniority keyword defaults).
    3. SENIORITY KEYWORDS IN TITLE: Only if NO explicit numeric requirement was found anywhere in title or description:
       - "Senior", "Sr.", "Lead", "Staff", "Principal", "Architect", "Director" -> 5.0 years default.
       - "Junior", "Jr.", "Entry Level", "Associate", "Intern", "Fresher" -> 0.0 years default.
    4. UNSTATED / AMBIGUOUS: Return None (triggers REVIEW status with reason EXP_REQUIREMENT_UNSPECIFIED).
    """
    # Step 1: Search title for explicit numeric patterns
    for pattern in ANCHORED_EXP_PATTERNS:
        match = re.search(pattern, title)
        if match:
            return float(match.group(1))

    # Step 2: Search description_raw for explicit numeric patterns (with false-positive suppression)
    if description_raw:
        for pattern in ANCHORED_EXP_PATTERNS:
            for match in re.finditer(pattern, description_raw):
                match_str = match.group(0)
                if any(re.search(fp, match_str, re.IGNORECASE) for fp in FALSE_POSITIVE_PATTERNS):
                    continue
                return float(match.group(1))

    # Step 3: Fall back to seniority keywords ONLY if no explicit numbers were found anywhere in title or description
    title_lower = title.lower()
    if any(kw in title_lower for kw in ["fresher", "intern", "graduate", "entry level", "junior", "jr."]):
        return 0.0

    if any(kw in title_lower for kw in ["senior", "sr.", "lead", "staff", "principal", "architect", "director"]):
        return 5.0

    # Step 4: Ambiguous / Unstated
    return None


def normalize_title(title: str) -> str:
    """Normalize title by lowercasing, stripping special chars, and expanding abbreviations."""
    cleaned = title.lower().strip()
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    tokens = cleaned.split()

    normalized_tokens = []
    for t in tokens:
        if t == "ml":
            normalized_tokens.append("machine learning")
        elif t == "swe":
            normalized_tokens.append("software engineer")
        elif t == "dev":
            normalized_tokens.append("developer")
        else:
            normalized_tokens.append(t)

    return " ".join(normalized_tokens)


class DeterministicFilterService:
    """Deterministic filtering service comparing verified CandidateProfile with ingested Jobs."""

    def __init__(self, config: FilterConfig | None = None):
        self.config = config or FilterConfig()
        self.synonyms = {**DEFAULT_SYNONYM_MAPPINGS, **(self.config.synonym_mappings or {})}

    def evaluate_experience(
        self,
        candidate_exp: float,
        job_min_exp: float | None,
    ) -> RuleResult:
        """Evaluate experience gap rule."""
        if job_min_exp is None:
            return RuleResult(
                rule_name="Experience",
                status="review",
                reason_code="EXP_REQUIREMENT_UNSPECIFIED",
                explanation="Job description does not specify required experience.",
            )

        gap = max(0.0, job_min_exp - candidate_exp)
        max_gap = self.config.max_allowed_experience_gap

        if gap <= 1.0:
            reason = "EXP_MATCH_EXACT" if gap == 0.0 else "EXP_GAP_ACCEPTABLE"
            return RuleResult(
                rule_name="Experience",
                status="pass",
                reason_code=reason,
                explanation=f"Candidate exp ({candidate_exp:.1f} yrs) meets/within 1 yr of required exp ({job_min_exp:.1f} yrs).",
            )
        elif gap <= max_gap:
            return RuleResult(
                rule_name="Experience",
                status="review",
                reason_code="EXP_GAP_ACCEPTABLE",
                explanation=f"Candidate exp ({candidate_exp:.1f} yrs) vs required exp ({job_min_exp:.1f} yrs) gap is {gap:.1f} yrs (<= {max_gap:.1f} yrs max gap). Recommended for candidate review.",
            )
        else:
            return RuleResult(
                rule_name="Experience",
                status="reject",
                reason_code="EXP_GAP_TOO_LARGE",
                explanation=f"Candidate exp ({candidate_exp:.1f} yrs) vs required exp ({job_min_exp:.1f} yrs) gap is {gap:.1f} yrs, exceeding max gap threshold ({max_gap:.1f} yrs).",
            )

    def evaluate_role(
        self,
        target_titles: list[str] | None,
        job_title: str,
    ) -> RuleResult:
        """Evaluate role title normalization and synonym matching."""
        if not target_titles:
            return RuleResult(
                rule_name="RoleTitle",
                status="review",
                reason_code="ROLE_AMBIGUOUS",
                explanation="Candidate has no preferred target titles defined.",
            )

        norm_job_title = normalize_title(job_title)

        # 1. Exact match or synonym match check
        for target in target_titles:
            raw_target_lower = target.lower().strip()
            norm_target = normalize_title(target)

            if norm_target in norm_job_title or norm_job_title in norm_target:
                return RuleResult(
                    rule_name="RoleTitle",
                    status="pass",
                    reason_code="ROLE_EXACT_OR_SYNONYM",
                    explanation=f"Job title '{job_title}' matches candidate target title '{target}'.",
                )

            # Check synonym clusters
            cluster = self.synonyms.get(raw_target_lower, []) or self.synonyms.get(norm_target, [])
            for syn in cluster:
                norm_syn = normalize_title(syn)
                if norm_syn in norm_job_title or norm_job_title in norm_syn:
                    return RuleResult(
                        rule_name="RoleTitle",
                        status="pass",
                        reason_code="ROLE_EXACT_OR_SYNONYM",
                        explanation=f"Job title '{job_title}' matches synonym '{syn}' for target title '{target}'.",
                    )

        # 2. Check partial word overlap
        job_words = set(norm_job_title.split())
        for target in target_titles:
            target_words = set(normalize_title(target).split())
            if job_words.intersection(target_words):
                return RuleResult(
                    rule_name="RoleTitle",
                    status="review",
                    reason_code="ROLE_PARTIAL_MATCH",
                    explanation=f"Job title '{job_title}' partially overlaps with target title '{target}'.",
                )

        # 3. Mismatch
        return RuleResult(
            rule_name="RoleTitle",
            status="reject",
            reason_code="ROLE_MISMATCH",
            explanation=f"Job title '{job_title}' does not match candidate target titles ({target_titles}).",
        )

    def evaluate_location(self, job: Job) -> RuleResult:
        """Evaluate location and work mode filter."""
        if job.is_remote:
            return RuleResult(
                rule_name="Location",
                status="pass",
                reason_code="LOCATION_MATCH",
                explanation="Job offers remote work.",
            )

        if not job.location:
            return RuleResult(
                rule_name="Location",
                status="review",
                reason_code="LOCATION_UNSPECIFIED",
                explanation="Job location or remote work mode is unspecified.",
            )

        return RuleResult(
            rule_name="Location",
            status="pass",
            reason_code="LOCATION_MATCH",
            explanation=f"Job is located at '{job.location}'.",
        )

    def calculate_skill_overlap(
        self,
        candidate_skills: list[str] | None,
        job_skills: list[str] | None,
    ) -> tuple[list[str], list[str]]:
        """Calculate matched and missing skills lists."""
        c_set = {s.strip().lower(): s for s in (candidate_skills or []) if isinstance(s, str) and s.strip()}
        j_list = [s.strip() for s in (job_skills or []) if isinstance(s, str) and s.strip()]

        matched = []
        missing = []

        for req_skill in j_list:
            if req_skill.lower() in c_set:
                matched.append(req_skill)
            else:
                missing.append(req_skill)

        return matched, missing

    def evaluate_job(
        self,
        candidate: CandidateProfile,
        job: Job,
    ) -> JobFilterResult:
        """Evaluate all deterministic rules for a single job against candidate profile."""
        candidate_exp = calculate_candidate_experience_years(candidate.experience)
        job_min_exp = extract_job_required_experience(job.title, job.description_raw)

        rule_results: list[RuleResult] = []

        # Rule 1: Experience
        exp_rule = self.evaluate_experience(candidate_exp, job_min_exp)
        rule_results.append(exp_rule)

        # Rule 2: Role Title
        role_rule = self.evaluate_role(candidate.target_titles, job.title)
        rule_results.append(role_rule)

        # Rule 3: Location
        loc_rule = self.evaluate_location(job)
        rule_results.append(loc_rule)

        # Final Precedence Calculation
        rule_statuses = [r.status for r in rule_results]

        if "reject" in rule_statuses:
            overall_status = "rejected"
            passed_deterministic = False
        elif "review" in rule_statuses:
            overall_status = "review"
            passed_deterministic = True
        else:
            overall_status = "shortlisted"
            passed_deterministic = True

        # Skills overlap
        matched_skills, missing_skills = self.calculate_skill_overlap(candidate.skills, job.skills_required)

        # Format human-readable summary explanation
        summary_lines = [
            f"Deterministic Outcome: {overall_status.upper()} (Passed Deterministic Gate: {passed_deterministic})",
            f"- Experience Rule: [{exp_rule.status.upper()}] {exp_rule.explanation}",
            f"- Role Rule: [{role_rule.status.upper()}] {role_rule.explanation}",
            f"- Location Rule: [{loc_rule.status.upper()}] {loc_rule.explanation}",
        ]
        if job.salary_min or job.salary_max:
            s_min = f"${job.salary_min:,}" if job.salary_min else "Unspecified"
            s_max = f"${job.salary_max:,}" if job.salary_max else "Unspecified"
            summary_lines.append(f"- Informational Salary: {s_min} - {s_max}")
        else:
            summary_lines.append("- Informational Salary: Unspecified")

        summary_explanation = "\n".join(summary_lines)

        job_id = job.id or uuid.uuid4()
        candidate_profile_id = candidate.id or uuid.uuid4()
        company = job.company or "Unspecified Company"
        title = job.title or "Unspecified Title"

        return JobFilterResult(
            job_id=job_id,
            candidate_profile_id=candidate_profile_id,
            title=title,
            company=company,
            overall_status=overall_status,
            passed_deterministic=passed_deterministic,
            rule_results=rule_results,
            summary_explanation=summary_explanation,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
        )

    async def filter_and_persist_jobs(
        self,
        db: AsyncSession,
        candidate_profile_id: UUID,
        limit: int = 100,
    ) -> list[JobFilterResult]:
        """Fetch candidate and jobs, evaluate rules, and upsert JobMatch records into database."""
        # 1. Fetch CandidateProfile
        stmt_candidate = select(CandidateProfile).where(CandidateProfile.id == candidate_profile_id)
        res_candidate = await db.execute(stmt_candidate)
        candidate = res_candidate.scalar_one_or_none()
        if not candidate:
            raise ValueError(f"CandidateProfile with ID {candidate_profile_id} not found.")

        # 2. Fetch Jobs
        stmt_jobs = select(Job).limit(limit)
        res_jobs = await db.execute(stmt_jobs)
        jobs = list(res_jobs.scalars().all())

        results: list[JobFilterResult] = []

        for job in jobs:
            res = self.evaluate_job(candidate, job)
            results.append(res)

            # Upsert into JobMatch table
            stmt_match = select(JobMatch).where(
                JobMatch.candidate_profile_id == candidate.id,
                JobMatch.job_id == job.id,
            )
            res_match = await db.execute(stmt_match)
            existing_match = res_match.scalar_one_or_none()

            if existing_match:
                existing_match.passed_deterministic = res.passed_deterministic
                existing_match.status = res.overall_status
                existing_match.matched_skills = res.matched_skills
                existing_match.missing_skills = res.missing_skills
                existing_match.analysis_summary = res.summary_explanation
            else:
                new_match = JobMatch(
                    candidate_profile_id=candidate.id,
                    job_id=job.id,
                    passed_deterministic=res.passed_deterministic,
                    status=res.overall_status,
                    matched_skills=res.matched_skills,
                    missing_skills=res.missing_skills,
                    analysis_summary=res.summary_explanation,
                )
                db.add(new_match)

        await db.commit()
        return results
