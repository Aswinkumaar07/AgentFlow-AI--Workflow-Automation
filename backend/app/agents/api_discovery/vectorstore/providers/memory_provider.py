import logging
import math
from typing import Dict, List, Optional
from app.agents.api_discovery.models import EndpointMetadataModel
from app.agents.api_discovery.vectorstore.base import BaseVectorStoreProvider

logger = logging.getLogger("agentflow.api_discovery.vectorstore.memory")


class MemoryVectorStoreProvider(BaseVectorStoreProvider):
    """High-Performance Multi-Tenant In-Memory Vector Database Backend."""

    def __init__(self) -> None:
        self._tenant_store: Dict[str, List[EndpointMetadataModel]] = {}

    @property
    def provider_name(self) -> str:
        return "memory"

    async def add_endpoints(self, endpoints: List[EndpointMetadataModel], tenant_id: str = "default") -> None:
        if tenant_id not in self._tenant_store:
            self._tenant_store[tenant_id] = []
        self._tenant_store[tenant_id].extend(endpoints)
        logger.info(f"Indexed {len(endpoints)} endpoints into MemoryVectorStore for tenant: [{tenant_id}]")

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    async def search_vectors(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter_providers: Optional[List[str]] = None,
        tenant_id: str = "default",
    ) -> List[EndpointMetadataModel]:
        candidates = self._tenant_store.get(tenant_id, [])
        if not candidates and tenant_id != "default":
            # Fallback to default public endpoints
            candidates = self._tenant_store.get("default", [])

        if filter_providers:
            provider_set = {p.lower() for p in filter_providers}
            candidates = [
                ep for ep in candidates
                if ep.provider.lower() in provider_set or any(p in ep.provider.lower() for p in provider_set)
            ]

        scored = []
        for ep in candidates:
            sim = self._cosine_similarity(query_vector, ep.embedding) if ep.embedding else 0.50
            scored.append((sim, ep))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for sim, ep in scored[:top_k]:
            copied = ep.model_copy()
            copied.confidence_score = round(min(0.99, max(0.50, sim)), 2)
            results.append(copied)

        return results
