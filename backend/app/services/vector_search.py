import logging
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CandidateProfile, Job, JobMatch
from app.schemas.matching import JobVectorMatchResult, VectorSearchRequest
from app.services.embedding import EmbeddingService, format_candidate_profile_text

logger = logging.getLogger(__name__)


class VectorSearchService:
    """
    Stage 2 Vector Similarity Search Service.

    Queries dense 384-dimensional embeddings stored in PostgreSQL using pgvector's
    cosine distance operator (<=>), ranks jobs by semantic similarity to the
    candidate profile embedding, and persists vector scores into JobMatch.
    """

    def __init__(
        self,
        db: AsyncSession,
        embedding_service: EmbeddingService | None = None,
    ):
        self._db = db
        self._embedding_service = embedding_service

    @property
    def embedding_service(self) -> EmbeddingService:
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    async def ensure_candidate_embedding(self, candidate: CandidateProfile) -> list[float]:
        """
        Verify that candidate has an embedding. If missing, generate it from
        verified CandidateProfile data and persist to the database.
        """
        if candidate.embedding is not None and len(candidate.embedding) == 384:
            return candidate.embedding

        text = format_candidate_profile_text(candidate)
        if not text or not text.strip():
            raise ValueError(
                f"CandidateProfile '{candidate.id}' has no verified profile fields (headline, skills, summary, experience) to generate an embedding."
            )

        vector = self.embedding_service.generate_embedding(text)
        candidate.embedding = vector
        self._db.add(candidate)
        await self._db.commit()
        await self._db.refresh(candidate)
        return vector

    async def search_and_persist_matches(
        self,
        request: VectorSearchRequest,
    ) -> list[JobVectorMatchResult]:
        """
        Execute Stage 2 vector similarity search, rank jobs by cosine similarity,
        persist vector_score to JobMatch, and return top semantic matches.
        """
        # 1. Fetch CandidateProfile
        stmt_cand = select(CandidateProfile).where(CandidateProfile.id == request.candidate_profile_id)
        res_cand = await self._db.execute(stmt_cand)
        candidate = res_cand.scalar_one_or_none()
        if not candidate:
            raise ValueError(f"CandidateProfile with ID '{request.candidate_profile_id}' not found.")

        # 2. Ensure candidate embedding exists
        candidate_vector = await self.ensure_candidate_embedding(candidate)

        # 3. Build pgvector cosine distance & similarity expressions
        # Cosine distance ranges from 0 (identical) to 2 (opposite).
        # Cosine similarity = 1.0 - cosine_distance.
        cosine_distance_expr = Job.embedding.cosine_distance(candidate_vector)
        cosine_similarity_expr = (1.0 - cosine_distance_expr)

        # 4. Construct query with conditional Stage 1 deterministic filtering
        if request.only_passed_deterministic:
            stmt = (
                select(Job, JobMatch, cosine_similarity_expr.label("similarity"))
                .join(
                    JobMatch,
                    (JobMatch.job_id == Job.id) & (JobMatch.candidate_profile_id == candidate.id),
                )
                .where(
                    Job.embedding.isnot(None),
                    JobMatch.passed_deterministic.is_(True),
                )
            )
        else:
            stmt = (
                select(Job, JobMatch, cosine_similarity_expr.label("similarity"))
                .outerjoin(
                    JobMatch,
                    (JobMatch.job_id == Job.id) & (JobMatch.candidate_profile_id == candidate.id),
                )
                .where(Job.embedding.isnot(None))
            )

        # 5. Apply minimum similarity threshold if requested
        if request.min_similarity_threshold > 0.0:
            stmt = stmt.where(cosine_similarity_expr >= request.min_similarity_threshold)

        # 6. Order by distance ascending (closest / highest similarity first) and limit
        stmt = stmt.order_by(cosine_distance_expr.asc()).limit(request.limit)

        rows = (await self._db.execute(stmt)).all()

        results: list[JobVectorMatchResult] = []

        # 7. Upsert vector_score into JobMatch and assemble results
        for job, match, raw_similarity in rows:
            similarity = round(float(raw_similarity), 4)

            if match is not None:
                match.vector_score = similarity
            else:
                match = JobMatch(
                    candidate_profile_id=candidate.id,
                    job_id=job.id,
                    passed_deterministic=False,
                    vector_score=similarity,
                    status="review",
                    matched_skills=[],
                    missing_skills=[],
                    analysis_summary=f"Vector similarity: {similarity:.4f} (Stage 1 deterministic not run).",
                )
                self._db.add(match)

            results.append(
                JobVectorMatchResult(
                    job_id=job.id,
                    candidate_profile_id=candidate.id,
                    title=job.title or "",
                    company=job.company or "",
                    location=job.location,
                    is_remote=bool(job.is_remote) if job.is_remote is not None else False,
                    vector_score=similarity,
                    passed_deterministic=bool(match.passed_deterministic),
                    status=match.status,
                    matched_skills=match.matched_skills or [],
                    missing_skills=match.missing_skills or [],
                )
            )

        if results:
            await self._db.commit()

        return results
