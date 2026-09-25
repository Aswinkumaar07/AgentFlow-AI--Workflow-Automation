import re
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agentflow.agents.expressions.generator")


class ExpressionResult(BaseModel):
    expression: str
    category: str
    description: str
    is_valid: bool = True
    validation_error: Optional[str] = None


class ExpressionGenerator:
    """
    AI Expression Generator Engine
    Converts natural language text intent into executable workflow expression syntax
    covering String, Date, Math, Conditions, and Array operations.
    """

    def generate_expression(
        self, prompt: str, target_var: Optional[str] = None
    ) -> ExpressionResult:
        p_lower = prompt.lower()
        base_var = target_var or "$node.Gmail.subject"

        # 1. Date & Time Expressions
        if "today" in p_lower or "date" in p_lower:
            return ExpressionResult(
                expression="{{$today}}",
                category="Date",
                description="Current ISO formatted date (YYYY-MM-DD)",
            )
        elif "now" in p_lower or "timestamp" in p_lower:
            return ExpressionResult(
                expression="{{$now}}",
                category="Date",
                description="Current UTC ISO timestamp",
            )
        elif "uuid" in p_lower:
            return ExpressionResult(
                expression="{{$uuid}}",
                category="System",
                description="Generates a unique v4 UUID",
            )

        # 2. String Functions
        elif "uppercase" in p_lower or "upper" in p_lower:
            return ExpressionResult(
                expression=f"{{{{{base_var}.toUpperCase()}}}}",
                category="String",
                description="Converts string value to uppercase",
            )
        elif "lowercase" in p_lower or "lower" in p_lower:
            return ExpressionResult(
                expression=f"{{{{{base_var}.toLowerCase()}}}}",
                category="String",
                description="Converts string value to lowercase",
            )
        elif "trim" in p_lower:
            return ExpressionResult(
                expression=f"{{{{{base_var}.trim()}}}}",
                category="String",
                description="Trims leading and trailing whitespace",
            )
        elif "contains" in p_lower:
            return ExpressionResult(
                expression=f"{{{{{base_var}.includes('keyword')}}}}",
                category="String",
                description="Checks if string contains keyword substring",
            )

        # 3. Array Operations
        elif "length" in p_lower or "count" in p_lower or "array" in p_lower:
            arr_var = target_var or "$node.Sheets.values"
            return ExpressionResult(
                expression=f"{{{{{arr_var}.length}}}}",
                category="Array",
                description="Returns total number of items in array collection",
            )
        elif "join" in p_lower:
            arr_var = target_var or "$node.Sheets.values"
            return ExpressionResult(
                expression=f"{{{{{arr_var}.join(', ')}}}}",
                category="Array",
                description="Joins array elements into delimited string",
            )

        # 4. Math Functions
        elif "round" in p_lower:
            num_var = target_var or "$node.Sheets.amount"
            return ExpressionResult(
                expression=f"{{{{Math.round({num_var})}}}}",
                category="Math",
                description="Rounds numeric value to nearest integer",
            )
        elif "abs" in p_lower or "absolute" in p_lower:
            num_var = target_var or "$node.Sheets.amount"
            return ExpressionResult(
                expression=f"{{{{Math.abs({num_var})}}}}",
                category="Math",
                description="Returns absolute numeric value",
            )

        # 5. Conditional Expressions
        elif "greater than" in p_lower or "condition" in p_lower or "if" in p_lower:
            num_var = target_var or "$node.Sheets.amount"
            return ExpressionResult(
                expression=f"{{{{{num_var} > 100 ? 'High' : 'Low'}}}}",
                category="Condition",
                description="Ternary condition evaluating value threshold",
            )

        # Default Fallback Expression
        return ExpressionResult(
            expression=f"{{{{{base_var}}}}}",
            category="Generic",
            description="Direct dynamic variable reference",
        )


expression_generator = ExpressionGenerator()
