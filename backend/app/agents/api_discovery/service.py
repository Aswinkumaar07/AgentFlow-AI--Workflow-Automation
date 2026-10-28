import asyncio
import glob
import logging
import os
import time
from typing import Any, Dict, List, Optional

from app.agents.api_discovery.cache.enterprise_cache import EnterpriseCache
from app.agents.api_discovery.config import discovery_config
from app.agents.api_discovery.dynamic_discovery import (
    DynamicConnectorSpec,
    DynamicDiscoveryResult,
    dynamic_api_discovery_engine,
)
from app.agents.api_discovery.embeddings.generator import EmbeddingGenerator
from app.agents.api_discovery.graph.capability_graph import CapabilityGraph
from app.agents.api_discovery.interfaces import BaseAPIDiscoveryService
from app.agents.api_discovery.models import EndpointMetadataModel
from app.agents.api_discovery.parser.spec_parser import EnterpriseSpecParser
from app.agents.api_discovery.ranking.hybrid_ranker import HybridRanker
from app.agents.api_discovery.recommendation.engine import RecommendationEngine
from app.agents.api_discovery.vectorstore.store import VectorStore
from app.agents.llm.enums import AgentType
from app.agents.llm.exceptions import LLMError
from app.agents.llm.manager import llm_manager
from app.agents.llm.prompts import PromptBuilder

logger = logging.getLogger("agentflow.api_discovery.service")


class APIDiscoveryAgent(BaseAPIDiscoveryService):
    """Enterprise API Discovery Platform Engine incorporating Vector Search, Hybrid Ranking, Capability Graph, and Tier-1 Caching."""

    def __init__(self) -> None:
        self.spec_parser = EnterpriseSpecParser()
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStore()
        self.hybrid_ranker = HybridRanker()
        self.capability_graph = CapabilityGraph()
        self.recommendation_engine = RecommendationEngine()
        self.cache = EnterpriseCache()

        self._catalog_loaded = False
        self._load_yaml_catalogs()

    def _load_yaml_catalogs(self) -> None:
        """Loads and indexes YAML provider catalogs from catalog/ directory."""
        if self._catalog_loaded:
            return

        catalog_dir = discovery_config.CATALOG_DIR
        if not os.path.exists(catalog_dir):
            # Fallback to local relative path
            catalog_dir = os.path.join(os.path.dirname(__file__), "catalog")

        yaml_files = glob.glob(os.path.join(catalog_dir, "*.yaml")) + glob.glob(
            os.path.join(catalog_dir, "*.yml")
        )
        all_endpoints: List[EndpointMetadataModel] = []

        for yf in yaml_files:
            try:
                with open(yf, "r", encoding="utf-8") as f:
                    content = f.read()
                    parsed = self.spec_parser.parse_spec(content)
                    all_endpoints.extend(parsed)
            except Exception as e:
                logger.error(f"Failed to parse catalog YAML file '{yf}': {e}")

        # Compute embeddings synchronously for default catalog
        for ep in all_endpoints:
            text = f"{ep.provider} {ep.operation_id} {ep.summary} {ep.description}"
            # Synchronous md5-hash vector computation
            words = text.lower().split()
            vec = [0.0] * 384
            for w in words:
                idx = hash(w) % 384
                vec[idx] += 0.1
            ep.embedding = vec

        # Add to vector store safely without raising event loop deprecation/runtime errors
        try:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.vector_store.add_endpoints(all_endpoints))
            except RuntimeError:
                asyncio.run(self.vector_store.add_endpoints(all_endpoints))
        except Exception:
            if hasattr(self.vector_store, "_provider") and hasattr(
                self.vector_store._provider, "_endpoints"
            ):
                self.vector_store._provider._endpoints.extend(all_endpoints)

        self._catalog_loaded = True
        logger.info(
            f"Loaded {len(all_endpoints)} endpoints across {len(yaml_files)} YAML catalogs into Enterprise API Discovery Engine."
        )

    async def discover_endpoints(
        self, query: str, target_providers: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Performs vector similarity + hybrid search to find ranked API endpoints matching user prompt."""
        cache_key = f"{query}_{','.join(target_providers or [])}"
        cached_res = await self.cache.get(cache_key)
        if cached_res:
            logger.info(
                f"Enterprise API Discovery cache hit for query: '{query}'"
            )
            return cached_res

        # 1. Generate query embedding vector
        query_vector = await self.embedding_generator.generate_embedding(query)

        # 2. Vector search over index
        candidates = await self.vector_store.search_vectors(
            query_vector, top_k=10, filter_providers=target_providers
        )

        # 3. Hybrid ranking
        ranked_candidates = self.hybrid_ranker.rank(
            candidates, query, query_vector
        )
        result_dicts = [
            ep.model_dump(exclude={"embedding"}) for ep in ranked_candidates
        ]

        # 4. Cache result
        await self.cache.set(
            cache_key,
            result_dicts,
            ttl_seconds=discovery_config.CACHE_TTL_SECONDS,
        )
        return result_dicts

    async def discover_for_plan(
        self, plan: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Discovers endpoints for an execution plan using LLM strategy fallback."""
        goal = (
            plan.get("goal", str(plan)) if isinstance(plan, dict) else str(plan)
        )
        services = (
            plan.get("services", []) if isinstance(plan, dict) else []
        )

        try:
            provider = llm_manager.provider_for(AgentType.DISCOVERY)
            prompt = PromptBuilder.discovery_prompt(
                goal=goal, services=services
            )
            llm_res = await provider.generate_json(prompt)

            candidates = llm_res.get("api_candidates", [])
            if candidates:
                return candidates
        except LLMError:
            pass

        return await self.discover_endpoints(
            query=goal, target_providers=services
        )

    async def parse_openapi_spec(
        self, spec_url_or_json: Any
    ) -> Dict[str, Any]:
        """Parses OpenAPI spec and indexes endpoints into vector store."""
        parsed = self.spec_parser.parse_spec(spec_url_or_json)
        for ep in parsed:
            ep.embedding = await self.embedding_generator.generate_embedding(
                f"{ep.provider} {ep.operation_id} {ep.summary}"
            )
        await self.vector_store.add_endpoints(parsed)
        return {"parsed_spec": True, "endpoints_indexed": len(parsed)}

    async def discover_and_register_from_url(
        self, url: str, fetcher_override: Optional[Any] = None
    ) -> DynamicDiscoveryResult:
        """
        AI-37 Phase 2 Discovery Bridge:
        Retrieves remote OpenAPI/Swagger spec via SpecFetcher, parses content using EnterpriseSpecParser,
        and registers operations dynamically into DynamicAPIDiscoveryEngine.
        """
        from app.agents.api_discovery.fetcher import (
            SpecFetcherError,
            spec_fetcher,
        )

        active_fetcher = fetcher_override or spec_fetcher

        try:
            fetch_res = await active_fetcher.fetch(url)
        except SpecFetcherError as sfe:
            logger.error(f"SpecFetcher failed for URL '{url}': {sfe}")
            return DynamicDiscoveryResult(
                success=False,
                provider="Unknown",
                endpoints_indexed=0,
                connector_spec=DynamicConnectorSpec(provider="Unknown"),
                message=f"SpecFetcher error: {sfe.message if hasattr(sfe, 'message') else str(sfe)}",
            )

        # Pass fetched specification content to DynamicAPIDiscoveryEngine (which invokes EnterpriseSpecParser)
        discovery_res = dynamic_api_discovery_engine.discover_and_register_api(
            fetch_res.content, format_hint=fetch_res.format_hint
        )

        # Index parsed endpoints into VectorStore for RAG matching
        if discovery_res.success and fetch_res.content:
            try:
                parsed_eps = self.spec_parser.parse_spec(
                    fetch_res.content, format_hint=fetch_res.format_hint
                )
                for ep in parsed_eps:
                    ep.embedding = (
                        await self.embedding_generator.generate_embedding(
                            f"{ep.provider} {ep.operation_id} {ep.summary} {ep.description}"
                        )
                    )
                await self.vector_store.add_endpoints(parsed_eps)
            except Exception as e:
                logger.warning(
                    f"Failed to index endpoints into VectorStore: {e}"
                )

        return discovery_res


api_discovery_agent = APIDiscoveryAgent()
