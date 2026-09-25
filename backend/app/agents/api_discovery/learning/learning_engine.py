import logging
import threading
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("agentflow.api_discovery.learning")


class WorkflowLearningEngine:
    """Enterprise Workflow Learning & Provider Health Intelligence Engine.

    Tracks real-time execution statistics (success, failure, latency, 429 rate, user acceptance)
    and dynamically feeds health adjustments back into the Hybrid Ranking Engine.
    """

    def __init__(self) -> None:
        self._provider_health: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def record_execution(
        self,
        provider: str,
        operation_id: str,
        latency_ms: float,
        success: bool = True,
        status_code: int = 200,
        user_accepted: bool = True,
    ) -> None:
        with self._lock:
            p_key = provider.lower()
            if p_key not in self._provider_health:
                self._provider_health[p_key] = {
                    "total_requests": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "rate_limit_count": 0,
                    "total_latency_ms": 0.0,
                    "user_accepted_count": 0,
                    "last_updated": time.time(),
                }

            stats = self._provider_health[p_key]
            stats["total_requests"] += 1
            stats["total_latency_ms"] += latency_ms
            stats["last_updated"] = time.time()

            if success:
                stats["success_count"] += 1
            else:
                stats["failure_count"] += 1

            if status_code == 429:
                stats["rate_limit_count"] += 1

            if user_accepted:
                stats["user_accepted_count"] += 1

            logger.info(f"Recorded learning feedback for [{provider}.{operation_id}]: success={success}, latency={latency_ms}ms")

    def get_health_score(self, provider: str) -> float:
        with self._lock:
            p_key = provider.lower()
            if p_key not in self._provider_health:
                return 0.98

            stats = self._provider_health[p_key]
            total = stats["total_requests"]
            if total == 0:
                return 0.98

            success_rate = stats["success_count"] / total
            rate_limit_penalty = (stats["rate_limit_count"] / total) * 0.3
            health = max(0.1, min(1.0, success_rate - rate_limit_penalty))
            return round(health, 2)


learning_engine = WorkflowLearningEngine()
