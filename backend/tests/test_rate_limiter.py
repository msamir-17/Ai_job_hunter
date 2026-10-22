import pytest
from fastapi import HTTPException
from app.core.rate_limiter import SlidingWindowRateLimiter, upload_limiter


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_sliding_window_rate_limiter_allows_under_limit():
    limiter = SlidingWindowRateLimiter(requests_limit=3, window_seconds=10)
    # 3 requests should succeed
    await limiter.check("test_client_1")
    await limiter.check("test_client_1")
    await limiter.check("test_client_1")


@pytest.mark.anyio
async def test_sliding_window_rate_limiter_blocks_over_limit():
    limiter = SlidingWindowRateLimiter(requests_limit=2, window_seconds=10)
    await limiter.check("test_client_2")
    await limiter.check("test_client_2")
    
    with pytest.raises(HTTPException) as exc_info:
        await limiter.check("test_client_2")
    
    assert exc_info.value.status_code == 429
    assert "Rate limit exceeded" in exc_info.value.detail
    assert "Retry-After" in exc_info.value.headers


@pytest.mark.anyio
async def test_sliding_window_rate_limiter_isolates_keys():
    limiter = SlidingWindowRateLimiter(requests_limit=1, window_seconds=10)
    await limiter.check("client_a")
    
    # client_b should succeed even though client_a is exhausted
    await limiter.check("client_b")
    
    # client_a should fail
    with pytest.raises(HTTPException):
        await limiter.check("client_a")


@pytest.mark.anyio
async def test_sliding_window_rate_limiter_reset():
    limiter = SlidingWindowRateLimiter(requests_limit=1, window_seconds=10)
    await limiter.check("client_reset")
    with pytest.raises(HTTPException):
        await limiter.check("client_reset")
    
    limiter.reset()
    # After reset, it should pass again
    await limiter.check("client_reset")
