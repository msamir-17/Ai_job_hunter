"""
AI Job Hunter Co-Pilot - Background Worker Daemon & Scheduled Ingestion.
Runs periodic ingestion, SKIP LOCKED queue consumption, heartbeats, and graceful shutdown.
"""
import argparse
import asyncio
import logging
import os
import signal
import sys
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters import AdzunaJobSourceAdapter, ManualJobSourceAdapter, RemotiveJobSourceAdapter
from app.config import settings
from app.database import AsyncSessionLocal, engine
from app.models import Job, WorkerHeartbeat
from app.services.job_ingestion import JobIngestionService
from app.services.job_queue import AsyncJobQueueWorker, PipelineStatus

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("ai_job_hunter.worker")


class JobHunterWorkerDaemon:
    """
    Production-grade background worker daemon:
    - Periodic scheduled ingestion across multiple adapters with deduplication
    - High-concurrency Postgres SKIP LOCKED queue consumption
    - Real-time heartbeat persistence in worker_heartbeats table
    - Clean signal handling and graceful shutdown
    """

    def __init__(self, worker_id: str | None = None):
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.is_running = False
        self.stop_event = asyncio.Event()
        self.jobs_processed_total = 0
        self.last_ingest_time: datetime | None = None

    async def update_heartbeat(self, status: str = "active", stage: str | None = None):
        """Upsert current worker heartbeat into database."""
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(WorkerHeartbeat).where(WorkerHeartbeat.worker_id == self.worker_id)
                res = await session.execute(stmt)
                hb = res.scalar_one_or_none()
                now_utc = datetime.now(timezone.utc)

                if hb:
                    hb.status = status
                    hb.last_heartbeat_at = now_utc
                    hb.jobs_processed = self.jobs_processed_total
                    hb.current_stage = stage
                else:
                    hb = WorkerHeartbeat(
                        worker_id=self.worker_id,
                        status=status,
                        last_heartbeat_at=now_utc,
                        jobs_processed=self.jobs_processed_total,
                        current_stage=stage,
                    )
                    session.add(hb)
                await session.commit()
        except Exception as e:
            logger.warning(f"Failed to record worker heartbeat: {str(e)}")

    async def run_ingestion_cycle(self, limit: int = 20) -> int:
        """
        Executes one ingestion pass across configured source adapters and enqueues matches.
        """
        total_enqueued = 0
        logger.info(f"Worker [{self.worker_id}] starting scheduled ingestion cycle...")
        await self.update_heartbeat(status="active", stage="ingesting")

        for source in settings.WORKER_ENABLED_SOURCES:
            source_lower = source.strip().lower()
            adapter = None
            if source_lower == "manual":
                adapter = ManualJobSourceAdapter()
            elif source_lower == "remotive":
                adapter = RemotiveJobSourceAdapter()
            elif source_lower == "adzuna":
                if settings.ADZUNA_APP_ID and settings.ADZUNA_APP_KEY:
                    adapter = AdzunaJobSourceAdapter()
                else:
                    logger.debug("Skipping Adzuna adapter: missing credentials.")
                    continue

            if not adapter:
                continue

            try:
                async with AsyncSessionLocal() as session:
                    service = JobIngestionService(session)
                    ingest_result = await service.ingest_jobs(adapter=adapter, limit=limit)
                    logger.info(
                        f"Ingestion from '{source_lower}': fetched={ingest_result.fetched}, "
                        f"inserted={ingest_result.inserted}, skipped_dups={ingest_result.skipped_duplicates}"
                    )

                    # If new jobs were inserted, enqueue them for candidate profiles
                    if ingest_result.inserted > 0:
                        # Fetch recent job IDs for this source
                        recent_stmt = (
                            select(Job.id)
                            .where(Job.source == source_lower)
                            .order_by(Job.created_at.desc())
                            .limit(ingest_result.inserted)
                        )
                        recent_jobs = await session.execute(recent_stmt)
                        job_ids = list(recent_jobs.scalars().all())

                        enqueued = await AsyncJobQueueWorker.enqueue_jobs_for_candidates(session, job_ids)
                        total_enqueued += enqueued
                        logger.info(f"Enqueued {enqueued} new JobMatch records for candidate profiles.")

            except Exception as e:
                logger.error(f"Error during scheduled ingestion from '{source_lower}': {str(e)}")

        self.last_ingest_time = datetime.now(timezone.utc)
        return total_enqueued

    async def run_queue_pass(self) -> int:
        """
        Executes one batch consumption pass from Postgres queue using SKIP LOCKED.
        """
        await self.update_heartbeat(status="active", stage="processing_queue")
        async with AsyncSessionLocal() as session:
            worker = AsyncJobQueueWorker(session)
            processed = await worker.process_batch(
                batch_size=settings.WORKER_BATCH_SIZE,
                max_retries=settings.WORKER_MAX_RETRIES,
            )
            if processed > 0:
                self.jobs_processed_total += processed
                logger.info(f"Worker [{self.worker_id}] processed {processed} matches in current batch.")
            return processed

    async def start(self, run_once: bool = False):
        """
        Main worker execution entrypoint. Runs continuous loop or single cycle.
        """
        self.is_running = True
        logger.info(f"Starting JobHunterWorkerDaemon [ID: {self.worker_id}] (run_once={run_once})...")
        await self.update_heartbeat(status="active", stage="initialized")

        if run_once:
            logger.info("Running single iteration mode (--once)...")
            await self.run_ingestion_cycle(limit=10)
            while True:
                processed = await self.run_queue_pass()
                if processed == 0:
                    break
            self.is_running = False
            await self.update_heartbeat(status="stopped", stage="completed")
            logger.info("Single iteration mode finished cleanly.")
            return

        # Setup background heartbeat task
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        last_ingest_timestamp = 0.0
        try:
            while not self.stop_event.is_set():
                now = asyncio.get_event_loop().time()

                # 1. Scheduled Ingestion Trigger
                if now - last_ingest_timestamp >= settings.WORKER_INGESTION_INTERVAL_SECONDS:
                    await self.run_ingestion_cycle()
                    last_ingest_timestamp = now

                # 2. Queue Consumption Pass
                processed = await self.run_queue_pass()

                # Adaptive Sleep: sleep only when queue was empty
                if processed == 0:
                    try:
                        await asyncio.wait_for(
                            self.stop_event.wait(),
                            timeout=settings.WORKER_POLL_INTERVAL_SECONDS,
                        )
                    except asyncio.TimeoutError:
                        pass
                else:
                    # Small yield to prevent event loop starvation
                    await asyncio.sleep(0.01)

        except asyncio.CancelledError:
            logger.info(f"Worker [{self.worker_id}] received cancellation signal.")
        finally:
            self.is_running = False
            heartbeat_task.cancel()
            await self.update_heartbeat(status="stopped", stage="shutdown")
            logger.info(f"Worker [{self.worker_id}] shutdown complete. Total processed: {self.jobs_processed_total}")

    async def _heartbeat_loop(self):
        """Background coroutine keeping heartbeat fresh."""
        try:
            while not self.stop_event.is_set():
                await asyncio.sleep(5.0)
                await self.update_heartbeat(status="active", stage="idle")
        except asyncio.CancelledError:
            pass

    def stop(self):
        """Signals worker to stop gracefully."""
        logger.info(f"Worker [{self.worker_id}] shutdown requested.")
        self.stop_event.set()


async def print_queue_status():
    """CLI utility to query and format current queue status from database."""
    async with AsyncSessionLocal() as session:
        depths = await AsyncJobQueueWorker.get_queue_depths(session)
        stmt = select(WorkerHeartbeat).order_by(WorkerHeartbeat.last_heartbeat_at.desc())
        res = await session.execute(stmt)
        heartbeats = res.scalars().all()

    print("\n--- AI JOB HUNTER WORKER & QUEUE STATUS ---")
    print(f"Ingested (Pending):  {depths.get(PipelineStatus.INGESTED, 0)}")
    print(f"Filtered:            {depths.get(PipelineStatus.FILTERED, 0)}")
    print(f"Scored (Ready):      {depths.get(PipelineStatus.SCORED, 0)}")
    print(f"Tailored:            {depths.get(PipelineStatus.TAILORED, 0)}")
    print(f"Failed:              {depths.get(PipelineStatus.FAILED, 0)}")
    print(f"Dead Letter (DLQ):   {depths.get(PipelineStatus.DEAD_LETTER, 0)}")
    print("------------------------------------------")

    if heartbeats:
        print("Registered Workers:")
        now_utc = datetime.now(timezone.utc)
        for hb in heartbeats:
            age_secs = (now_utc - hb.last_heartbeat_at.replace(tzinfo=timezone.utc)).total_seconds()
            is_alive = age_secs < 30.0 and hb.status != "stopped"
            health_str = "HEALTHY" if is_alive else "OFFLINE"
            print(
                f" - {hb.worker_id}: status={hb.status} ({health_str}, age={age_secs:.1f}s), "
                f"processed={hb.jobs_processed}, stage={hb.current_stage}"
            )
    else:
        print("No worker heartbeats found in database.")
    print("------------------------------------------\n")


def main():
    parser = argparse.ArgumentParser(description="AI Job Hunter Background Worker Daemon")
    parser.add_argument("--once", action="store_true", help="Run one ingestion and drain queue pass, then exit")
    parser.add_argument("--status", action="store_true", help="Print queue depths and worker heartbeats, then exit")
    parser.add_argument("--ingest-now", action="store_true", help="Trigger immediate ingestion cycle and exit")
    parser.add_argument("--worker-id", type=str, default=None, help="Custom identifier for this worker instance")
    args = parser.parse_args()

    if args.status:
        asyncio.run(print_queue_status())
        return

    daemon = JobHunterWorkerDaemon(worker_id=args.worker_id)

    if args.ingest_now:
        async def _run_ingest():
            enqueued = await daemon.run_ingestion_cycle()
            print(f"Immediate ingestion completed. Enqueued {enqueued} matches.")
            await print_queue_status()
        asyncio.run(_run_ingest())
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def _handle_shutdown(*_):
        daemon.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_shutdown)
        except (NotImplementedError, AttributeError):
            # Windows signal handling fallback
            signal.signal(sig, _handle_shutdown)

    try:
        loop.run_until_complete(daemon.start(run_once=args.once))
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, stopping worker...")
        daemon.stop()
        loop.run_until_complete(asyncio.sleep(0.5))
    finally:
        loop.close()


if __name__ == "__main__":
    main()
