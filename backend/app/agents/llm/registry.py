import logging
import threading
from typing import Callable, Dict, List

from app.agents.llm.base import BaseLLMProvider
from app.agents.llm.enums import ProviderType
from app.agents.llm.gemini import GeminiProvider
from app.agents.llm.mock import MockLLMProvider

logger = logging.getLogger("agentflow.llm.registry")


class ProviderRegistry:
    """Thread-safe Enterprise Provider Registry featuring Lazy Initialization of LLM Providers."""

    def __init__(self) -> None:
        self._factories: Dict[ProviderType, Callable[[], BaseLLMProvider]] = {}
        self._instances: Dict[ProviderType, BaseLLMProvider] = {}
        self._lock = threading.Lock()
        self._register_default_factories()

    def _register_default_factories(self) -> None:
        self.register_factory(ProviderType.GEMINI, lambda: GeminiProvider())
        self.register_factory(ProviderType.MOCK, lambda: MockLLMProvider())

    def register_factory(
        self, provider_type: ProviderType | str, factory_fn: Callable[[], BaseLLMProvider]
    ) -> None:
        key = ProviderType.from_str(str(provider_type)) if isinstance(provider_type, str) else provider_type
        with self._lock:
            self._factories[key] = factory_fn
            if key in self._instances:
                del self._instances[key]
            logger.info(f"Registered lazy provider factory in ProviderRegistry: {key.value}")

    def register_instance(
        self, provider_type: ProviderType | str, provider_instance: BaseLLMProvider
    ) -> None:
        key = ProviderType.from_str(str(provider_type)) if isinstance(provider_type, str) else provider_type
        with self._lock:
            self._instances[key] = provider_instance
            logger.info(f"Registered pre-built provider instance in ProviderRegistry: {key.value}")

    def get(self, provider_type: ProviderType | str) -> BaseLLMProvider:
        key = ProviderType.from_str(str(provider_type)) if isinstance(provider_type, str) else provider_type

        with self._lock:
            if key in self._instances:
                return self._instances[key]

            if key in self._factories:
                logger.info(f"Lazily instantiating provider: {key.value}")
                instance = self._factories[key]()
                self._instances[key] = instance
                return instance

            raise KeyError(
                f"Provider '{key.value}' is not registered in ProviderRegistry. Available: {[p.value for p in self._factories.keys()]}"
            )

    def has(self, provider_type: ProviderType | str) -> bool:
        key = ProviderType.from_str(str(provider_type)) if isinstance(provider_type, str) else provider_type
        with self._lock:
            return key in self._instances or key in self._factories

    def get_active_instances(self) -> List[BaseLLMProvider]:
        """Returns list of already-instantiated provider objects without triggering lazy loading for unused factories."""
        with self._lock:
            return list(self._instances.values())


provider_registry = ProviderRegistry()
