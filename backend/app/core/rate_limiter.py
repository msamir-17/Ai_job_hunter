"""
Rate Limiting Middleware / Dependency.
Provides sliding-window in-memory rate limiting per client IP or user identity.
"""
import time
import asyncio
from typing import Dict, List
from fastapi import Request, HTTPException, status


class SlidingWindowRateLimiter:
    """
    Sliding-window rate limiter storing request timestamps per identifier key.
    Automatically purges expired timestamps outside the rolling window.
    """

    def __init__(self, requests_limit: int = 10, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self._history: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()

    def _clean_old_requests(self, now: float, key: str) -> None:
        threshold = now - self.window_seconds
        if key in self._history:
            self._history[key] = [t for t in self._history[key] if t > threshold]
            if not self._history[key]:
                del self._history[key]

    async def check(self, key: str) -> None:
        async with self._lock:
            now = time.time()
            self._clean_old_requests(now, key)
            timestamps = self._history.get(key, [])
            if len(timestamps) >= self.requests_limit:
                earliest = timestamps[0]
                retry_after = max(1, int(self.window_seconds - (now - earliest)))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {self.requests_limit} requests per {self.window_seconds}s. Try again in {retry_after}s.",
                    headers={"Retry-After": str(retry_after)},
                )
            if key not in self._history:
                self._history[key] = []
            self._history[key].append(now)

    def reset(self) -> None:
        """Reset all tracked history (useful for unit tests)."""
        self._history.clear()


# Default limiter for resume upload endpoints (10 requests per minute)
upload_limiter = SlidingWindowRateLimiter(requests_limit=10, window_seconds=60)


async def check_upload_rate_limit(request: Request) -> None:
    """
    FastAPI dependency to rate-limit uploads by client IP.
    """
    client_ip = request.client.host if request.client else "unknown_client"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    await upload_limiter.check(client_ip)
