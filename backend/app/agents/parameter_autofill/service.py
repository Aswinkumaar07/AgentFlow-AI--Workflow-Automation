import logging
from typing import Any, Dict, List, Tuple
from app.agents.parameter_autofill.parameter_autofill_engine import parameter_autofill_engine

logger = logging.getLogger("agentflow.agents.parameter_autofill.service")


class ParameterAutofillService:
    """Service serving prompt-aware node parameter autofill & pre-configuration."""

    def autofill_graph(self, graph: Dict[str, Any], prompt: str = "") -> Dict[str, Any]:
        """Autofills all node parameters in a workflow graph with prompt context."""
        return parameter_autofill_engine.autofill_workflow_nodes(graph, prompt=prompt)

    def extract_prompt_parameters(
        self, provider: str, operation_id: str, prompt: str, existing_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Extracts parameters, confidence scores, and missing parameters for a single node."""
        params, conf_scores, missing = parameter_autofill_engine.autofill_node(
            provider=provider,
            operation_id=operation_id,
            existing_params=existing_params,
            prompt=prompt,
        )
        return {
            "provider": provider,
            "operation_id": operation_id,
            "parameters": params,
            "confidence_scores": conf_scores,
            "missing_parameters": missing,
            "is_complete": len(missing) == 0,
        }


parameter_autofill_service = ParameterAutofillService()
