import pytest
import httpx
from datetime import datetime, timezone
from app.adapters.lever_adapter import LeverJobSourceAdapter, _clean_html


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_clean_html_lever():
    html = "<div><p>Lead our engineering pods.</p></div>"
    assert "Lead our engineering pods." in _clean_html(html)


@pytest.mark.anyio
async def test_lever_adapter_fetch_success(monkeypatch):
    mock_payload = [
        {
            "id": "lever-uuid-1",
            "text": "Machine Learning Engineer",
            "categories": {
                "location": "New York, NY",
                "team": "Search",
                "commitment": "Full time",
            },
            "workplaceType": "remote",
            "createdAt": 1792767640000,
            "hostedUrl": "https://jobs.lever.co/spotify/lever-uuid-1",
            "applyUrl": "https://jobs.lever.co/spotify/lever-uuid-1/apply",
            "description": "<p>Build high-throughput ML pipelines.</p>",
            "lists": [
                {
                    "text": "Requirements",
                    "content": "<li>5+ years Python and PyTorch</li>",
                }
            ],
        }
    ]

    class MockResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return mock_payload

    async def mock_get(self, url, *args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = LeverJobSourceAdapter(slugs=["spotify"])
    assert adapter.source_name == "lever"

    jobs = await adapter.fetch_jobs(limit=1)
    assert len(jobs) == 1
    job = jobs[0]
    assert job["source"] == "lever"
    assert job["external_id"] == "lever-uuid-1"
    assert job["title"] == "Machine Learning Engineer"
    assert job["company"] == "Spotify"
    assert job["location"] == "New York, NY"
    assert job["is_remote"] is True
    assert job["source_url"] == "https://jobs.lever.co/spotify/lever-uuid-1"
    assert job["apply_url"] == "https://jobs.lever.co/spotify/lever-uuid-1/apply"
    assert job["posted_at"] == datetime.fromtimestamp(1792767640, tz=timezone.utc)
    assert "Build high-throughput ML pipelines." in job["raw_description"]
    assert "Requirements:" in job["raw_description"]
    assert "5+ years Python and PyTorch" in job["raw_description"]


@pytest.mark.anyio
async def test_lever_adapter_handles_404_gracefully(monkeypatch):
    class Mock404Response:
        status_code = 404

        def raise_for_status(self):
            raise httpx.HTTPStatusError("404 Not Found", request=None, response=self)

        def json(self):
            return {}

    async def mock_get(self, url, *args, **kwargs):
        return Mock404Response()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = LeverJobSourceAdapter(slugs=["unknown-lever-slug"])
    jobs = await adapter.fetch_jobs()
    assert jobs == []
