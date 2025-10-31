"""Scan orchestration utilities coordinating strategies and validation."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import AsyncIterator, Awaitable, Callable, List, Optional

from .rate_limiter import RateLimiter
from .strategy import ScanStrategy
from .validator import StreamValidationResult, StreamValidator

from pydantic import BaseModel, Field

ProgressCallback = Callable[["ScanProgress"], Awaitable[None]]


class ScanProgress(BaseModel):
    """Represents incremental scan statistics."""

    total: int
    completed: int = 0
    valid: int = 0
    invalid: int = 0
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = dict(arbitrary_types_allowed=True)


class ScanOrchestrator:
    """Coordinates scanning strategy execution with rate limiting and validation."""

    def __init__(
        self,
        validator: StreamValidator,
        *,
        max_concurrency: int = 10,
        rate_limiter: Optional[RateLimiter] = None,
    ) -> None:
        self._validator = validator
        self._rate_limiter = rate_limiter or RateLimiter(
            max_concurrency=max_concurrency
        )
        self._callbacks: List[ProgressCallback] = []

    def on_progress(self, callback: ProgressCallback) -> None:
        """Register an async callback invoked after each validation result."""

        self._callbacks.append(callback)

    async def execute_scan(
        self, strategy: ScanStrategy
    ) -> AsyncIterator[StreamValidationResult]:
        """Run scan strategy and yield validation results as they arrive."""

        total = strategy.estimate_target_count()
        progress = ScanProgress(total=total)

        async for url in strategy.generate_targets():
            result = await self._rate_limiter.execute(self._validator.validate(url))

            progress.completed += 1
            if result.is_valid:
                progress.valid += 1
            else:
                progress.invalid += 1

            await self._dispatch_progress(progress)
            yield result

    async def _dispatch_progress(self, progress: ScanProgress) -> None:
        if not self._callbacks:
            return
        await asyncio.gather(*(callback(progress) for callback in self._callbacks))


__all__ = ["ScanOrchestrator", "ScanProgress"]
