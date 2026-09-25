import logging
from typing import Any, Dict, List, Tuple
from app.agents.parameter_ai.parameter_generator import parameter_generator, ParameterGenerationResult

logger = logging.getLogger("agentflow.agents.parameter_ai.service")


class ParameterAIService:
    """AI Parameter Service populating parameters and discovering missing inputs across DAG nodes."""

    def populate_node_parameters(
        self, prompt: str, nodes: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Iterates over graph nodes, populating node parameters and aggregating missing inputs."""
        all_missing: List[str] = []

        for node in nodes:
            op_id = node.get("operation_id", "")
            provider = node.get("provider", "")
            res: ParameterGenerationResult = parameter_generator.generate_parameters_for_operation(
                prompt, op_id, provider
            )

            merged_params = {**res.parameters, **node.get("parameters", {})}
            node["parameters"] = merged_params

            if res.missing_inputs:
                all_missing.extend(res.missing_inputs)

        unique_missing = list(dict.fromkeys(all_missing))
        return nodes, unique_missing


parameter_ai_service = ParameterAIService()
