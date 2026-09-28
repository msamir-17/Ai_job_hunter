import logging
import math
from typing import Sequence
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CandidateProfile, Job
from app.services.embedding import EmbeddingService

logger = logging.getLogger(__name__)


class EmbeddingPersistenceResult(BaseModel):
    """Execution summary statistics for embedding generation and persistence."""

    jobs_processed: int = 0
    jobs_updated: int = 0
    jobs_failed: int = 0
    jobs_skipped: int = 0
    profiles_processed: int = 0
    profiles_updated: int = 0
    profiles_failed: int = 0
    profiles_skipped: int = 0
    errors: list[str] = Field(default_factory=list)


class EmbeddingPersistenceService:
    """
    Service responsible for finding jobs and candidate profiles with missing vector embeddings,
    generating 384-dimensional dense vectors via EmbeddingService, and persisting them to PostgreSQL.
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
        """Lazily access or create the EmbeddingService instance."""
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    async def get_jobs_needing_embeddings(
        self,
        job_ids: list[UUID] | None = None,
        force_regenerate: bool = False,
        limit: int | None = None,
    ) -> Sequence[Job]:
        """Fetch Job records requiring vector embedding generation."""
        stmt = select(Job)
        if job_ids:
            stmt = stmt.where(Job.id.in_(job_ids))
        elif not force_regenerate:
            stmt = stmt.where(Job.embedding.is_(None))

        if limit is not None and limit > 0:
            stmt = stmt.limit(limit)

        res = await self._db.execute(stmt)
        return res.scalars().all()

    async def get_candidate_profiles_needing_embeddings(
        self,
        profile_ids: list[UUID] | None = None,
        force_regenerate: bool = False,
        limit: int | None = None,
    ) -> Sequence[CandidateProfile]:
        """Fetch CandidateProfile records requiring vector embedding generation."""
        stmt = select(CandidateProfile)
        if profile_ids:
            stmt = stmt.where(CandidateProfile.id.in_(profile_ids))
        elif not force_regenerate:
            stmt = stmt.where(CandidateProfile.embedding.is_(None))

        if limit is not None and limit > 0:
            stmt = stmt.limit(limit)

        res = await self._db.execute(stmt)
        return res.scalars().all()

    async def generate_and_persist_job_embeddings(
        self,
        job_ids: list[UUID] | None = None,
        force_regenerate: bool = False,
        batch_size: int = 100,
    ) -> EmbeddingPersistenceResult:
        """Generate and persist embeddings for Job records."""
        result = EmbeddingPersistenceResult()
        jobs = await self.get_jobs_needing_embeddings(
            job_ids=job_ids, force_regenerate=force_regenerate
        )

        if not jobs:
            return result

        result.jobs_processed = len(jobs)

        for job in jobs:
            try:
                vector = self.embedding_service.generate_job_embedding(job)

                if (
                    not isinstance(vector, list)
                    or len(vector) != self.embedding_service.expected_dimension
                    or not all(math.isfinite(x) for x in vector)
                ):
                    raise RuntimeError(
                        f"Generated vector dimension mismatch or non-finite values for job {job.id}"
                    )

                async with self._db.begin_nested():
                    job.embedding = vector
                    await self._db.flush()

                result.jobs_updated += 1
            except Exception as err:
                async with self._db.begin_nested():
                    job.embedding = None
                    await self._db.flush()

                result.jobs_failed += 1
                result.errors.append(f"Job {job.id} embedding failed: {str(err)}")

        await self._db.commit()
        return result

    async def generate_and_persist_candidate_embeddings(
        self,
        profile_ids: list[UUID] | None = None,
        force_regenerate: bool = False,
        batch_size: int = 100,
    ) -> EmbeddingPersistenceResult:
        """Generate and persist embeddings for CandidateProfile records."""
        result = EmbeddingPersistenceResult()
        profiles = await self.get_candidate_profiles_needing_embeddings(
            profile_ids=profile_ids, force_regenerate=force_regenerate
        )

        if not profiles:
            return result

        result.profiles_processed = len(profiles)

        for profile in profiles:
            try:
                vector = self.embedding_service.generate_candidate_embedding(profile)

                if (
                    not isinstance(vector, list)
                    or len(vector) != self.embedding_service.expected_dimension
                    or not all(math.isfinite(x) for x in vector)
                ):
                    raise RuntimeError(
                        f"Generated vector dimension mismatch or non-finite values for profile {profile.id}"
                    )

                async with self._db.begin_nested():
                    profile.embedding = vector
                    await self._db.flush()

                result.profiles_updated += 1
            except Exception as err:
                async with self._db.begin_nested():
                    profile.embedding = None
                    await self._db.flush()

                result.profiles_failed += 1
                result.errors.append(
                    f"CandidateProfile {profile.id} embedding failed: {str(err)}"
                )

        await self._db.commit()
        return result

    async def backfill_embeddings(
        self,
        batch_size: int = 100,
        force_regenerate: bool = False,
        process_jobs: bool = True,
        process_profiles: bool = True,
    ) -> EmbeddingPersistenceResult:
        """
        Backfill missing embeddings for existing Jobs and CandidateProfiles in batch.

        LAZY MODEL LOADING GUARD:
        Queries database first. If 0 jobs and 0 candidate profiles need processing,
        returns immediately without referencing self.embedding_service or triggering
        SentenceTransformer model loading.
        """
        overall_result = EmbeddingPersistenceResult()

        jobs_to_process = (
            await self.get_jobs_needing_embeddings(force_regenerate=force_regenerate)
            if process_jobs
            else []
        )
        profiles_to_process = (
            await self.get_candidate_profiles_needing_embeddings(
                force_regenerate=force_regenerate
            )
            if process_profiles
            else []
        )

        # Early exit: Avoid loading embedding model if no records need embeddings
        if not jobs_to_process and not profiles_to_process:
            return overall_result

        # Process Jobs if any
        if jobs_to_process:
            overall_result.jobs_processed = len(jobs_to_process)
            for job in jobs_to_process:
                try:
                    vector = self.embedding_service.generate_job_embedding(job)
                    if (
                        not isinstance(vector, list)
                        or len(vector) != self.embedding_service.expected_dimension
                        or not all(math.isfinite(x) for x in vector)
                    ):
                        raise RuntimeError(
                            f"Generated vector dimension mismatch or non-finite values for job {job.id}"
                        )
                    async with self._db.begin_nested():
                        job.embedding = vector
                        await self._db.flush()
                    overall_result.jobs_updated += 1
                except Exception as err:
                    async with self._db.begin_nested():
                        job.embedding = None
                        await self._db.flush()
                    overall_result.jobs_failed += 1
                    overall_result.errors.append(f"Job {job.id} embedding failed: {str(err)}")

        # Process Profiles if any
        if profiles_to_process:
            overall_result.profiles_processed = len(profiles_to_process)
            for profile in profiles_to_process:
                try:
                    vector = self.embedding_service.generate_candidate_embedding(profile)
                    if (
                        not isinstance(vector, list)
                        or len(vector) != self.embedding_service.expected_dimension
                        or not all(math.isfinite(x) for x in vector)
                    ):
                        raise RuntimeError(
                            f"Generated vector dimension mismatch or non-finite values for profile {profile.id}"
                        )
                    async with self._db.begin_nested():
                        profile.embedding = vector
                        await self._db.flush()
                    overall_result.profiles_updated += 1
                except Exception as err:
                    async with self._db.begin_nested():
                        profile.embedding = None
                        await self._db.flush()
                    overall_result.profiles_failed += 1
                    overall_result.errors.append(
                        f"CandidateProfile {profile.id} embedding failed: {str(err)}"
                    )

        await self._db.commit()
        return overall_result
