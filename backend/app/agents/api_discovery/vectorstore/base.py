from abc import ABC, abstractmethod
from typing import List, Optional
from app.agents.api_discovery.models import EndpointMetadataModel


class BaseVectorStoreProvider(ABC):
    """Abstract Interface for Vector Database Backends (Qdrant, pgvector, Pinecone, Chroma, FAISS, Memory)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns string name of the vector database provider."""
        raise NotImplementedError

    @abstractmethod
    async def add_endpoints(self, endpoints: List[EndpointMetadataModel], tenant_id: str = "default") -> None:
        """Indexes endpoint metadata models into tenant-isolated vector store."""
        raise NotImplementedError

    @abstractmethod
    async def search_vectors(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter_providers: Optional[List[str]] = None,
        tenant_id: str = "default",
    ) -> List[EndpointMetadataModel]:
        """Performs vector similarity search over tenant vector space."""
        raise NotImplementedError
