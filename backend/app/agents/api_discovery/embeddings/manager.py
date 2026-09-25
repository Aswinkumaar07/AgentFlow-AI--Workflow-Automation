import logging
from typing import List, Optional
from app.agents.api_discovery.config import discovery_config
from app.agents.api_discovery.embeddings.base import BaseEmbeddingProvider
from app.agents.api_discovery.embeddings.registry import embedding_registry

logger = logging.getLogger("agentflow.api_discovery.embeddings.manager")


class EmbeddingManager:
    """Strategy Engine for dynamic resolution of active Embedding Providers."""

    def __init__(self) -> None:
        self._registry = embedding_registry

    def get_active_provider(self, provider_name: Optional[str] = None) -> BaseEmbeddingProvider:
        target = provider_name or discovery_config.EMBEDDING_PROVIDER
        return self._registry.get(target)

    async def generate_embedding(self, text: str, provider_name: Optional[str] = None) -> List[float]:
        provider = self.get_active_provider(provider_name)
        return await provider.generate_embedding(text)

    async def generate_batch(self, texts: List[str], provider_name: Optional[str] = None) -> List[List[float]]:
        provider = self.get_active_provider(provider_name)
        return await provider.generate_batch(texts)


embedding_manager = EmbeddingManager()
