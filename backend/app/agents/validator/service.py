import logging
from typing import Any, Dict
from app.agents.validator.workflow_validator import workflow_validator, ValidationResult

logger = logging.getLogger("agentflow.agents.validator.service")


class ValidatorAIService:
    """AI Validator Service verifying DAG topology, expressions, parameters, and connector integrity."""

    def validate(self, workflow_graph: Dict[str, Any]) -> ValidationResult:
        """Validates workflow graph spec returning structured ValidationResult."""
        return workflow_validator.validate_workflow(workflow_graph)


validator_ai_service = ValidatorAIService()
