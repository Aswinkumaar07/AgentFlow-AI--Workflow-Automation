import logging
from typing import List, Optional
from app.agents.api_discovery.interfaces import BaseVectorStore
from app.agents.api_discovery.models import EndpointMetadataModel
from app.agents.api_discovery.vectorstore.providers.memory_provider import MemoryVectorStoreProvider

logger = logging.getLogger("agentflow.api_discovery.vectorstore")


class VectorStore(BaseVectorStore):
    """Distributed Vector Store facade routing to configured Vector Database backend."""

    def __init__(self) -> None:
        self._provider = MemoryVectorStoreProvider()

    async def add_endpoints(self, endpoints: List[EndpointMetadataModel], tenant_id: str = "default") -> None:
        await self._provider.add_endpoints(endpoints, tenant_id=tenant_id)

    async def search_vectors(
        self, query_vector: List[float], top_k: int = 10, filter_providers: Optional[List[str]] = None, tenant_id: str = "default"
    ) -> List[EndpointMetadataModel]:
        return await self._provider.search_vectors(query_vector, top_k=top_k, filter_providers=filter_providers, tenant_id=tenant_id)
