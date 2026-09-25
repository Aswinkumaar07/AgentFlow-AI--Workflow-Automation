import logging
import threading
from typing import Callable, Dict
from app.agents.api_discovery.embeddings.base import BaseEmbeddingProvider
from app.agents.api_discovery.embeddings.providers import (
    GeminiEmbeddingProvider,
    LocalEmbeddingProvider,
    OpenAIEmbeddingProvider,
)

logger = logging.getLogger("agentflow.api_discovery.embeddings.registry")


class EmbeddingRegistry:
    """Thread-safe Registry for managing Embedding Providers using the Strategy Pattern."""

    def __init__(self) -> None:
        self._providers: Dict[str, BaseEmbeddingProvider] = {}
        self._lock = threading.Lock()
        self._register_default_providers()

    def _register_default_providers(self) -> None:
        self.register("local", LocalEmbeddingProvider())
        self.register("openai", OpenAIEmbeddingProvider())
        self.register("gemini", GeminiEmbeddingProvider())

    def register(self, name: str, provider: BaseEmbeddingProvider) -> None:
        with self._lock:
            self._providers[name.lower()] = provider
            logger.info(f"Registered EmbeddingProvider: [{name.lower()}]")

    def get(self, name: str) -> BaseEmbeddingProvider:
        key = name.lower()
        with self._lock:
            if key not in self._providers:
                logger.warning(f"EmbeddingProvider '{key}' not found. Falling back to 'local'.")
                return self._providers.get("local", LocalEmbeddingProvider())
            return self._providers[key]


embedding_registry = EmbeddingRegistry()
