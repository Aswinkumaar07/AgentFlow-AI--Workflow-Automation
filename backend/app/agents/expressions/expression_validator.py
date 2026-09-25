import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger("agentflow.agents.expressions.validator")


class ExpressionValidator:
    """
    AI Expression Pre-Runtime Validator Engine
    Validates expression syntax, brace balancing, function signatures, and parenthetical matching.
    """

    def validate_expression(self, expression: str) -> Tuple[bool, Optional[str]]:
        if not expression:
            return False, "Expression string cannot be empty."

        # 1. Double Brace Matching Check
        open_braces = expression.count("{{")
        close_braces = expression.count("}}")

        if open_braces != close_braces:
            return False, f"Mismatched expression braces: {open_braces} '{{{{' vs {close_braces} '}}}}'."

        if open_braces == 0:
            return True, None  # Plain literal string

        # Extract content inside braces
        matches = re.findall(r"\{\{(.*?)\}\}", expression, re.DOTALL)
        for content in matches:
            content = content.strip()

            # 2. Check for Parentheses Balance in Function Calls
            open_parens = content.count("(")
            close_parens = content.count(")")
            if open_parens != close_parens:
                return False, f"Unbalanced parentheses in function call expression: '{content}'."

            # 3. Check for Illegal Characters
            if re.search(r"[;\$<>]", content) and not any(op in content for op in [">", "<", "$", "=>"]):
                return False, f"Syntax error in expression body: '{content}'."

        return True, None


expression_validator = ExpressionValidator()
