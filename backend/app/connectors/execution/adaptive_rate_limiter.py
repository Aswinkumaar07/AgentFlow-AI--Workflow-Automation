import asyncio
import logging
import time
from typing import Dict, List

logger = logging.getLogger("agentflow.connectors.execution.rate_limiter")


class AdaptiveRateLimiter:
    """Enterprise Sliding-Window Dynamic Rate Limiter with per-provider quota tracking & burst handling."""

    def __init__(self) -> None:
        self._provider_quotas: Dict[str, int] = {
            "gmail": 250,
            "google drive": 1000,
            "slack": 60,
            "github": 5000,
            "stripe": 100,
            "generic rest api": 10000,
        }
        self._requests: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, provider: str) -> None:
        """Acquires rate limit permit, delaying execution if quota exceeded."""
        p_key = provider.lower()
        max_quota = self._provider_quotas.get(p_key, 100)

        async with self._lock:
            now = time.time()
            if p_key not in self._requests:
                self._requests[p_key] = []

            # Filter requests within past 60 seconds
            self._requests[p_key] = [t for t in self._requests[p_key] if now - t < 60.0]

            if len(self._requests[p_key]) >= max_quota:
                sleep_time = 60.0 - (now - self._requests[p_key][0])
                logger.warning(f"Rate limit hit for provider [{provider}]. Throttling execution for {sleep_time:.2f}s...")
                await asyncio.sleep(max(0.1, sleep_time))

            self._requests[p_key].append(time.time())


adaptive_rate_limiter = AdaptiveRateLimiter()
