import pytest
import httpx
from datetime import datetime, timezone
from app.adapters.greenhouse_adapter import GreenhouseJobSourceAdapter, _clean_html


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_clean_html_removes_tags_and_scripts():
    html = """
    <div>
        <h3>About the Role</h3>
        <script>console.log('secret');</script>
        <p>We are looking for a <strong>Senior Engineer</strong>.</p>
        <style>.foo { color: red; }</style>
    </div>
    """
    cleaned = _clean_html(html)
    assert "About the Role" in cleaned
    assert "Senior Engineer" in cleaned
    assert "console.log" not in cleaned
    assert ".foo" not in cleaned


@pytest.mark.anyio
async def test_greenhouse_adapter_fetch_success(monkeypatch):
    mock_payload = {
        "jobs": [
            {
                "id": 12345,
                "title": "Staff Backend Engineer",
                "location": {"name": "Remote, US"},
                "absolute_url": "https://boards.greenhouse.io/stripe/jobs/12345",
                "first_published": "2026-10-20T12:00:00Z",
                "content": "<p>Build scalable financial infrastructure.</p>",
            },
            {
                "id": 67890,
                "title": "Product Designer",
                "location": {"name": "San Francisco, CA"},
                "absolute_url": "https://boards.greenhouse.io/stripe/jobs/67890",
                "first_published": None,
                "content": "<p>Design intuitive user experiences.</p>",
            },
        ]
    }

    class MockResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return mock_payload

    async def mock_get(self, url, *args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = GreenhouseJobSourceAdapter(slugs=["stripe"])
    assert adapter.source_name == "greenhouse"

    jobs = await adapter.fetch_jobs(limit=1)
    assert len(jobs) == 1
    job = jobs[0]
    assert job["source"] == "greenhouse"
    assert job["external_id"] == "12345"
    assert job["title"] == "Staff Backend Engineer"
    assert job["company"] == "Stripe"
    assert job["location"] == "Remote, US"
    assert job["is_remote"] is True
    assert job["source_url"] == "https://boards.greenhouse.io/stripe/jobs/12345"
    assert job["apply_url"] == "https://boards.greenhouse.io/stripe/jobs/12345"
    assert job["posted_at"] == datetime(2026, 10, 20, 12, 0, 0, tzinfo=timezone.utc)
    assert "Build scalable financial infrastructure." in job["raw_description"]


@pytest.mark.anyio
async def test_greenhouse_adapter_handles_404_gracefully(monkeypatch):
    class Mock404Response:
        status_code = 404

        def raise_for_status(self):
            raise httpx.HTTPStatusError("404 Not Found", request=None, response=self)

        def json(self):
            return {}

    async def mock_get(self, url, *args, **kwargs):
        return Mock404Response()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = GreenhouseJobSourceAdapter(slugs=["nonexistent-company-slug-xyz"])
    jobs = await adapter.fetch_jobs()
    assert jobs == []
