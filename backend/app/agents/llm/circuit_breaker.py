import logging
import threading
import time
from enum import Enum
from typing import Any, Dict

logger = logging.getLogger("agentflow.llm.circuit_breaker")


class CircuitState(str, Enum):
    """Circuit Breaker States."""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    """Thread-safe Enterprise Circuit Breaker for monitoring LLM Provider failures."""

    def __init__(self, threshold: int = 3, cooldown_seconds: float = 60.0):
        self.threshold = threshold
        self.cooldown_seconds = cooldown_seconds
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self._lock = threading.Lock()

    def allow_execution(self) -> bool:
        """Determines whether execution should be permitted in a thread-safe manner."""
        with self._lock:
            now = time.monotonic()

            if self.state == CircuitState.CLOSED:
                return True

            if self.state == CircuitState.OPEN:
                if now - self.last_failure_time >= self.cooldown_seconds:
                    logger.info("CircuitBreaker entering HALF_OPEN trial state.")
                    self.state = CircuitState.HALF_OPEN
                    return True
                return False

            if self.state == CircuitState.HALF_OPEN:
                return True

            return False

    def record_success(self) -> None:
        """Records a successful operation in a thread-safe manner."""
        with self._lock:
            if self.state != CircuitState.CLOSED:
                logger.info("CircuitBreaker recovered. Resetting state to CLOSED.")
            self.failure_count = 0
            self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Records a failure operation in a thread-safe manner."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.monotonic()

            if self.failure_count >= self.threshold:
                if self.state != CircuitState.OPEN:
                    logger.warning(
                        f"CircuitBreaker tripped OPEN after {self.failure_count} consecutive failures. Cooldown: {self.cooldown_seconds}s"
                    )
                self.state = CircuitState.OPEN

    def to_dict(self) -> Dict[str, Any]:
        """Serializes current circuit state safely."""
        with self._lock:
            now = time.monotonic()
            seconds_left = max(0.0, round(self.cooldown_seconds - (now - self.last_failure_time), 1)) if self.state == CircuitState.OPEN else 0.0
            return {
                "state": self.state.value,
                "failure_count": self.failure_count,
                "threshold": self.threshold,
                "cooldown_seconds": self.cooldown_seconds,
                "seconds_until_retry": seconds_left,
            }
