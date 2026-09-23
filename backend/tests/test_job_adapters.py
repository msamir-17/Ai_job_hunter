from pathlib import Path
import pytest
from app.adapters.manual import ManualJobSourceAdapter
from app.adapters.remotive import RemotiveJobSourceAdapter


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_manual_adapter_default_jobs():
    adapter = ManualJobSourceAdapter()
    assert adapter.source_name == "manual"

    jobs = await adapter.fetch_jobs()
    assert len(jobs) > 0
    assert jobs[0]["external_id"] == "manual-001"
    assert "AI/ML Engineer" in jobs[0]["title"]


@pytest.mark.anyio
async def test_manual_adapter_respects_limit():
    adapter = ManualJobSourceAdapter()
    jobs = await adapter.fetch_jobs(limit=2)
    assert len(jobs) == 2


@pytest.mark.anyio
async def test_remotive_adapter_load_from_cache():
    # Uses the cache file created in data/raw/remotive_cache.json
    adapter = RemotiveJobSourceAdapter()
    assert adapter.source_name == "remotive"

    jobs = await adapter.fetch_jobs(use_cache=True, limit=2)
    assert len(jobs) == 2
    assert jobs[0]["external_id"] == "1928401"
    assert jobs[0]["title"] == "Senior Python Developer"
    assert jobs[0]["company"] == "DataTech Labs"
    assert jobs[0]["is_remote"] is True
    assert jobs[0]["salary_min"] == 130000
    assert jobs[0]["salary_max"] == 160000


@pytest.mark.anyio
async def test_remotive_adapter_missing_cache_raises_file_not_found():
    non_existent_path = Path("/invalid/path/remotive_cache.json")
    adapter = RemotiveJobSourceAdapter(cache_file_path=non_existent_path)

    with pytest.raises(FileNotFoundError) as exc_info:
        await adapter.fetch_jobs(use_cache=True)

    assert "missing" in str(exc_info.value).lower()
