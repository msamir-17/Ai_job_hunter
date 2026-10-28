"""
Backfill script for existing Job records.
Computes deterministic dedup_key and populates source_url, apply_url, and posted_at
for legacy rows where these columns are currently NULL.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Job
from app.services.dedup_service import generate_dedup_key

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("backfill_dedup")


async def backfill_jobs() -> int:
    async with AsyncSessionLocal() as session:
        stmt = select(Job).where(Job.dedup_key.is_(None))
        result = await session.execute(stmt)
        jobs = list(result.scalars().all())

        if not jobs:
            logger.info("No jobs found with NULL dedup_key. Everything is up to date!")
            return 0

        logger.info(f"Found {len(jobs)} jobs needing backfill.")
        updated_count = 0

        for job in jobs:
            job.dedup_key = generate_dedup_key(
                company=job.company,
                title=job.title,
                location=job.location,
                is_remote=job.is_remote,
            )
            if not job.source_url and job.url:
                job.source_url = job.url
            if not job.apply_url and job.url:
                job.apply_url = job.url
            if not job.posted_at and job.created_at:
                job.posted_at = job.created_at

            updated_count += 1

        await session.commit()
        logger.info(f"Successfully backfilled {updated_count} jobs.")
        return updated_count


if __name__ == "__main__":
    count = asyncio.run(backfill_jobs())
    print(f"Backfill complete: {count} jobs updated.")
