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


def test_detect_country_indeed():
    from app.adapters.jobspy_adapter import detect_country_indeed
    assert detect_country_indeed("Bengaluru, India") == "india"
    assert detect_country_indeed("Mumbai, MH") == "india"
    assert detect_country_indeed("New York, NY, USA") == "USA"
    assert detect_country_indeed("London, UK") == "UK"
    assert detect_country_indeed(None) == "india"
    assert detect_country_indeed("Remote") == "india"


def test_sanitize_location_and_remote():
    from app.adapters.jobspy_adapter import sanitize_location_and_remote
    # Pure 'Remote' as location maps geographic location to India and is_remote to True
    loc, is_rem = sanitize_location_and_remote("Remote", None)
    assert loc == "India"
    assert is_rem is True

    # 'Remote, India'
    loc, is_rem = sanitize_location_and_remote("Remote, India", None)
    assert loc == "India"
    assert is_rem is True

    # City with Remote note
    loc, is_rem = sanitize_location_and_remote("Bengaluru (Remote)", None)
    assert loc == "Bengaluru"
    assert is_rem is True

    # Onsite city
    loc, is_rem = sanitize_location_and_remote("Mumbai", False)
    assert loc == "Mumbai"
    assert is_rem is False


def test_normalize_job_type():
    from app.adapters.jobspy_adapter import normalize_job_type
    assert normalize_job_type("full-time") == "fulltime"
    assert normalize_job_type("Full Time") == "fulltime"
    assert normalize_job_type("contract") == "contract"
    assert normalize_job_type("part-time") == "parttime"
    assert normalize_job_type("internship") == "internship"
    assert normalize_job_type("unknown-type") is None


@pytest.mark.anyio
async def test_jobspy_adapter_forwards_clean_location_and_remote():
    mock_df = pd.DataFrame([
        {
            "id": "1",
            "site": "indeed",
            "title": "Engineer",
            "company": "Tech Co",
            "location": "Bengaluru, India",
            "is_remote": True,
        }
    ])

    with patch("jobspy.scrape_jobs", return_value=mock_df) as mock_scrape:
        adapter = JobSpyJobSourceAdapter(search_term="Python", location="Remote", is_remote=None)
        await adapter.fetch_jobs(limit=5)

        # Confirm scrape_jobs was called with clean location 'India' and is_remote=True, NOT location='Remote'
        call_kwargs = mock_scrape.call_args.kwargs
        assert call_kwargs["location"] == "India"
        assert call_kwargs["is_remote"] is True
        assert call_kwargs["country_indeed"] == "india"


