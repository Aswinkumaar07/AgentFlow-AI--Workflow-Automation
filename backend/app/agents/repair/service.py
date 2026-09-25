import logging
from typing import Any, Dict, Optional
from app.agents.repair.workflow_repair_agent import workflow_repair_agent, RepairResult

logger = logging.getLogger("agentflow.agents.repair.service")


class RepairAIService:
    """AI Repair Service analyzing runtime failures and applying auto-fixes."""

    def repair_failure(
        self, error_message: str, node: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> RepairResult:
        """Analyzes execution error and generates auto-repair fixes."""
        res = workflow_repair_agent.analyze_and_repair(error_message, node, context)
        logger.info(f"AI Repair Engine analyzed failure for node '{node.get('id')}': {res.problem} | Auto-fix = {res.auto_fix}")
        return res


repair_ai_service = RepairAIService()
