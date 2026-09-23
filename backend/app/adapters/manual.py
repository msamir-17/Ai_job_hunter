from typing import Any
from app.adapters.base import BaseJobSourceAdapter

# Sample deterministic raw mock data for testing & development
DEFAULT_MANUAL_JOBS: list[dict[str, Any]] = [
    {
        "external_id": "manual-001",
        "title": " Senior AI/ML Engineer ",
        "company": "TechCorp Innovations",
        "location": "San Francisco, CA (Remote)",
        "is_remote": True,
        "salary_min": 150000,
        "salary_max": 190000,
        "raw_description": "Building next-generation LLM pipelines and RAG agents.",
        "skills_required": ["Python", "PyTorch", "FastAPI", "PostgreSQL", "python"],
        "url": "https://example.com/jobs/manual-001",
    },
    {
        "external_id": "manual-002",
        "title": "Full Stack Developer",
        "company": "Acme Solutions",
        "location": "New York, NY",
        "is_remote": False,
        "salary_min": 120000,
        "salary_max": 150000,
        "raw_description": "React and FastAPI web application development.",
        "skills_required": ["React", "TypeScript", "Python", "TailwindCSS"],
        "url": "https://example.com/jobs/manual-002",
    },
    {
        "external_id": "manual-003",
        "title": "Backend Python Engineer",
        "company": "DataScale Systems",
        "location": "Remote",
        "is_remote": True,
        "salary_min": 130000,
        "salary_max": 160000,
        "raw_description": "High throughput microservices and SQL optimization.",
        "skills_required": ["Python", "SQLAlchemy", "Docker", "PostgreSQL"],
        "url": "https://example.com/jobs/manual-003",
    },
    {
        "external_id": "manual-004",
        "title": "MLOps Specialist",
        "company": "Neural Cloud",
        "location": None,
        "is_remote": True,
        "salary_min": 140000,
        "salary_max": 180000,
        "raw_description": "Deploying deep learning models to production clusters.",
        "skills_required": ["Kubernetes", "Docker", "Python", "MLflow"],
        "url": "https://example.com/jobs/manual-004",
    },
]


class ManualJobSourceAdapter(BaseJobSourceAdapter):
    """
    Manual / In-memory mock adapter for reproducible testing and development.
    """

    def __init__(self, mock_jobs: list[dict[str, Any]] | None = None):
        self._mock_jobs = mock_jobs if mock_jobs is not None else DEFAULT_MANUAL_JOBS

    @property
    def source_name(self) -> str:
        return "manual"

    async def fetch_jobs(self, limit: int | None = None, **kwargs: Any) -> list[dict[str, Any]]:
        """Return deterministic mock jobs up to specified limit."""
        jobs = list(self._mock_jobs)
        if limit is not None and limit > 0:
            jobs = jobs[:limit]
        return jobs
