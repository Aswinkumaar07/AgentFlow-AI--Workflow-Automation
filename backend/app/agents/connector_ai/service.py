import logging
from typing import Any, Dict, List, Optional
from app.agents.connector_ai.connector_selector import connector_selector, ConnectorCandidate
from app.agents.connector_ai.operation_ranker import operation_ranker, OperationResult

logger = logging.getLogger("agentflow.agents.connector_ai.service")


class ConnectorAIService:
    """AI Connector Intelligence Layer serving semantic search, operation ranking, and dynamic schema discovery."""

    def discover_connectors_and_operations(
        self, query: str, target_providers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Discovers candidates, ranks operations, and builds dynamic parameter & authentication schemas."""
        selected_candidates = connector_selector.select_connectors(query, top_k=5)
        ranked_ops: List[OperationResult] = []

        if target_providers:
            for p in target_providers:
                ops = operation_ranker.rank_operations(query, target_provider=p, top_k=2)
                ranked_ops.extend(ops)
        else:
            for c in selected_candidates:
                ops = operation_ranker.rank_operations(query, target_provider=c.provider, top_k=2)
                ranked_ops.extend(ops)

        return {
            "query": query,
            "candidates": [c.model_dump() for c in selected_candidates],
            "ranked_operations": [op.model_dump() for op in ranked_ops],
        }


connector_ai_service = ConnectorAIService()
