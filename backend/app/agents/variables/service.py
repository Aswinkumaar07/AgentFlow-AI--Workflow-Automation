import logging
from typing import Any, Dict
from app.agents.variables.variable_resolver import variable_resolver, VariableDiscoveryResult

logger = logging.getLogger("agentflow.agents.variables.service")


class VariableAIService:
    """AI Variable Discovery Service serving node output schemas, loop tokens, and system variables."""

    def discover(self, workflow_graph: Dict[str, Any]) -> Dict[str, Any]:
        """Discovers all available variable tokens for a given workflow graph."""
        res: VariableDiscoveryResult = variable_resolver.discover_variables(workflow_graph)
        return res.model_dump()


variable_ai_service = VariableAIService()
