import logging
from typing import Any, Dict, Optional, Tuple
from app.agents.expressions.expression_generator import expression_generator, ExpressionResult
from app.agents.expressions.expression_validator import expression_validator

logger = logging.getLogger("agentflow.agents.expressions.service")


class ExpressionAIService:
    """AI Expression Service generating executable expressions and performing pre-runtime validation."""

    def generate(
        self, prompt: str, target_var: Optional[str] = None
    ) -> ExpressionResult:
        res = expression_generator.generate_expression(prompt, target_var)
        is_valid, err = expression_validator.validate_expression(res.expression)
        res.is_valid = is_valid
        res.validation_error = err
        return res

    def validate(self, expression: str) -> Tuple[bool, Optional[str]]:
        return expression_validator.validate_expression(expression)


expression_ai_service = ExpressionAIService()
