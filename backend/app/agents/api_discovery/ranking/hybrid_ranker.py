import math
import re
from typing import List
from app.agents.api_discovery.config import discovery_config
from app.agents.api_discovery.interfaces import BaseHybridRanker
from app.agents.api_discovery.models import EndpointMetadataModel


class HybridRanker(BaseHybridRanker):
    """Multi-Factor Enterprise Hybrid Ranking Engine combining Vector Similarity, BM25, Popularity, Health, Latency, & Cost."""

    def rank(
        self, candidates: List[EndpointMetadataModel], query: str, query_vector: List[float]
    ) -> List[EndpointMetadataModel]:
        query_words = set(re.findall(r"\w+", query.lower()))

        for ep in candidates:
            # 1. Vector similarity component
            vec_sim = ep.confidence_score

            # 2. BM25 keyword overlap
            text_corpus = f"{ep.provider} {ep.operation_id} {ep.summary} {ep.description} {' '.join(ep.required_params)}".lower()
            corpus_words = set(re.findall(r"\w+", text_corpus))
            bm25_score = (len(query_words.intersection(corpus_words)) / len(query_words)) if query_words else 0.0

            # 3. Popularity & Health
            pop_score = ep.popularity_score
            health_score = ep.health_score

            # 4. Latency score (lower is better, normalized 0.0 - 1.0)
            latency_score = max(0.0, 1.0 - (ep.latency_ms / 500.0))

            # 5. Cost score (lower cost is better, normalized 0.0 - 1.0)
            cost_score = max(0.0, 1.0 - (ep.estimated_cost * 100))

            # Weighted Hybrid Aggregation
            final_score = (
                (discovery_config.WEIGHT_VECTOR_SIMILARITY * vec_sim)
                + (discovery_config.WEIGHT_BM25 * bm25_score)
                + (discovery_config.WEIGHT_POPULARITY * pop_score)
                + (discovery_config.WEIGHT_HEALTH_SCORE * health_score)
                + (discovery_config.WEIGHT_LATENCY * latency_score)
                + (discovery_config.WEIGHT_COST * cost_score)
            )

            ep.confidence_score = round(min(0.99, max(0.50, final_score)), 2)

        return sorted(candidates, key=lambda x: x.confidence_score, reverse=True)
