import ast
import logging
from typing import Optional, Tuple

logger = logging.getLogger("agentflow.agents.code_generator.validator")


class CodeValidator:
    """
    Python Code AST Pre-Execution Syntax Auditor
    Parses Python source code using Abstract Syntax Trees (AST) to return syntax errors before execution.
    """

    def validate_python_code(self, code: str) -> Tuple[bool, Optional[str]]:
        if not code or not code.strip():
            return False, "Python code source string cannot be empty."

        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            err_msg = f"SyntaxError: {e.msg} at line {e.lineno}, col {e.offset}"
            logger.error(f"Python code syntax validation failed: {err_msg}")
            return False, err_msg
        except Exception as e:
            return False, f"AST Parse Error: {str(e)}"


code_validator = CodeValidator()
