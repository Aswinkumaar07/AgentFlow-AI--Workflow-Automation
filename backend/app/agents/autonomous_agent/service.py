import logging
from typing import Any, Dict, Optional
from app.agents.autonomous_agent.autonomous_engine import autonomous_agent_engine, AutonomousExecutionResult

logger = logging.getLogger("agentflow.agents.autonomous_agent.service")


class AutonomousAgentAIService:
    """Service serving world's first Autonomous Workflow Agent Engine."""

    def execute_goal(
        self, goal: str, context: Optional[Dict[str, Any]] = None
    ) -> AutonomousExecutionResult:
        """Executes outcome goal dynamically without predefined DAG templates."""
        return autonomous_agent_engine.execute_outcome_goal(goal, context)

    def rollback(self, execution_result: AutonomousExecutionResult) -> AutonomousExecutionResult:
        """Reverses autonomous steps executed during run."""
        return autonomous_agent_engine.rollback_execution(execution_result)


autonomous_agent_ai_service = AutonomousAgentAIService()
