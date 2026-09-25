from typing import Dict, Any, List
from app.agents.validation.interface import BaseValidationService
from app.agents.tools import validator_tool
from app.agents.llm.manager import llm_manager
from app.agents.llm.prompts import PromptBuilder
from app.agents.llm.exceptions import LLMError
from app.agents.llm.enums import AgentType


class ValidationAgent(BaseValidationService):
    """Validation Agent Node for graph audit, DAG cycle detection & parameter schema validation."""

    async def validate_dag_structure(self, dag: Dict[str, Any]) -> List[str]:
        report = await self.validate_workflow(dag)
        return report.get("errors", [])

    async def validate_workflow(self, dag: Dict[str, Any]) -> Dict[str, Any]:
        tool_report = validator_tool.validate(dag)
        provider = llm_manager.provider_for(AgentType.VALIDATION)

        try:
            prompt = PromptBuilder.validation_prompt(workflow=dag)
            llm_res = await provider.generate_json(prompt)

            is_valid = tool_report.get("is_valid", True) and llm_res.get("is_valid", True)
            errors = list(set(tool_report.get("errors", []) + llm_res.get("errors", [])))
            warnings = list(set(tool_report.get("warnings", []) + llm_res.get("warnings", [])))

            return {
                "is_valid": is_valid,
                "errors": errors,
                "warnings": warnings,
                "checked_rules": llm_res.get("checked_rules", ["acyclic_check", "schema_validation"]),
            }
        except LLMError:
            return tool_report


validation_agent = ValidationAgent()
