from __future__ import annotations

import asyncio
import time
import unittest

from iptv_sniffer.scanner.rate_limiter import RateLimiter


class RateLimiterTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_rate_limiter_respects_concurrency_limit(self) -> None:
        limiter = RateLimiter(max_concurrency=2, timeout=1)
        active = 0
        peak = 0

        async def task(duration: float) -> None:
            nonlocal active, peak
            async with limiter:
                active += 1
                peak = max(peak, active)
                await asyncio.sleep(duration)
                active -= 1

        await asyncio.gather(*(task(0.1) for _ in range(5)))
        self.assertLessEqual(peak, 2)

    async def test_rate_limiter_execute_applies_timeout(self) -> None:
        limiter = RateLimiter(max_concurrency=1, timeout=0.05)

        with self.assertRaises(asyncio.TimeoutError):
            await limiter.execute(asyncio.sleep(0.2))

    def test_rate_limiter_rejects_invalid_concurrency(self) -> None:
        with self.assertRaises(ValueError):
            RateLimiter(max_concurrency=0)
        with self.assertRaises(ValueError):
            RateLimiter(max_concurrency=51)

    async def test_rate_limiter_execute_custom_timeout(self) -> None:
        limiter = RateLimiter(max_concurrency=1, timeout=1)
        start = time.perf_counter()
        with self.assertRaises(asyncio.TimeoutError):
            await limiter.execute(asyncio.sleep(0.2), timeout=0.05)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.2)


if __name__ == "__main__":
    unittest.main()
