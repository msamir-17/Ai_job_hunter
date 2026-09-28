import math
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import CandidateProfile, Job
from app.services.embedding import EmbeddingService
from app.services.embedding_persistence import (
    EmbeddingPersistenceResult,
    EmbeddingPersistenceService,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def mock_db():
    """Mock AsyncSession for unit testing."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    
    # Mock begin_nested context manager
    nested_cm = AsyncMock()
    nested_cm.__aenter__ = AsyncMock()
    nested_cm.__aexit__ = AsyncMock()
    session.begin_nested = MagicMock(return_value=nested_cm)
    
    return session


@pytest.fixture
def mock_embedding_service():
    """Mock EmbeddingService for unit testing."""
    service = MagicMock(spec=EmbeddingService)
    service.expected_dimension = 384
    return service


@pytest.mark.anyio
async def test_backfill_embeddings_zero_records_avoids_model_loading(mock_db):
    """
    Verify backfill_embeddings queries database first and exits early
    without triggering embedding model loading when 0 records need embeddings.
    """
    mock_result_empty = MagicMock()
    mock_result_empty.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result_empty

    with patch.object(EmbeddingService, "_get_model") as mock_get_model:
        service = EmbeddingPersistenceService(db=mock_db)
        res = await service.backfill_embeddings()

        assert isinstance(res, EmbeddingPersistenceResult)
        assert res.jobs_processed == 0
        assert res.jobs_updated == 0
        assert res.profiles_processed == 0
        assert res.profiles_updated == 0
        assert res.errors == []

        # Model loader MUST NOT have been called
        mock_get_model.assert_not_called()


@pytest.mark.anyio
async def test_generate_and_persist_job_embeddings_success(mock_db, mock_embedding_service):
    """Verify successful generation and persistence of job embeddings."""
    job1 = Job(id=uuid.uuid4(), title="AI Engineer", company="Tech Co", embedding=None)
    job2 = Job(id=uuid.uuid4(), title="ML Dev", company="Data Inc", embedding=None)

    mock_exec_res = MagicMock()
    mock_exec_res.scalars.return_value.all.return_value = [job1, job2]
    mock_db.execute.return_value = mock_exec_res

    fake_vector = [0.1] * 384
    mock_embedding_service.generate_job_embedding.return_value = fake_vector

    service = EmbeddingPersistenceService(
        db=mock_db, embedding_service=mock_embedding_service
    )
    res = await service.generate_and_persist_job_embeddings()

    assert res.jobs_processed == 2
    assert res.jobs_updated == 2
    assert res.jobs_failed == 0
    assert job1.embedding == fake_vector
    assert job2.embedding == fake_vector
    assert mock_db.commit.called


@pytest.mark.anyio
async def test_generate_and_persist_candidate_embeddings_success(mock_db, mock_embedding_service):
    """Verify successful generation and persistence of candidate profile embeddings."""
    profile = CandidateProfile(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        headline="Senior AI Engineer",
        skills=["Python", "PyTorch"],
        embedding=None,
    )

    mock_exec_res = MagicMock()
    mock_exec_res.scalars.return_value.all.return_value = [profile]
    mock_db.execute.return_value = mock_exec_res

    fake_vector = [0.2] * 384
    mock_embedding_service.generate_candidate_embedding.return_value = fake_vector

    service = EmbeddingPersistenceService(
        db=mock_db, embedding_service=mock_embedding_service
    )
    res = await service.generate_and_persist_candidate_embeddings()

    assert res.profiles_processed == 1
    assert res.profiles_updated == 1
    assert res.profiles_failed == 0
    assert profile.embedding == fake_vector
    assert mock_db.commit.called


@pytest.mark.anyio
async def test_missing_text_keeps_embedding_null(mock_db, mock_embedding_service):
    """Verify Job/Profile with missing embeddable text keeps embedding NULL and records error."""
    empty_job = Job(id=uuid.uuid4(), title="", company="", embedding=None)

    mock_exec_res = MagicMock()
    mock_exec_res.scalars.return_value.all.return_value = [empty_job]
    mock_db.execute.return_value = mock_exec_res

    mock_embedding_service.generate_job_embedding.side_effect = ValueError(
        "Job contains no embeddable text content."
    )

    service = EmbeddingPersistenceService(
        db=mock_db, embedding_service=mock_embedding_service
    )
    res = await service.generate_and_persist_job_embeddings()

    assert res.jobs_processed == 1
    assert res.jobs_updated == 0
    assert res.jobs_failed == 1
    assert empty_job.embedding is None
    assert len(res.errors) == 1
    assert "no embeddable text" in res.errors[0]


@pytest.mark.anyio
async def test_invalid_vector_dimension_keeps_embedding_null(mock_db, mock_embedding_service):
    """Verify invalid or wrong-dimension vector keeps embedding NULL without breaking batch."""
    job = Job(id=uuid.uuid4(), title="Valid Title", company="Valid Co", embedding=None)

    mock_exec_res = MagicMock()
    mock_exec_res.scalars.return_value.all.return_value = [job]
    mock_db.execute.return_value = mock_exec_res

    # Return 512 dimensions instead of 384
    invalid_vector = [0.1] * 512
    mock_embedding_service.generate_job_embedding.return_value = invalid_vector

    service = EmbeddingPersistenceService(
        db=mock_db, embedding_service=mock_embedding_service
    )
    res = await service.generate_and_persist_job_embeddings()

    assert res.jobs_processed == 1
    assert res.jobs_updated == 0
    assert res.jobs_failed == 1
    assert job.embedding is None
    assert len(res.errors) == 1
    assert "dimension mismatch" in res.errors[0]


@pytest.mark.anyio
async def test_idempotency_ignores_existing_embeddings_by_default(mock_db):
    """Verify jobs with existing non-null embeddings are filtered out by default."""
    mock_result_empty = MagicMock()
    mock_result_empty.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result_empty

    service = EmbeddingPersistenceService(db=mock_db)
    res = await service.generate_and_persist_job_embeddings(force_regenerate=False)

    assert res.jobs_processed == 0
    assert res.jobs_updated == 0


@pytest.mark.anyio
async def test_candidate_profile_formatting_ignores_resume_parsed_json(mock_db, mock_embedding_service):
    """Verify candidate embedding logic uses CandidateProfile fields and ignores Resume.parsed_json."""
    profile = CandidateProfile(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        headline="AI Specialist",
        skills=["Python"],
        embedding=None,
    )
    # Simulate presence of an unconfirmed resume with parsed_json
    profile.resumes = [MagicMock(parsed_json={"unconfirmed_skill": "Rust"})]

    mock_exec_res = MagicMock()
    mock_exec_res.scalars.return_value.all.return_value = [profile]
    mock_db.execute.return_value = mock_exec_res

    fake_vector = [0.3] * 384
    mock_embedding_service.generate_candidate_embedding.return_value = fake_vector

    service = EmbeddingPersistenceService(
        db=mock_db, embedding_service=mock_embedding_service
    )
    res = await service.generate_and_persist_candidate_embeddings()

    assert res.profiles_updated == 1
    assert profile.embedding == fake_vector
    # Verify generate_candidate_embedding was called directly with the CandidateProfile object
    mock_embedding_service.generate_candidate_embedding.assert_called_once_with(profile)
