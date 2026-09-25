import logging
import time
from typing import Any, Dict, Optional

from app.agents.llm.base import BaseLLMProvider
from app.agents.llm.enums import ProviderType

logger = logging.getLogger("agentflow.llm.mock")


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM Provider for offline testing, local development, and zero-quota execution."""

    def __init__(self) -> None:
        super().__init__()

    @property
    def provider_type(self) -> ProviderType:
        """Returns ProviderType.MOCK enum identity."""
        return ProviderType.MOCK

    async def health_check(self) -> bool:
        """Mock provider is always healthy."""
        return True

    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> str:
        start = time.perf_counter()
        logger.debug(f"[MockLLMProvider] Received text prompt length: {len(prompt)}")
        res = f"[Mock Response] Generated output for prompt: {prompt[:100]}..."
        duration_ms = (time.perf_counter() - start) * 1000.0
        self.record_execution_metrics(prompt, res, duration_ms, success=True)
        return res

    async def generate_json(
        self,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        start = time.perf_counter()
        logger.debug(f"[MockLLMProvider] Received JSON prompt length: {len(prompt)}")
        prompt_lower = prompt.lower()

        if "planner" in prompt_lower or "goal" in prompt_lower:
            result = {
                "goal": "Automated workflow execution plan",
                "services": ["gmail", "slack"],
                "tasks": [
                    {
                        "task_id": "task_1",
                        "action": "read_emails",
                        "service": "gmail",
                        "description": "Fetch unread messages",
                        "dependencies": [],
                    },
                    {
                        "task_id": "task_2",
                        "action": "send_notification",
                        "service": "slack",
                        "description": "Send alert to Slack channel",
                        "dependencies": ["task_1"],
                    },
                ],
                "confidence_score": 0.95,
            }
        elif "discovery" in prompt_lower or "endpoint" in prompt_lower:
            result = {
                "api_candidates": [
                    {
                        "task_id": "task_1",
                        "provider": "gmail",
                        "endpoint": "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                        "http_method": "GET",
                        "auth_type": "OAuth2",
                        "required_params": ["q"],
                    },
                    {
                        "task_id": "task_2",
                        "provider": "slack",
                        "endpoint": "https://slack.com/api/chat.postMessage",
                        "http_method": "POST",
                        "auth_type": "Bearer",
                        "required_params": ["channel", "text"],
                    },
                ]
            }
        elif "validation" in prompt_lower:
            result = {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "checked_rules": ["acyclic_check", "schema_validation"],
            }
        elif "repair" in prompt_lower:
            result = {
                "repaired_workflow_json": {},
                "repair_report": {
                    "applied_fixes": ["Patched endpoint path parameters"],
                    "fixed_error_codes": ["404_NOT_FOUND"],
                },
            }
        else:
            result = {
                "status": "success",
                "message": "Mock JSON response generated successfully",
                "data": {},
            }

        duration_ms = (time.perf_counter() - start) * 1000.0
        self.record_execution_metrics(prompt, str(result), duration_ms, success=True)
        return result
