import logging
from typing import Any, Dict, List, Optional
from app.agents.marketplace.marketplace_engine import ai_marketplace_engine, MarketplaceTemplate

logger = logging.getLogger("agentflow.agents.marketplace.service")


class MarketplaceAIService:
    """Service serving AI-Powered Workflow Marketplace."""

    def list_templates(self) -> List[MarketplaceTemplate]:
        return list(ai_marketplace_engine.templates.values())

    def search_recommend(self, query: str) -> List[MarketplaceTemplate]:
        return ai_marketplace_engine.search_recommend(query)

    def publish(
        self, title: str, description: str, workflow_graph: Dict[str, Any], author: str = "User"
    ) -> MarketplaceTemplate:
        return ai_marketplace_engine.publish_workflow(title, description, workflow_graph, author)

    def personalize(self, template_id: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        return ai_marketplace_engine.personalize_template(template_id, user_context)

    def fork(self, template_id: str, user_id: str = "User") -> MarketplaceTemplate:
        return ai_marketplace_engine.fork_workflow(template_id, user_id)

    def rate(self, template_id: str, stars: float) -> MarketplaceTemplate:
        return ai_marketplace_engine.add_rating(template_id, stars)

    def comment(self, template_id: str, user_name: str, content: str) -> MarketplaceTemplate:
        return ai_marketplace_engine.add_comment(template_id, user_name, content)


marketplace_ai_service = MarketplaceAIService()
