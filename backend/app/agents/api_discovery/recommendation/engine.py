import logging
from typing import List
from app.agents.api_discovery.interfaces import BaseRecommendationEngine
from app.agents.api_discovery.models import APIRecommendationModel, EndpointMetadataModel

logger = logging.getLogger("agentflow.api_discovery.recommendation")


class RecommendationEngine(BaseRecommendationEngine):
    """Enterprise Recommendation Engine for recommending cheaper, faster, or higher availability alternative APIs."""

    def recommend_alternatives(
        self, target_endpoint: EndpointMetadataModel, catalog: List[EndpointMetadataModel]
    ) -> List[APIRecommendationModel]:
        recommendations: List[APIRecommendationModel] = []

        for candidate in catalog:
            if candidate.operation_id == target_endpoint.operation_id:
                continue

            # 1. Faster Latency Recommendation
            if candidate.latency_ms < target_endpoint.latency_ms * 0.7:
                savings = round(((target_endpoint.latency_ms - candidate.latency_ms) / target_endpoint.latency_ms) * 100, 1)
                recommendations.append(
                    APIRecommendationModel(
                        target_operation_id=target_endpoint.operation_id,
                        recommended_operation_id=candidate.operation_id,
                        recommendation_type="faster",
                        savings_percentage=savings,
                        rationale=f"Provider '{candidate.provider}' endpoint responds {savings}% faster ({candidate.latency_ms}ms vs {target_endpoint.latency_ms}ms).",
                    )
                )

            # 2. Cheaper Cost Recommendation
            if candidate.estimated_cost < target_endpoint.estimated_cost * 0.7:
                savings = round(((target_endpoint.estimated_cost - candidate.estimated_cost) / target_endpoint.estimated_cost) * 100, 1)
                recommendations.append(
                    APIRecommendationModel(
                        target_operation_id=target_endpoint.operation_id,
                        recommended_operation_id=candidate.operation_id,
                        recommendation_type="cheaper",
                        savings_percentage=savings,
                        rationale=f"Provider '{candidate.provider}' offers {savings}% cost savings per 1000 execution requests.",
                    )
                )

        return recommendations
