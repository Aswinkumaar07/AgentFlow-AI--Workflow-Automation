import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.agents.llm.enums import ProviderType
from app.agents.llm.utils import estimate_tokens


class BaseLLMProvider(ABC):
    """Abstract Base Class defining the standard interface, metrics & type identity for all LLM providers."""

    def __init__(self) -> None:
        self.request_count: int = 0
        self.success_count: int = 0
        self.failure_count: int = 0
        self.total_latency_ms: float = 0.0
        self.total_tokens_estimated: int = 0
        self._metrics_lock = threading.Lock()

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Returns explicit ProviderType enum identity for this provider instance."""
        raise NotImplementedError("Subclasses must implement provider_type property")

    def record_execution_metrics(self, prompt: str, response_text: str, duration_ms: float, success: bool = True) -> None:
        """Thread-safe recording of execution statistics for telemetry monitoring."""
        with self._metrics_lock:
            self.request_count += 1
            self.total_latency_ms += duration_ms
            if success:
                self.success_count += 1
                tokens_in = estimate_tokens(prompt)
                tokens_out = estimate_tokens(response_text)
                self.total_tokens_estimated += tokens_in + tokens_out
            else:
                self.failure_count += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Returns thread-safe aggregated telemetry metrics for this provider."""
        with self._metrics_lock:
            avg_latency = (self.total_latency_ms / self.request_count) if self.request_count > 0 else 0.0
            return {
                "provider_type": self.provider_type.value,
                "request_count": self.request_count,
                "success_count": self.success_count,
                "failure_count": self.failure_count,
                "average_latency_ms": round(avg_latency, 2),
                "estimated_token_usage": self.total_tokens_estimated,
            }

    @abstractmethod
    async def health_check(self) -> bool:
        """Performs an asynchronous health ping to check provider availability."""
        raise NotImplementedError("Subclasses must implement health_check()")

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> str:
        """Generates raw text response from the underlying LLM provider."""
        raise NotImplementedError("Subclasses must implement generate_text()")

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generates structured JSON response from the underlying LLM provider."""
        raise NotImplementedError("Subclasses must implement generate_json()")
