import logging
from typing import Any, Dict
from app.nodes.expression_engine import expression_engine

logger = logging.getLogger("agentflow.nodes.condition")


class ConditionNode:
    """Conditional (IF/ELSE) DAG Node evaluating boolean rules and branching execution."""

    @staticmethod
    def evaluate_condition(node_params: Dict[str, Any], scope: Dict[str, Any]) -> Dict[str, Any]:
        left_raw = node_params.get("left") if node_params.get("left") is not None else node_params.get("left_value", "")
        operator = str(node_params.get("operator") or "equals")
        right_raw = node_params.get("right") if node_params.get("right") is not None else node_params.get("right_value", "")

        left_val = expression_engine.evaluate(str(left_raw), scope) if isinstance(left_raw, str) else left_raw
        right_val = expression_engine.evaluate(str(right_raw), scope) if isinstance(right_raw, str) else right_raw

        result = ConditionNode._compare(left_val, operator, right_val)

        selected_branch = "true_branch" if result else "false_branch"
        true_branch = node_params.get("true_branch") or node_params.get("true_step_id")
        false_branch = node_params.get("false_branch") or node_params.get("false_step_id")

        logger.info(f"ConditionNode evaluated [{left_val} {operator} {right_val}] -> {result} ({selected_branch}).")

        return {
            "status": "SUCCESS",
            "result": result,
            "selected_branch": selected_branch,
            "left": left_val,
            "right": right_val,
            "left_evaluated": left_val,
            "right_evaluated": right_val,
            "left_raw": left_raw,
            "right_raw": right_raw,
            "operator": operator,
            "true_branch": true_branch,
            "false_branch": false_branch,
            "executed_branch": true_branch if result else false_branch,
            "skipped_branch": false_branch if result else true_branch,
        }

    @staticmethod
    def _compare(left: Any, operator: str, right: Any) -> bool:
        op = operator.lower().strip().replace(" ", "_")

        if op in ["exists"]:
            if left is None:
                return False
            if isinstance(left, (str, list, dict)):
                return len(left) > 0
            return True

        if op in ["not_exists"]:
            if left is None:
                return True
            if isinstance(left, (str, list, dict)):
                return len(left) == 0
            return False

        l_str = str(left if left is not None else "")
        r_str = str(right if right is not None else "")

        if op in ["equals", "equal", "=="]:
            return l_str == r_str
        if op in ["not_equals", "not_equal", "!="]:
            return l_str != r_str
        if op in ["contains"]:
            return r_str.lower() in l_str.lower()
        if op in ["not_contains"]:
            return r_str.lower() not in l_str.lower()
        if op in ["starts_with", "startswith"]:
            return l_str.lower().startswith(r_str.lower())
        if op in ["ends_with", "endswith"]:
            return l_str.lower().endswith(r_str.lower())

        try:
            l_num = float(left) if left is not None else 0.0
            r_num = float(right) if right is not None else 0.0
            if op in ["greater_than", "greaterthan", ">"]:
                return l_num > r_num
            if op in ["less_than", "lessthan", "<"]:
                return l_num < r_num
            if op in ["greater_or_equal", "greater_equal", ">="]:
                return l_num >= r_num
            if op in ["less_or_equal", "less_equal", "<="]:
                return l_num <= r_num
        except (ValueError, TypeError):
            pass

        return False
