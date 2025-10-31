"""Concurrency control helpers for network scanning."""

from __future__ import annotations

import asyncio
from typing import Awaitable, Optional, TypeVar

T = TypeVar("T")


class RateLimiter:
    """Async semaphore-based rate limiter with timeout enforcement."""

    _MAX_CONCURRENCY = 50

    def __init__(self, max_concurrency: int = 10, timeout: float = 10.0) -> None:
        if not 1 <= max_concurrency <= self._MAX_CONCURRENCY:
            raise ValueError(
                f"max_concurrency must be between 1 and {self._MAX_CONCURRENCY}"
            )
        if timeout <= 0:
            raise ValueError("timeout must be positive")

        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._timeout = timeout
        self._capacity = max_concurrency

    @property
    def timeout(self) -> float:
        return self._timeout

    @property
    def max_concurrency(self) -> int:
        return self._capacity

    async def __aenter__(self) -> "RateLimiter":
        await self._semaphore.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self._semaphore.release()

    async def execute(
        self, coro: Awaitable[T], *, timeout: Optional[float] = None
    ) -> T:
        """Run the provided coroutine under concurrency and timeout constraints."""

        async with self:
            effective_timeout = timeout if timeout is not None else self._timeout
            return await asyncio.wait_for(coro, timeout=effective_timeout)


__all__ = ["RateLimiter"]
