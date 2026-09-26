"""Simple in-memory sliding-window rate limiter for expensive endpoints.

Suitable for a single-process prototype; swap for a shared store (e.g. Redis) when scaling out.
"""

import threading
import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, status

from app.config import Settings, get_settings
from app.security.auth import AuthenticatedUser, get_current_user


class SlidingWindowLimiter:
    def __init__(self, window_seconds: int = 60) -> None:
        self._window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int) -> bool:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self._window:
                hits.popleft()
            if len(hits) >= limit:
                return False
            hits.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = SlidingWindowLimiter()


def rate_limited(scope: str):
    """Dependency factory: limits authenticated users per scope per minute."""

    def dependency(
        user: AuthenticatedUser = Depends(get_current_user),
        settings: Settings = Depends(get_settings),
    ) -> AuthenticatedUser:
        if not limiter.allow(f"{scope}:{user.id}", settings.rate_limit_per_minute):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "RATE_LIMITED", "message": "Too many requests. Please wait a moment and try again."},
            )
        return user

    return dependency
