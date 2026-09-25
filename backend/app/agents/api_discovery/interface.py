from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseAPIDiscoveryService(ABC):
    """
    Abstract Interface for Automated API Discovery & Schema Parsing.
    
    TODO: Plug in OpenAPI / Swagger parser & semantic vector search for API discovery.
    """

    @abstractmethod
    async def discover_endpoints(self, query: str) -> List[Dict[str, Any]]:
        """
        Search vector database or OpenAPI registry for endpoints matching functional requirements.
        """
        pass

    @abstractmethod
    async def parse_openapi_spec(self, spec_url_or_json: str) -> Dict[str, Any]:
        """
        Parse and index raw OpenAPI spec into standardized tool schemas for AI agents.
        """
        pass
