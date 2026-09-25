import datetime
import re
import uuid
from typing import Any, Dict


class ExpressionEngine:
    """Safe evaluation and interpolation engine for workflow expressions and system variables."""

    @staticmethod
    def evaluate(expression_str: str, scope: Dict[str, Any]) -> Any:
        if not isinstance(expression_str, str):
            return expression_str

        # System Built-in Variables
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        today_date = datetime.date.today().isoformat()
        generated_uuid = str(uuid.uuid4())

        system_vars = {
            "$now": now_iso,
            "$today": today_date,
            "$uuid": generated_uuid,
            "$execution": scope.get("execution", {"id": "exec_demo"}),
            "$env": scope.get("env", {"API_KEY": "secret_key_123"}),
        }

        merged_scope = {**system_vars, **scope}

        # Check for {{expression}}
        pattern = r"\{\{\s*(.*?)\s*\}\}"
        matches = re.findall(pattern, expression_str)
        if not matches:
            return expression_str

        # If single match, evaluate directly
        if len(matches) == 1 and expression_str.strip() == f"{{{{{matches[0]}}}}}":
            return ExpressionEngine._eval_single_expr(matches[0], merged_scope)

        result_str = expression_str
        for expr in matches:
            val = ExpressionEngine._eval_single_expr(expr, merged_scope)
            result_str = result_str.replace(f"{{{{{expr}}}}}", str(val if val is not None else ""))
        return result_str

    @staticmethod
    def _eval_single_expr(expr: str, scope: Dict[str, Any]) -> Any:
        expr = expr.strip()

        # Check string functions e.g. path.toUpperCase()
        if ".toUpperCase()" in expr:
            base_path = expr.replace(".toUpperCase()", "").strip()
            val = ExpressionEngine._resolve_path(base_path, scope)
            return str(val).upper() if val is not None else ""

        if ".toLowerCase()" in expr:
            base_path = expr.replace(".toLowerCase()", "").strip()
            val = ExpressionEngine._resolve_path(base_path, scope)
            return str(val).lower() if val is not None else ""

        # Check simple arithmetic e.g. path + 100
        if " + " in expr:
            parts = expr.split(" + ")
            left = ExpressionEngine._resolve_path(parts[0].strip(), scope)
            right = ExpressionEngine._resolve_path(parts[1].strip(), scope)
            try:
                l_num = float(left) if left is not None else 0
                r_num = float(right) if right is not None else float(parts[1].strip())
                return l_num + r_num
            except ValueError:
                return f"{left or ''}{right or parts[1].strip()}"

        return ExpressionEngine._resolve_path(expr, scope)

    @staticmethod
    def _resolve_path(path: str, scope: Dict[str, Any]) -> Any:
        clean_path = path.replace("$node.", "").replace("node.", "").replace("$workflow.", "").replace("workflow.", "")
        parts = clean_path.split(".")

        # Try root scope first
        val = ExpressionEngine._lookup_parts(parts, scope)
        if val is not None:
            return val

        # Try scope["node"] if present
        if "node" in scope and isinstance(scope["node"], dict):
            val = ExpressionEngine._lookup_parts(parts, scope["node"])
            if val is not None:
                return val

        # Try scope["previous_outputs"] if present
        if "previous_outputs" in scope and isinstance(scope["previous_outputs"], dict):
            val = ExpressionEngine._lookup_parts(parts, scope["previous_outputs"])
            if val is not None:
                return val

        return None

    @staticmethod
    def _lookup_parts(parts: list, current: Any) -> Any:
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current


expression_engine = ExpressionEngine()
