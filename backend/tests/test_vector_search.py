import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.models import CandidateProfile, Job, JobMatch
from app.schemas.matching import VectorSearchRequest
from app.services.embedding import EmbeddingService
from app.services.vector_search import VectorSearchService


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def mock_db():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_embedding_service():
    service = MagicMock(spec=EmbeddingService)
    service.expected_dimension = 384
    service.generate_embedding.return_value = [0.1] * 384
    return service


@pytest.mark.anyio
async def test_ensure_candidate_embedding_already_exists(mock_db):
    """When candidate already has a 384-dim vector, returns it directly without regenerating."""
    existing_vector = [0.05] * 384
    cand = CandidateProfile(
        id=uuid.uuid4(),
        headline="AI Engineer",
        embedding=existing_vector,
    )
    service = VectorSearchService(db=mock_db)
    result = await service.ensure_candidate_embedding(cand)

    assert result == existing_vector
    mock_db.commit.assert_not_called()


@pytest.mark.anyio
async def test_ensure_candidate_embedding_generates_when_missing(mock_db, mock_embedding_service):
    """When candidate has verified fields but no vector, generates and persists it."""
    cand = CandidateProfile(
        id=uuid.uuid4(),
        headline="NLP Specialist",
        skills=["PyTorch", "HuggingFace"],
        embedding=None,
    )
    service = VectorSearchService(db=mock_db, embedding_service=mock_embedding_service)
    result = await service.ensure_candidate_embedding(cand)

    assert len(result) == 384
    assert cand.embedding == [0.1] * 384
    mock_embedding_service.generate_embedding.assert_called_once()
    mock_db.add.assert_called_once_with(cand)
    mock_db.commit.assert_called_once()


@pytest.mark.anyio
async def test_ensure_candidate_embedding_raises_if_empty_profile(mock_db):
    """Raises ValueError when candidate profile has no verified fields to embed."""
    cand = CandidateProfile(
        id=uuid.uuid4(),
        headline="",
        summary="",
        skills=[],
        experience=[],
        embedding=None,
    )
    service = VectorSearchService(db=mock_db)

    with pytest.raises(ValueError, match="no verified profile fields"):
        await service.ensure_candidate_embedding(cand)


@pytest.mark.anyio
async def test_search_candidate_not_found_raises(mock_db):
    """Raises ValueError when candidate profile ID does not exist."""
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_res

    service = VectorSearchService(db=mock_db)
    req = VectorSearchRequest(candidate_profile_id=uuid.uuid4())

    with pytest.raises(ValueError, match="not found"):
        await service.search_and_persist_matches(req)


@pytest.mark.anyio
async def test_search_and_persist_matches_success(mock_db):
    """Verifies vector search result ranking, cosine similarity conversion, and JobMatch update."""
    candidate_id = uuid.uuid4()
    candidate = CandidateProfile(
        id=candidate_id,
        headline="AI Research Engineer",
        embedding=[0.2] * 384,
    )

    job1 = Job(
        id=uuid.uuid4(),
        title="ML Engineer",
        company="Alpha AI",
        location="Remote",
        is_remote=True,
    )
    job2 = Job(
        id=uuid.uuid4(),
        title="Data Scientist",
        company="Beta Analytics",
        location="New York, NY",
        is_remote=False,
    )

    match1 = JobMatch(
        id=uuid.uuid4(),
        candidate_profile_id=candidate_id,
        job_id=job1.id,
        passed_deterministic=True,
        status="shortlisted",
        matched_skills=["Python"],
    )

    # 1st execute: fetch candidate
    mock_cand_res = MagicMock()
    mock_cand_res.scalar_one_or_none.return_value = candidate

    # 2nd execute: query vector matches (job, match, similarity)
    # raw_similarity for job1 = 0.8854, for job2 = 0.7210
    mock_rows_res = MagicMock()
    mock_rows_res.all.return_value = [
        (job1, match1, 0.88542),
        (job2, None, 0.72101),
    ]

    mock_db.execute.side_effect = [mock_cand_res, mock_rows_res]

    service = VectorSearchService(db=mock_db)
    req = VectorSearchRequest(
        candidate_profile_id=candidate_id,
        limit=10,
        only_passed_deterministic=False,
        min_similarity_threshold=0.5,
    )
    results = await service.search_and_persist_matches(req)

    assert len(results) == 2
    assert results[0].job_id == job1.id
    assert results[0].vector_score == 0.8854
    assert results[0].passed_deterministic is True
    assert match1.vector_score == 0.8854

    # job2 had no prior match record, should have been newly added
    assert results[1].job_id == job2.id
    assert results[1].vector_score == 0.7210
    assert results[1].passed_deterministic is False

    mock_db.commit.assert_called_once()
