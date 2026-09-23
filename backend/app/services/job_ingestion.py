import uuid
from typing import Any
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import BaseJobSourceAdapter
from app.models import Job
from app.schemas.job import IngestionResult, NormalizedJob


class JobIngestionService:
    """
    Core service coordinating job fetching, deterministic normalization,
    Pydantic validation, idempotent PostgreSQL deduplication, and batch persistence.
    """

    def __init__(self, db: AsyncSession):
        self._db = db

    async def ingest_jobs(
        self,
        adapter: BaseJobSourceAdapter,
        limit: int | None = None,
        **adapter_kwargs: Any,
    ) -> IngestionResult:
        """
        Executes job ingestion from the provided source adapter into PostgreSQL.

        :param adapter: Concrete implementation of BaseJobSourceAdapter.
        :param limit: Maximum number of jobs to fetch and process.
        :param adapter_kwargs: Additional kwargs passed to adapter.fetch_jobs (e.g. use_cache=True).
        :return: IngestionResult with execution statistics.
        """
        source_name = adapter.source_name
        result = IngestionResult(source=source_name)

        # 1. Fetch raw job data from adapter
        try:
            raw_jobs = await adapter.fetch_jobs(limit=limit, **adapter_kwargs)
            result.fetched = len(raw_jobs)
        except Exception as err:
            result.failed += 1
            result.errors.append(f"Adapter fetch error: {str(err)}")
            return result

        if not raw_jobs:
            return result

        # Enforce deterministic limit processing
        if limit is not None and limit > 0:
            raw_jobs = raw_jobs[:limit]

        # 2. Normalize and validate raw items into NormalizedJob objects
        normalized_jobs: list[NormalizedJob] = []
        for idx, raw_item in enumerate(raw_jobs, start=1):
            # Ensure source field is explicitly populated
            item_data = dict(raw_item)
            item_data["source"] = source_name

            try:
                norm_job = NormalizedJob.model_validate(item_data)
                normalized_jobs.append(norm_job)
                result.normalized += 1
            except ValidationError as val_err:
                result.failed += 1
                error_msg = f"Job #{idx} validation error (ID: {item_data.get('external_id', 'unknown')}): {val_err.errors()[0]['msg']}"
                result.errors.append(error_msg)
            except Exception as err:
                result.failed += 1
                result.errors.append(f"Job #{idx} normalization error: {str(err)}")

        if not normalized_jobs:
            return result

        # 3. Application-level duplicate pre-check for target source
        external_ids = [job.external_id for job in normalized_jobs]
        stmt = select(Job.external_id).where(
            Job.source == source_name,
            Job.external_id.in_(external_ids),
        )
        existing_res = await self._db.execute(stmt)
        existing_set = set(existing_res.scalars().all())

        # 4. Idempotent database insertion
        for norm_job in normalized_jobs:
            if norm_job.external_id in existing_set:
                result.skipped_duplicates += 1
                continue

            # Create SQLAlchemy ORM model
            new_job = Job(
                id=uuid.uuid4(),
                source=norm_job.source,
                external_id=norm_job.external_id,
                title=norm_job.title,
                company=norm_job.company,
                location=norm_job.location,
                is_remote=norm_job.is_remote,
                salary_min=norm_job.salary_min,
                salary_max=norm_job.salary_max,
                description_raw=norm_job.raw_description,
                skills_required=norm_job.skills_required,
                url=norm_job.url,
                embedding=None,  # Intentionally NULL for Step 4
            )

            # Use nested transaction (savepoint) for race condition / duplicate safety
            async with self._db.begin_nested():
                self._db.add(new_job)
                try:
                    await self._db.flush()
                    result.inserted += 1
                    existing_set.add(norm_job.external_id)
                except IntegrityError:
                    # Duplicate caught at PostgreSQL UNIQUE constraint boundary
                    result.skipped_duplicates += 1

        # Commit batch transaction
        await self._db.commit()
        return result
