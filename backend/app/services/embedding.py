import math
from typing import Any

import numpy as np

from app.config import settings
from app.models import CandidateProfile, Job


def format_candidate_profile_text(profile: CandidateProfile) -> str:
    """
    Format verified CandidateProfile fields into a structured text representation for embedding.

    STRICT GROUNDING & ZERO-HALLUCINATION GUARDRAIL:
    - Exclusively reads verified fields directly on the CandidateProfile model.
    - NEVER accesses, reads, or embeds unconfirmed Resume.parsed_json or external resume uploads.
    """
    parts: list[str] = []

    if profile.headline and profile.headline.strip():
        parts.append(f"Headline: {profile.headline.strip()}")

    if profile.target_titles:
        titles = [str(t).strip() for t in profile.target_titles if isinstance(t, str) and str(t).strip()]
        if titles:
            parts.append(f"Target Titles: {', '.join(titles)}")

    if profile.skills:
        skills_list: list[str] = []
        for s in profile.skills:
            if isinstance(s, str) and s.strip():
                skills_list.append(s.strip())
            elif isinstance(s, dict) and s.get("name"):
                skills_list.append(str(s["name"]).strip())
        if skills_list:
            parts.append(f"Skills: {', '.join(skills_list)}")

    if profile.summary and profile.summary.strip():
        parts.append(f"Summary: {profile.summary.strip()}")

    if profile.experience and isinstance(profile.experience, list):
        exp_parts: list[str] = []
        for item in profile.experience:
            if isinstance(item, dict):
                title = str(item.get("title", "")).strip()
                company = str(item.get("company", "")).strip()
                desc = str(item.get("description", "")).strip()

                if title and company:
                    entry = f"{title} at {company}"
                elif title:
                    entry = title
                elif company:
                    entry = company
                else:
                    entry = ""

                if desc:
                    entry = f"{entry}: {desc}" if entry else desc

                if entry:
                    exp_parts.append(entry)

        if exp_parts:
            parts.append("Experience: " + " | ".join(exp_parts))

    if profile.education and isinstance(profile.education, list):
        edu_parts: list[str] = []
        for item in profile.education:
            if isinstance(item, dict):
                degree = str(item.get("degree", "")).strip()
                institution = str(item.get("institution", "")).strip()
                field = str(item.get("field_of_study", "")).strip()

                bits = [b for b in (degree, field, institution) if b]
                if bits:
                    edu_parts.append(" - ".join(bits))
            elif isinstance(item, str) and item.strip():
                edu_parts.append(item.strip())

        if edu_parts:
            parts.append("Education: " + " | ".join(edu_parts))

    return "\n".join(parts).strip()


def format_job_text(job: Job) -> str:
    """
    Format Job model fields into a structured text representation for embedding.
    """
    parts: list[str] = []

    if job.title and job.title.strip():
        parts.append(f"Title: {job.title.strip()}")

    if job.company and job.company.strip():
        parts.append(f"Company: {job.company.strip()}")

    location_str = job.location.strip() if job.location and job.location.strip() else ""
    if job.is_remote:
        location_str = f"Remote ({location_str})" if location_str else "Remote"
    if location_str:
        parts.append(f"Location: {location_str}")

    if job.skills_required and isinstance(job.skills_required, list):
        skills = [str(s).strip() for s in job.skills_required if isinstance(s, str) and str(s).strip()]
        if skills:
            parts.append(f"Required Skills: {', '.join(skills)}")

    if job.description_raw and job.description_raw.strip():
        parts.append(f"Description: {job.description_raw.strip()}")

    return "\n".join(parts).strip()


class EmbeddingService:
    """
    Service generating L2-normalized 384-dimensional dense vectors using Hugging Face SentenceTransformers.
    Employs lazy singleton loading for the underlying model to minimize startup latency and memory usage.
    """

    _model_instance: Any = None

    def __init__(
        self,
        model_name: str | None = None,
        expected_dimension: int | None = None,
    ):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.expected_dimension = expected_dimension or settings.EMBEDDING_DIMENSION

    @classmethod
    def reset_model_instance(cls) -> None:
        """Reset lazy singleton model instance (used primarily for testing)."""
        cls._model_instance = None

    @classmethod
    def _get_model(cls, model_name: str) -> Any:
        """Lazy singleton instance loader for SentenceTransformer."""
        if cls._model_instance is None:
            try:
                from sentence_transformers import SentenceTransformer

                cls._model_instance = SentenceTransformer(model_name)
            except Exception as err:
                raise RuntimeError(
                    f"Failed to load embedding model '{model_name}': {err}"
                ) from err
        return cls._model_instance

    def _normalize_vector(self, vector: list[float]) -> list[float]:
        """Ensure vector is L2-normalized (magnitude == 1.0)."""
        arr = np.array(vector, dtype=float)
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm
        return arr.tolist()

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate an L2-normalized dense vector for the given text.

        :param text: Input non-empty text string.
        :return: List of floats representing the embedding vector.
        :raises ValueError: If input text is empty or whitespace-only.
        :raises RuntimeError: If encoding fails or dimension mismatch occurs.
        """
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding for empty or blank text.")

        model = self._get_model(self.model_name)
        try:
            raw_output = model.encode(text, normalize_embeddings=True)
        except Exception as err:
            raise RuntimeError(
                f"Failed to encode text with embedding model '{self.model_name}': {err}"
            ) from err

        if isinstance(raw_output, np.ndarray):
            vec_list = raw_output.astype(float).tolist()
        else:
            vec_list = [float(x) for x in raw_output]

        # Verify finite numeric values
        if not all(math.isfinite(x) for x in vec_list):
            raise RuntimeError("Generated embedding contains non-finite numeric values (NaN or Inf).")

        # Verify exact dimension requirement (384)
        if len(vec_list) != self.expected_dimension:
            raise RuntimeError(
                f"Embedding dimension mismatch: expected {self.expected_dimension}, got {len(vec_list)}"
            )

        # Ensure strict L2 normalization
        vec_list = self._normalize_vector(vec_list)
        return vec_list

    def generate_candidate_embedding(self, profile: CandidateProfile) -> list[float]:
        """
        Format CandidateProfile facts and generate embedding vector.

        :param profile: CandidateProfile instance.
        :return: L2-normalized vector.
        :raises ValueError: If profile contains no embeddable facts.
        """
        text = format_candidate_profile_text(profile)
        if not text:
            raise ValueError("CandidateProfile contains no embeddable text content.")
        return self.generate_embedding(text)

    def generate_job_embedding(self, job: Job) -> list[float]:
        """
        Format Job instance and generate embedding vector.

        :param job: Job ORM model instance.
        :return: L2-normalized vector.
        :raises ValueError: If job contains no embeddable text content.
        """
        text = format_job_text(job)
        if not text:
            raise ValueError("Job contains no embeddable text content.")
        return self.generate_embedding(text)
