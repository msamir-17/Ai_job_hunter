import asyncio
from datetime import date, datetime, timezone
from unittest.mock import patch
import pandas as pd
import pytest

from app.adapters.jobspy_adapter import JobSpyJobSourceAdapter


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_jobspy_adapter_normalization():
    mock_df = pd.DataFrame([
        {
            "id": "li-12345",
            "site": "linkedin",
            "job_url": "https://www.linkedin.com/jobs/view/12345",
            "job_url_direct": "https://boards.greenhouse.io/stripe/jobs/12345",
            "title": "Senior AI Infrastructure Engineer",
            "company": "Stripe",
            "location": "Remote, USA",
            "is_remote": True,
            "min_amount": 160000.0,
            "max_amount": 210000.0,
            "date_posted": date(2026, 10, 20),
            "description": "Lead planetary scale AI workloads.",
        },
        {
            "id": "in-67890",
            "site": "indeed",
            "job_url": "https://www.indeed.com/viewjob?jk=67890",
            "job_url_direct": None,
            "title": "Backend Python Developer",
            "company": "Datatech Inc",
            "location": "New York, NY",
            "is_remote": False,
            "min_amount": 120000.0,
            "max_amount": 150000.0,
            "date_posted": "2026-10-22",
            "description": "FastAPI and PostgreSQL microservices.",
        },
    ])

    with patch("jobspy.scrape_jobs", return_value=mock_df):
        adapter = JobSpyJobSourceAdapter(search_term="Python", location="Remote")
        assert adapter.source_name == "jobspy"

        jobs = await adapter.fetch_jobs(limit=10)
        assert len(jobs) == 2

        # Check LinkedIn row
        j1 = jobs[0]
        assert j1["source"] == "linkedin"
        assert j1["external_id"] == "li-12345"
        assert j1["title"] == "Senior AI Infrastructure Engineer"
        assert j1["company"] == "Stripe"
        assert j1["apply_url"] == "https://boards.greenhouse.io/stripe/jobs/12345"
        assert j1["source_url"] == "https://www.linkedin.com/jobs/view/12345"
        assert j1["is_remote"] is True
        assert j1["salary_min"] == 160000
        assert j1["salary_max"] == 210000
        assert j1["posted_at"] == datetime(2026, 10, 20, 0, 0, 0, tzinfo=timezone.utc)

        # Check Indeed row
        j2 = jobs[1]
        assert j2["source"] == "indeed"
        assert j2["external_id"] == "in-67890"
        assert j2["title"] == "Backend Python Developer"
        assert j2["company"] == "Datatech Inc"
        assert j2["apply_url"] == "https://www.indeed.com/viewjob?jk=67890"
        assert j2["is_remote"] is False


@pytest.mark.anyio
async def test_jobspy_adapter_handles_empty_or_failure():
    with patch("jobspy.scrape_jobs", side_effect=Exception("Scraping rate limit / blocked")):
        adapter = JobSpyJobSourceAdapter()
        jobs = await adapter.fetch_jobs(limit=5)
        assert jobs == []
