import logging
from typing import Optional, Tuple
from app.agents.code_generator.python_generator import python_code_generator, CodeGenerationResult
from app.agents.code_generator.code_validator import code_validator

logger = logging.getLogger("agentflow.agents.code_generator.service")


class CodeGeneratorAIService:
    """AI Code Generator Service producing validated, executable Python code script nodes."""

    def generate_python_node(self, task_prompt: str) -> CodeGenerationResult:
        res = python_code_generator.generate_code(task_prompt)
        is_valid, err = code_validator.validate_python_code(res.code)
        res.is_valid = is_valid
        res.syntax_error = err
        return res

    def validate_code(self, code: str) -> Tuple[bool, Optional[str]]:
        return code_validator.validate_python_code(code)


code_generator_ai_service = CodeGeneratorAIService()
