import logging
from typing import Any, Dict, List

logger = logging.getLogger("agentflow.nodes.merge")


class MergeNode:
    """Merge DAG Node combining multiple incoming parallel execution branch outputs."""

    @staticmethod
    def process_merge(node_params: Dict[str, Any], scope: Dict[str, Any]) -> Dict[str, Any]:
        mode = node_params.get("mode", "Wait All")  # Wait All, Merge Append, Merge By Key
        previous_outputs = scope.get("previous_outputs", {})

        merged_data: List[Any] = []
        for step_id, out_val in previous_outputs.items():
            merged_data.append({"source_step": step_id, "data": out_val})

        logger.info(f"MergeNode processed {len(merged_data)} incoming branch outputs with mode [{mode}].")

        return {
            "mode": mode,
            "merged_count": len(merged_data),
            "output": merged_data,
        }
