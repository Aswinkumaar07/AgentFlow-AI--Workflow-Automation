import logging
from typing import Any, Dict
from app.agents.self_healing.self_healing_engine import self_healing_engine, SelfHealingDiagnostic

logger = logging.getLogger("agentflow.agents.self_healing.service")


class SelfHealingAIService:
    """Service serving Self-Healing workflow diagnostics and one-click graph fixes."""

    def diagnose(
        self, error_message: str, node: Dict[str, Any], workflow_graph: Dict[str, Any]
    ) -> SelfHealingDiagnostic:
        """Diagnoses execution error and plans repair fix."""
        return self_healing_engine.diagnose_and_plan_fix(error_message, node, workflow_graph)

    def apply_fix(
        self, error_message: str, node: Dict[str, Any], workflow_graph: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Applies one-click repair fix directly to workflow DAG."""
        return self_healing_engine.apply_one_click_fix(error_message, node, workflow_graph)


self_healing_ai_service = SelfHealingAIService()
self_healing_agent = self_healing_ai_service
