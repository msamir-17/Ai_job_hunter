import uuid
import pytest
from sqlalchemy import delete, select

from app.database import AsyncSessionLocal, engine
from app.models import CandidateProfile, Job, User
from app.services.embedding_persistence import EmbeddingPersistenceService


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def dispose_db_engine():
    yield
    await engine.dispose()


@pytest.mark.anyio
async def test_embedding_persistence_real_postgres():
    """
    Integration test verifying embedding generation and persistence
    against real Docker PostgreSQL database (port 5435, ai_job_hunter).
    """
    test_user_id = uuid.uuid4()
    test_email = f"emb_test_{test_user_id.hex[:8]}@example.com"

    candidate_profile_id = None
    job_ids = []
    empty_job_id = None

    try:
        # 1. Setup User, CandidateProfile, and Jobs in real Postgres (port 5435)
        async with AsyncSessionLocal() as db:
            user = User(
                id=test_user_id,
                email=test_email,
                hashed_password="hashed_password",
                full_name="Embedding Integration Candidate",
            )
            db.add(user)

            candidate = CandidateProfile(
                user_id=test_user_id,
                headline="Senior PyTorch & FastAPI Engineer",
                skills=["Python", "FastAPI", "PyTorch", "pgvector"],
                experience=[
                    {
                        "company": "AI Labs",
                        "title": "ML Engineer",
                        "description": "Engineered vector search pipelines.",
                    }
                ],
                target_titles=["AI Engineer"],
                embedding=None,  # Intentionally NULL
            )
            db.add(candidate)
            await db.commit()
            await db.refresh(candidate)
            candidate_profile_id = candidate.id

            job1 = Job(
                source="manual",
                external_id=f"ext_{uuid.uuid4().hex[:8]}",
                title="Staff AI Engineer",
                company="Vector Scale",
                description_raw="Building large scale pgvector vector search infrastructure.",
                is_remote=True,
                skills_required=["Python", "pgvector", "PyTorch"],
                embedding=None,  # Intentionally NULL
            )
            job2 = Job(
                source="manual",
                external_id=f"ext_{uuid.uuid4().hex[:8]}",
                title="Machine Learning Researcher",
                company="Deep AI Lab",
                description_raw="Researching MiniLM vector representations.",
                is_remote=False,
                skills_required=["PyTorch", "Transformers"],
                embedding=None,  # Intentionally NULL
            )
            empty_job = Job(
                source="manual",
                external_id=f"ext_{uuid.uuid4().hex[:8]}",
                title="",
                company="",
                description_raw="",
                skills_required=[],
                embedding=None,  # Intentionally NULL
            )

            db.add_all([job1, job2, empty_job])
            await db.commit()
            await db.refresh(job1)
            await db.refresh(job2)
            await db.refresh(empty_job)
            job_ids = [job1.id, job2.id]
            empty_job_id = empty_job.id

        # 2. Run EmbeddingPersistenceService backfill
        from unittest.mock import MagicMock
        from app.services.embedding import EmbeddingService, format_job_text

        mock_emb = MagicMock(spec=EmbeddingService)
        mock_emb.expected_dimension = 384
        mock_emb.generate_embedding.side_effect = lambda t: [1.0 / (384 ** 0.5)] * 384
        mock_emb.generate_candidate_embedding.side_effect = lambda p: [1.0 / (384 ** 0.5)] * 384

        def mock_job_emb(job):
            text = format_job_text(job)
            if not text:
                raise ValueError("Job contains no embeddable text content.")
            return [1.0 / (384 ** 0.5)] * 384

        mock_emb.generate_job_embedding.side_effect = mock_job_emb

        async with AsyncSessionLocal() as db:
            service = EmbeddingPersistenceService(db=db, embedding_service=mock_emb)
            result = await service.backfill_embeddings()

            assert result.jobs_processed >= 2
            assert result.jobs_updated >= 2
            assert result.profiles_processed >= 1
            assert result.profiles_updated >= 1

        # 3. Verify vector persistence in PostgreSQL
        async with AsyncSessionLocal() as db:
            # Check CandidateProfile vector
            res_cand = await db.execute(
                select(CandidateProfile).where(CandidateProfile.id == candidate_profile_id)
            )
            db_cand = res_cand.scalar_one()
            assert db_cand.embedding is not None
            assert len(db_cand.embedding) == 384
            assert any(x != 0 for x in db_cand.embedding)

            # Check Job vectors
            res_j1 = await db.execute(select(Job).where(Job.id == job_ids[0]))
            db_j1 = res_j1.scalar_one()
            assert db_j1.embedding is not None
            assert len(db_j1.embedding) == 384

            # Check Empty Job vector (must remain NULL)
            res_empty = await db.execute(select(Job).where(Job.id == empty_job_id))
            db_empty = res_empty.scalar_one()
            assert db_empty.embedding is None

        # 4. Test Idempotency: Re-running backfill when embeddings exist
        async with AsyncSessionLocal() as db:
            service = EmbeddingPersistenceService(db=db)
            rerun_res = await service.backfill_embeddings(force_regenerate=False)

            # Only empty_job or other un-embeddable records remain without embeddings
            assert rerun_res.jobs_updated == 0
            assert rerun_res.profiles_updated == 0

    finally:
        # Cleanup test records from PostgreSQL
        async with AsyncSessionLocal() as db:
            if candidate_profile_id:
                await db.execute(
                    delete(CandidateProfile).where(CandidateProfile.id == candidate_profile_id)
                )
            for jid in job_ids:
                await db.execute(delete(Job).where(Job.id == jid))
            if empty_job_id:
                await db.execute(delete(Job).where(Job.id == empty_job_id))
            await db.execute(delete(User).where(User.id == test_user_id))
            await db.commit()
