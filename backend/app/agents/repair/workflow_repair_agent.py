import re
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agentflow.agents.repair")


class RepairResult(BaseModel):
    problem: str
    cause: str
    recommendation: str
    auto_fix: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.95
    is_repaired: bool = True


class WorkflowRepairAgent:
    """
    AgentFlow AI - AI Runtime Repair Engine
    Analyzes runtime execution failures, stack traces, and errors, recommending and auto-fixing
    expressions, OAuth tokens, parameters, retries, rate limits, and missing variables.
    """

    def analyze_and_repair(
        self, error_message: str, node: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> RepairResult:
        err_lower = str(error_message).lower()
        provider = node.get("provider", "Generic")
        op_id = node.get("operation_id", "")
        params = node.get("parameters", {})

        # 1. OAuth / 401 Unauthorized Error
        if "401" in err_lower or "unauthorized" in err_lower or "token" in err_lower or "oauth" in err_lower:
            return RepairResult(
                problem="OAuth2 Authorization Failure",
                cause=f"OAuth access token for provider '{provider}' is expired or invalid.",
                recommendation=f"Refresh OAuth token for provider '{provider}' and re-authenticate.",
                auto_fix={"refresh_oauth": True, "provider": provider, "retry_after_refresh": True},
                confidence=0.98,
            )

        # 2. HTTP 429 Rate Limit Exceeded Error
        elif "429" in err_lower or "rate limit" in err_lower or "too many requests" in err_lower:
            return RepairResult(
                problem="Rate Limit Exceeded (HTTP 429)",
                cause=f"Provider '{provider}' rate limit exceeded during execution.",
                recommendation="Apply exponential backoff retry policy with initial delay of 5s.",
                auto_fix={
                    "retry_policy": {"max_retries": 5, "backoff_factor": 2.0, "initial_delay_seconds": 5},
                    "enable_rate_limit_delay": True,
                },
                confidence=0.95,
            )

        # 3. Expression Syntax Error / Mismatched Braces
        elif "expression" in err_lower or "mismatched" in err_lower or "syntaxerror" in err_lower or "{{" in err_lower:
            repaired_params = {}
            for k, v in params.items():
                if isinstance(v, str):
                    open_cnt = v.count("{{")
                    close_cnt = v.count("}}")
                    if open_cnt > close_cnt:
                        repaired_params[k] = v + ("}}" * (open_cnt - close_cnt))
                    else:
                        repaired_params[k] = v
                else:
                    repaired_params[k] = v

            return RepairResult(
                problem="Expression Syntax Error",
                cause="Mismatched braces or invalid syntax in node expression.",
                recommendation="Auto-repaired expression closing braces.",
                auto_fix={"repaired_parameters": repaired_params},
                confidence=0.92,
            )

        # 4. Missing Required Parameter Error
        elif "missing" in err_lower or "required" in err_lower or "parameter" in err_lower or "none" in err_lower:
            repaired_params = {**params}
            if op_id == "gmail.messages.send" and params.get("to") is None:
                repaired_params["to"] = "{{$loop.item.email}}"

            return RepairResult(
                problem="Missing Mandatory Parameter",
                cause=f"Node '{node.get('id')}' missing mandatory execution parameter.",
                recommendation="Injected dynamic variable fallback token for missing parameter.",
                auto_fix={"repaired_parameters": repaired_params},
                confidence=0.90,
            )

        # 5. Missing Variable / Reference Error
        elif "unresolved" in err_lower or "variable" in err_lower or "keyerror" in err_lower:
            return RepairResult(
                problem="Unresolved Variable Reference",
                cause="Referenced variable expression is missing from execution context.",
                recommendation="Injected fallback system timestamp token {{$now}}.",
                auto_fix={"fallback_expression": "{{$now}}"},
                confidence=0.88,
            )

        # Generic Runtime Failure
        return RepairResult(
            problem="Generic Runtime Failure",
            cause=f"Uncaught execution exception in node '{node.get('id')}': {error_message}",
            recommendation="Enable retry policy with max 3 retries.",
            auto_fix={"retry_policy": {"max_retries": 3, "backoff_factor": 1.5}},
            confidence=0.75,
        )


workflow_repair_agent = WorkflowRepairAgent()
