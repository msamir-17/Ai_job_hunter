import logging
from typing import Any
from uuid import UUID

from app.config import settings
from app.models import CandidateProfile, Job
from app.schemas.matching import JevJobEvalResult

logger = logging.getLogger(__name__)

try:
    from typesafe_sdk import Choice, Noul, Score, TypeSafeClient
    HAS_TYPESAFE_SDK = True
except ImportError:
    HAS_TYPESAFE_SDK = False


class JevMatchingService:
    """
    Jev System One decision model evaluator for Stage 2.5 fast-pass candidate-job matching.

    Evaluates state in ~70-300ms using typed decisions (Noul, Score, Choice)
    with calibrated statistical confidence scores.
    """

    def __init__(
        self,
        api_key: str | None = None,
        confidence_threshold: float | None = None,
    ):
        self.api_key = api_key or settings.JEV_API_KEY
        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else settings.JEV_CONFIDENCE_THRESHOLD
        )
        self.client: Any = None
        if HAS_TYPESAFE_SDK and self.api_key:
            try:
                self.client = TypeSafeClient(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize TypeSafeClient: {e}. Falling back to heuristic evaluator.")

    def _build_candidate_summary(self, candidate: CandidateProfile) -> str:
        """Construct concise candidate representation for Jev state."""
        skills = ", ".join(candidate.skills or [])
        titles = ", ".join(candidate.target_titles or [])
        exp_count = len(candidate.experience or [])
        return (
            f"Target Roles: {titles or 'AI/ML Engineer'}\n"
            f"Skills: {skills or 'Python, Machine Learning'}\n"
            f"Verified Experience Entries: {exp_count}\n"
            f"Education: {candidate.education or []}"
        )

    def _build_job_summary(self, job: Job) -> str:
        """Construct concise job posting snippet for Jev state."""
        skills = ", ".join(job.skills_required or [])
        desc_snippet = (job.description_raw or "")[:600]
        return (
            f"Title: {job.title}\n"
            f"Company: {job.company}\n"
            f"Location: {job.location} (Remote: {job.is_remote})\n"
            f"Required Skills: {skills}\n"
            f"Description: {desc_snippet}"
        )

    async def evaluate_job_fit(
        self,
        candidate: CandidateProfile,
        job: Job,
        max_experience_years: float = 3.0,
    ) -> JevJobEvalResult:
        """
        Evaluate candidate fit for a job posting using Jev System One model.

        Evaluates:
        1. is_qualified (Noul): Core qualifications check
        2. skill_score (Score 1-5): Skill overlap rating
        3. domain_fit (Choice): 'Direct Fit', 'Adjacent Role', 'Mismatch'
        4. meets_experience_ceiling (Noul): Job requires <= max_experience_years
        """
        candidate_summary = self._build_candidate_summary(candidate)
        job_summary = self._build_job_summary(job)

        state = {
            "candidate_profile": candidate_summary,
            "job_posting": job_summary,
            "experience_ceiling_years": max_experience_years,
        }

        # If live Jev client is available, make the API call
        if self.client:
            try:
                response = await self.client.system_one(
                    state=state,
                    questions={
                        "is_qualified": Noul(instructions="Does this candidate meet the core qualifications for this role?"),
                        "meets_experience_ceiling": Noul(
                            instructions=f"Is this role suitable for a candidate seeking {max_experience_years} years or fewer of required experience (i.e. NOT a senior/lead/staff role requiring more than {max_experience_years} years)?"
                        ),
                        "skill_score": Score(instructions="Rate candidate technical skill overlap on a scale from 1 to 5"),
                        "domain_fit": Choice(options=["Direct Fit", "Adjacent Role", "Mismatch"]),
                    },
                )

                is_qualified_prob = float(response.noul_value("is_qualified"))
                meets_exp_prob = float(response.noul_value("meets_experience_ceiling"))
                skill_score = int(response.score_value("skill_score"))
                domain_fit = str(response.choice_value("domain_fit"))

                is_qualified = is_qualified_prob >= 0.5
                meets_exp = meets_exp_prob >= 0.5
                confidence = round(is_qualified_prob, 3)

                passed_jev = (
                    is_qualified
                    and meets_exp
                    and confidence >= self.confidence_threshold
                    and domain_fit in ("Direct Fit", "Adjacent Role")
                    and skill_score >= 3
                )

                summary = (
                    f"Jev System One Decision: {'PASSED' if passed_jev else 'FILTERED OUT'} | "
                    f"Domain: {domain_fit} | Skill Score: {skill_score}/5 | "
                    f"Confidence: {confidence:.2f} | Meets <= {max_experience_years}yr Cap: {meets_exp}"
                )

                return JevJobEvalResult(
                    job_id=job.id,
                    candidate_profile_id=candidate.id,
                    title=job.title,
                    company=job.company,
                    is_qualified=is_qualified,
                    qualification_confidence=confidence,
                    skill_score=skill_score,
                    domain_fit=domain_fit,
                    meets_experience_ceiling=meets_exp,
                    passed_jev_filter=passed_jev,
                    evaluation_summary=summary,
                )
            except Exception as e:
                logger.warning(f"Error during live Jev API call: {e}. Falling back to heuristic evaluation.")

        # Heuristic / deterministic evaluation fallback
        return self._heuristic_evaluate(candidate, job, max_experience_years)

    def _heuristic_evaluate(
        self,
        candidate: CandidateProfile,
        job: Job,
        max_experience_years: float,
    ) -> JevJobEvalResult:
        """Deterministic heuristic fallback replicating Jev decision outputs."""
        c_skills = {s.lower().strip() for s in (candidate.skills or [])}
        j_skills = [s.lower().strip() for s in (job.skills_required or [])]

        # Skill overlap calculation
        matched = [s for s in j_skills if s in c_skills]
        overlap_ratio = len(matched) / max(len(j_skills), 1)

        # Title alignment
        title_lower = job.title.lower()
        candidate_titles = [t.lower().strip() for t in (candidate.target_titles or [])]
        is_direct_title = any(t in title_lower or title_lower in t for t in candidate_titles)

        # Experience check
        title_is_senior = any(w in title_lower for w in ["senior", "sr.", "lead", "staff", "principal", "director", "head"])
        meets_exp = not (title_is_senior and max_experience_years < 4.0)

        # Domain fit
        if is_direct_title and overlap_ratio >= 0.4:
            domain_fit = "Direct Fit"
        elif is_direct_title or overlap_ratio >= 0.2:
            domain_fit = "Adjacent Role"
        else:
            domain_fit = "Mismatch"

        # Skill Score 1 to 5
        if overlap_ratio >= 0.7:
            skill_score = 5
        elif overlap_ratio >= 0.5:
            skill_score = 4
        elif overlap_ratio >= 0.3:
            skill_score = 3
        elif overlap_ratio >= 0.1:
            skill_score = 2
        else:
            skill_score = 1

        is_qualified = domain_fit in ("Direct Fit", "Adjacent Role") and skill_score >= 3 and meets_exp
        confidence = round(0.50 + (overlap_ratio * 0.40) + (0.10 if is_direct_title else 0.0), 2)
        confidence = min(0.99, max(0.10, confidence))

        passed_jev = is_qualified and meets_exp and confidence >= self.confidence_threshold

        summary = (
            f"Jev System One Evaluation: {'PASSED' if passed_jev else 'FILTERED OUT'} | "
            f"Domain: {domain_fit} | Skill Score: {skill_score}/5 | "
            f"Confidence: {confidence:.2f} | Meets <= {max_experience_years}yr Cap: {meets_exp}"
        )

        return JevJobEvalResult(
            job_id=job.id,
            candidate_profile_id=candidate.id,
            title=job.title,
            company=job.company,
            is_qualified=is_qualified,
            qualification_confidence=confidence,
            skill_score=skill_score,
            domain_fit=domain_fit,
            meets_experience_ceiling=meets_exp,
            passed_jev_filter=passed_jev,
            evaluation_summary=summary,
        )

    async def evaluate_batch(
        self,
        candidate: CandidateProfile,
        jobs: list[Job],
        max_experience_years: float = 3.0,
    ) -> list[JevJobEvalResult]:
        """Evaluate a list of jobs in parallel using Jev System One."""
        results: list[JevJobEvalResult] = []
        for job in jobs:
            res = await self.evaluate_job_fit(
                candidate=candidate,
                job=job,
                max_experience_years=max_experience_years,
            )
            results.append(res)
        return results
