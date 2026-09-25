from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from app.agents.api_discovery.models import (
    APICapabilityNode,
    APIQueryFilter,
    APIRecommendationModel,
    EndpointMetadataModel,
)


class BaseAPIDiscoveryService(ABC):
    """Abstract Interface for Automated API Discovery Engine."""

    @abstractmethod
    async def discover_endpoints(self, query: str, target_providers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Searches repository and returns ranked endpoint candidate dictionaries."""
        raise NotImplementedError

    @abstractmethod
    async def discover_for_plan(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discovers endpoints for an entire execution plan structure."""
        raise NotImplementedError

    @abstractmethod
    async def parse_openapi_spec(self, spec_url_or_json: Any) -> Dict[str, Any]:
        """Parses raw OpenAPI/Swagger spec dictionary into endpoint models."""
        raise NotImplementedError


class BaseEmbeddingGenerator(ABC):
    """Interface for generating text vector embeddings."""

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generates a float vector for a given text input."""
        raise NotImplementedError

    @abstractmethod
    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates float vectors for a batch of text inputs."""
        raise NotImplementedError


class BaseVectorStore(ABC):
    """Interface for Vector Database operations."""

    @abstractmethod
    async def add_endpoints(self, endpoints: List[EndpointMetadataModel]) -> None:
        """Indexes endpoint metadata models with vector embeddings."""
        raise NotImplementedError

    @abstractmethod
    async def search_vectors(
        self, query_vector: List[float], top_k: int = 10, filter_providers: Optional[List[str]] = None
    ) -> List[EndpointMetadataModel]:
        """Performs vector similarity search returning nearest endpoint models."""
        raise NotImplementedError


class BaseSpecParser(ABC):
    """Interface for parsing API specifications."""

    @abstractmethod
    def parse_spec(self, raw_content: Any, format_hint: Optional[str] = None) -> List[EndpointMetadataModel]:
        """Parses OpenAPI 3.x, Swagger 2.0, Postman Collection, AsyncAPI, or YAML/JSON spec."""
        raise NotImplementedError


class BaseCapabilityGraph(ABC):
    """Interface for managing the Provider Capability Graph."""

    @abstractmethod
    def add_node(self, node: APICapabilityNode) -> None:
        """Adds a capability node to the graph."""
        raise NotImplementedError

    @abstractmethod
    def add_transition(self, source_node_id: str, target_node_id: str, operation_id: str) -> None:
        """Adds a directed transition link between capability nodes."""
        raise NotImplementedError

    @abstractmethod
    def find_path(self, source_entity: str, target_entity: str) -> List[Dict[str, Any]]:
        """Finds multi-step execution paths connecting source entity to target entity."""
        raise NotImplementedError


class BaseHybridRanker(ABC):
    """Interface for hybrid ranking of candidate API endpoints."""

    @abstractmethod
    def rank(
        self, candidates: List[EndpointMetadataModel], query: str, query_vector: List[float]
    ) -> List[EndpointMetadataModel]:
        """Ranks candidate endpoints using vector similarity, BM25, popularity, health, and latency."""
        raise NotImplementedError


class BaseRecommendationEngine(ABC):
    """Interface for generating API recommendations."""

    @abstractmethod
    def recommend_alternatives(
        self, target_endpoint: EndpointMetadataModel, catalog: List[EndpointMetadataModel]
    ) -> List[APIRecommendationModel]:
        """Recommends cheaper, faster, or more reliable alternative APIs."""
        raise NotImplementedError


class BaseEnterpriseCache(ABC):
    """Interface for Enterprise Caching Layer."""

    @abstractmethod
    async def get(self, key: str) -> Optional[List[Dict[str, Any]]]:
        raise NotImplementedError

    @abstractmethod
    async def set(self, key: str, value: List[Dict[str, Any]], ttl_seconds: int = 3600) -> bool:
        raise NotImplementedError
