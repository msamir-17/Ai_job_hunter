import math
from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from app.models import CandidateProfile, Job
from app.services.embedding import (
    EmbeddingService,
    format_candidate_profile_text,
    format_job_text,
)


def test_format_candidate_profile_text_verified_facts_only():
    """Verify format_candidate_profile_text extracts verified facts directly from CandidateProfile fields."""
    profile = CandidateProfile(
        headline="Senior AI Engineer",
        summary="Experienced in PyTorch and FastAPI.",
        target_titles=["AI Engineer", "ML Lead"],
        skills=["Python", "PyTorch", "FastAPI"],
        experience=[
            {"title": "AI Developer", "company": "Tech Innovations", "description": "Built LLM pipelines."}
        ],
        education=[
            {"degree": "B.S.", "field_of_study": "Computer Science", "institution": "State University"}
        ],
    )

    formatted = format_candidate_profile_text(profile)

    assert "Headline: Senior AI Engineer" in formatted
    assert "Target Titles: AI Engineer, ML Lead" in formatted
    assert "Skills: Python, PyTorch, FastAPI" in formatted
    assert "Summary: Experienced in PyTorch and FastAPI." in formatted
    assert "Experience: AI Developer at Tech Innovations: Built LLM pipelines." in formatted
    assert "Education: B.S. - Computer Science - State University" in formatted


def test_format_candidate_profile_does_not_access_resume():
    """Verify candidate text formatting strictly uses CandidateProfile and ignores unconfirmed Resume objects."""
    profile = CandidateProfile(
        headline="ML Engineer",
        skills=["Python"],
    )
    # Simulate presence of an unconfirmed resume relation
    profile.resumes = [MagicMock(parsed_json={"fake": "unverified_data"})]

    formatted = format_candidate_profile_text(profile)

    assert "fake" not in formatted
    assert "unverified_data" not in formatted
    assert "Headline: ML Engineer" in formatted
    assert "Skills: Python" in formatted


def test_format_candidate_profile_empty():
    """Verify format_candidate_profile_text with empty or None attributes returns an empty string."""
    profile = CandidateProfile()
    assert format_candidate_profile_text(profile) == ""


def test_format_job_text():
    """Verify format_job_text formats title, company, location, skills, and description."""
    job = Job(
        title="Machine Learning Engineer",
        company="AI Research Lab",
        location="San Francisco, CA",
        is_remote=True,
        skills_required=["PyTorch", "CUDA", "Python"],
        description_raw="We are hiring an ML engineer to work on foundation models.",
    )

    formatted = format_job_text(job)

    assert "Title: Machine Learning Engineer" in formatted
    assert "Company: AI Research Lab" in formatted
    assert "Location: Remote (San Francisco, CA)" in formatted
    assert "Required Skills: PyTorch, CUDA, Python" in formatted
    assert "Description: We are hiring an ML engineer to work on foundation models." in formatted


def test_format_job_text_empty():
    """Verify format_job_text with empty attributes returns empty string."""
    job = Job()
    assert format_job_text(job) == ""


def test_blank_input_handling():
    """Verify empty or whitespace-only text inputs raise ValueError."""
    EmbeddingService.reset_model_instance()
    service = EmbeddingService(model_name="dummy-model", expected_dimension=384)

    with pytest.raises(ValueError, match="empty or blank text"):
        service.generate_embedding("")

    with pytest.raises(ValueError, match="empty or blank text"):
        service.generate_embedding("   \n\t  ")

    empty_profile = CandidateProfile()
    with pytest.raises(ValueError, match="no embeddable text content"):
        service.generate_candidate_embedding(empty_profile)

    empty_job = Job()
    with pytest.raises(ValueError, match="no embeddable text content"):
        service.generate_job_embedding(empty_job)


def test_generate_embedding_mocked_vector_dimension_and_finite_values():
    """Verify embedding vector generation produces finite floats and strictly matches expected dimension (384)."""
    EmbeddingService.reset_model_instance()
    service = EmbeddingService(model_name="dummy-model", expected_dimension=384)

    # Mock 384-dimensional unnormalized numpy array output
    mock_vector = np.random.uniform(low=-1.0, high=1.0, size=(384,))

    mock_model = MagicMock()
    mock_model.encode.return_value = mock_vector

    with patch.object(EmbeddingService, "_get_model", return_value=mock_model):
        embedding = service.generate_embedding("Valid test text")

        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
        assert all(math.isfinite(x) for x in embedding)

        # Check L2 normalization
        norm = math.sqrt(sum(x * x for x in embedding))
        assert math.isclose(norm, 1.0, abs_tol=1e-5)


def test_generate_embedding_dimension_mismatch():
    """Verify RuntimeError is raised if model returns an unexpected vector length (e.g. 512 instead of 384)."""
    EmbeddingService.reset_model_instance()
    service = EmbeddingService(model_name="dummy-model", expected_dimension=384)

    mock_vector = np.ones(512)
    mock_model = MagicMock()
    mock_model.encode.return_value = mock_vector

    with patch.object(EmbeddingService, "_get_model", return_value=mock_model):
        with pytest.raises(RuntimeError, match="dimension mismatch"):
            service.generate_embedding("Valid test text")


def test_model_loading_failure():
    """Verify RuntimeError is raised with clear explanation if model loading fails."""
    EmbeddingService.reset_model_instance()

    mock_st_module = MagicMock()
    mock_st_module.SentenceTransformer.side_effect = Exception("Connection refused")

    with patch.dict("sys.modules", {"sentence_transformers": mock_st_module}):
        with pytest.raises(RuntimeError, match="Failed to load embedding model"):
            EmbeddingService._get_model("invalid-model-name")


def test_encoding_failure():
    """Verify RuntimeError is raised if model.encode throws an exception."""
    EmbeddingService.reset_model_instance()
    service = EmbeddingService(model_name="dummy-model", expected_dimension=384)

    mock_model = MagicMock()
    mock_model.encode.side_effect = Exception("GPU OOM")

    with patch.object(EmbeddingService, "_get_model", return_value=mock_model):
        with pytest.raises(RuntimeError, match="Failed to encode text"):
            service.generate_embedding("Valid text")


def test_lazy_singleton_caching():
    """Verify underlying model instance is loaded lazily and cached across multiple service instances."""
    EmbeddingService.reset_model_instance()

    mock_model = MagicMock()
    mock_vector = np.ones(384)
    mock_model.encode.return_value = mock_vector

    mock_st_class = MagicMock(return_value=mock_model)
    mock_st_module = MagicMock(SentenceTransformer=mock_st_class)

    with patch.dict("sys.modules", {"sentence_transformers": mock_st_module}):
        service1 = EmbeddingService()
        service2 = EmbeddingService()

        vec1 = service1.generate_embedding("Text one")
        vec2 = service2.generate_embedding("Text two")

        assert len(vec1) == 384
        assert len(vec2) == 384
        # SentenceTransformer constructor should have been called exactly ONCE
        mock_st_class.assert_called_once_with("sentence-transformers/all-MiniLM-L6-v2")
