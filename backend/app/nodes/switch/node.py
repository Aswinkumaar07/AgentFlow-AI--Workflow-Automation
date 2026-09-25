import logging
from typing import Any, Dict, List
from app.nodes.expression_engine import expression_engine

logger = logging.getLogger("agentflow.nodes.switch")


class SwitchNode:
    """Switch DAG Node routing execution across multiple matching case branches."""

    @staticmethod
    def evaluate_switch(node_params: Dict[str, Any], scope: Dict[str, Any]) -> Dict[str, Any]:
        target_expr = node_params.get("value", "{{$node.country}}")
        cases: List[Dict[str, Any]] = node_params.get("cases", [
            {"case_val": "India", "branch": "branch_india"},
            {"case_val": "USA", "branch": "branch_usa"},
        ])
        default_branch = node_params.get("default_branch", "branch_default")

        target_val = expression_engine.evaluate(str(target_expr), scope)
        selected_branch = default_branch

        for c in cases:
            case_match_val = expression_engine.evaluate(str(c.get("case_val")), scope)
            if str(target_val) == str(case_match_val):
                selected_branch = c.get("branch", default_branch)
                break

        logger.info(f"SwitchNode evaluated [{target_val}] -> Selected [{selected_branch}].")

        return {
            "target_value": target_val,
            "selected_branch": selected_branch,
        }
