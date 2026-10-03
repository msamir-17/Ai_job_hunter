import logging
from typing import Any
from uuid import UUID

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.graph.state import JobHunterState
from app.models import CandidateProfile, Job, JobMatch
from app.services.deterministic_filter import DeterministicFilterService
from app.services.llm_matching import LLMMatchingService
from app.services.vector_search import VectorSearchService

logger = logging.getLogger(__name__)


class MatchingWorkflowNodes:
    """
    State machine execution nodes for the JobHunter LangGraph pipeline.
    """

    def __init__(
        self,
        db: AsyncSession,
        filter_service: DeterministicFilterService | None = None,
        vector_service: VectorSearchService | None = None,
        llm_service: LLMMatchingService | None = None,
    ):
        self.db = db
        self.filter_service = filter_service or DeterministicFilterService()
        self.vector_service = vector_service or VectorSearchService(db=db)
        self.llm_service = llm_service or LLMMatchingService(db=db)

    async def load_data(self, state: JobHunterState) -> dict[str, Any]:
        """Node 1: Load candidate profile and job data from PostgreSQL."""
        candidate_id = UUID(state["candidate_profile_id"])
        job_id = UUID(state["job_id"])

        res_cand = await self.db.execute(
            select(CandidateProfile).where(CandidateProfile.id == candidate_id)
        )
        candidate = res_cand.scalar_one_or_none()
        if not candidate:
            return {
                "overall_status": "rejected",
                "error_message": f"CandidateProfile '{candidate_id}' not found.",
                "current_stage": "load_data",
            }

        res_job = await self.db.execute(select(Job).where(Job.id == job_id))
        job = res_job.scalar_one_or_none()
        if not job:
            return {
                "overall_status": "rejected",
                "error_message": f"Job '{job_id}' not found.",
                "current_stage": "load_data",
            }

        return {
            "current_stage": "load_data",
            "error_message": None,
        }

    async def deterministic_filter(self, state: JobHunterState) -> dict[str, Any]:
        """Node 2: Evaluate Stage 1 deterministic rules (experience, role, location)."""
        candidate_id = UUID(state["candidate_profile_id"])
        job_id = UUID(state["job_id"])

        cand = (await self.db.execute(select(CandidateProfile).where(CandidateProfile.id == candidate_id))).scalar_one()
        job = (await self.db.execute(select(Job).where(Job.id == job_id))).scalar_one()

        result = self.filter_service.evaluate_job(candidate=cand, job=job)

        return {
            "passed_deterministic": result.passed_deterministic,
            "deterministic_status": result.overall_status,
            "deterministic_summary": result.summary_explanation,
            "matched_skills": result.matched_skills,
            "missing_skills": result.missing_skills,
            "overall_status": result.overall_status,
            "current_stage": "deterministic_filter",
        }

    async def disqualify_job(self, state: JobHunterState) -> dict[str, Any]:
        """Disqualification branch: Job failed Stage 1 deterministic criteria."""
        return {
            "overall_status": "rejected",
            "analysis_summary": state.get(
                "deterministic_summary", "Disqualified by Stage 1 deterministic filters."
            ),
            "current_stage": "disqualified",
        }

    async def vector_similarity(self, state: JobHunterState) -> dict[str, Any]:
        """Node 3: Compute/verify Stage 2 dense vector cosine similarity."""
        candidate_id = UUID(state["candidate_profile_id"])
        job_id = UUID(state["job_id"])

        cand = (await self.db.execute(select(CandidateProfile).where(CandidateProfile.id == candidate_id))).scalar_one()
        job = (await self.db.execute(select(Job).where(Job.id == job_id))).scalar_one()

        # Ensure candidate vector exists
        cand_vec = await self.vector_service.ensure_candidate_embedding(cand)

        # Ensure job vector exists
        if job.embedding is None or len(job.embedding) != 384:
            from app.services.embedding import format_job_text

            job_text = format_job_text(job)
            if job_text and job_text.strip():
                job.embedding = self.vector_service.embedding_service.generate_embedding(job_text)
                self.db.add(job)
                await self.db.commit()
                await self.db.refresh(job)

        # Compute cosine similarity between unit vectors
        if job.embedding is not None and len(job.embedding) == 384:
            v_cand = np.array(cand_vec, dtype=float)
            v_job = np.array(job.embedding, dtype=float)
            dot_prod = float(np.dot(v_cand, v_job))
            similarity = round(float(np.clip(dot_prod, -1.0, 1.0)), 4)
        else:
            similarity = 0.0

        min_threshold = 0.30
        vector_passed = similarity >= min_threshold

        return {
            "vector_score": similarity,
            "vector_passed": vector_passed,
            "current_stage": "vector_similarity",
        }

    async def mark_low_match(self, state: JobHunterState) -> dict[str, Any]:
        """Disqualification branch: Job similarity below threshold."""
        score = state.get("vector_score", 0.0)
        return {
            "overall_status": "rejected",
            "analysis_summary": f"Disqualified in Stage 2: Vector similarity ({score:.4f}) is below minimum threshold (0.3000).",
            "current_stage": "low_vector_match",
        }

    async def llm_gap_analysis(self, state: JobHunterState) -> dict[str, Any]:
        """Node 4: Evaluate Stage 3 LLM skill gap analysis and scoring."""
        candidate_id = UUID(state["candidate_profile_id"])
        job_id = UUID(state["job_id"])

        cand = (await self.db.execute(select(CandidateProfile).where(CandidateProfile.id == candidate_id))).scalar_one()
        job = (await self.db.execute(select(Job).where(Job.id == job_id))).scalar_one()

        # Temporary in-memory JobMatch object for evaluation
        temp_match = JobMatch(
            candidate_profile_id=cand.id,
            job_id=job.id,
            passed_deterministic=state.get("passed_deterministic", True),
            vector_score=state.get("vector_score"),
            status=state.get("overall_status", "review"),
        )

        res = await self.llm_service.evaluate_match(candidate=cand, job=job, match=temp_match)

        return {
            "llm_score": res.llm_score,
            "matched_skills": res.matched_skills,
            "missing_skills": res.missing_skills,
            "missing_required_skills": res.missing_required_skills,
            "missing_preferred_skills": res.missing_preferred_skills,
            "analysis_summary": res.analysis_summary,
            "recommendation": res.recommendation,
            "overall_status": res.status,
            "current_stage": "llm_gap_analysis",
        }

    async def save_results(self, state: JobHunterState) -> dict[str, Any]:
        """Node 5: Persist final unified match outcome to PostgreSQL JobMatch."""
        candidate_id = UUID(state["candidate_profile_id"])
        job_id = UUID(state["job_id"])

        res_match = await self.db.execute(
            select(JobMatch).where(
                JobMatch.candidate_profile_id == candidate_id,
                JobMatch.job_id == job_id,
            )
        )
        match = res_match.scalar_one_or_none()

        if match is None:
            match = JobMatch(
                candidate_profile_id=candidate_id,
                job_id=job_id,
                passed_deterministic=state.get("passed_deterministic", False),
                vector_score=state.get("vector_score"),
                llm_score=state.get("llm_score"),
                matched_skills=state.get("matched_skills", []),
                missing_skills=state.get("missing_skills", []),
                analysis_summary=state.get("analysis_summary", ""),
                status=state.get("overall_status", "review"),
            )
            self.db.add(match)
        else:
            match.passed_deterministic = state.get("passed_deterministic", False)
            if "vector_score" in state:
                match.vector_score = state["vector_score"]
            if "llm_score" in state:
                match.llm_score = state["llm_score"]
            match.matched_skills = state.get("matched_skills", [])
            match.missing_skills = state.get("missing_skills", [])
            match.analysis_summary = state.get("analysis_summary", "")
            match.status = state.get("overall_status", "review")

        await self.db.commit()
        return {
            "current_stage": "completed",
        }
