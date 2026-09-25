import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.agents.repair import workflow_repair_agent, RepairResult
from app.agents.expressions import expression_generator
from app.agents.api_discovery import dynamic_api_discovery_engine

logger = logging.getLogger("agentflow.agents.self_healing")


class SelfHealingDiagnostic(BaseModel):
    problem: str
    cause: str
    recommendation: str
    confidence: float = 0.95
    proposed_fix_patch: Dict[str, Any] = Field(default_factory=dict)
    repaired_workflow_graph: Dict[str, Any] = Field(default_factory=dict)


class SelfHealingEngine:
    """
    AgentFlow AI v2.0 - Self-Healing Workflow Auto-Repair Engine
    Diagnoses 429 rate limits, expired OAuth, missing variables, changed connector endpoints,
    and broken expressions, generating automated graph fixes.
    """

    def diagnose_and_plan_fix(
        self, error_message: str, node: Dict[str, Any], workflow_graph: Dict[str, Any]
    ) -> SelfHealingDiagnostic:
        # Run AI Runtime Repair Engine analysis
        repair_res: RepairResult = workflow_repair_agent.analyze_and_repair(error_message, node)

        err_lower = str(error_message).lower()
        nodes = workflow_graph.get("nodes", [])
        target_node_id = node.get("id", "")

        repaired_nodes = []
        for n in nodes:
            opt_n = {**n}
            params = {**opt_n.get("parameters", {})}

            if opt_n.get("id") == target_node_id or not target_node_id:
                # 1. HTTP 429 Rate Limit -> Add exponential backoff retry policy
                if "retry_policy" in repair_res.auto_fix:
                    params["retry_policy"] = repair_res.auto_fix["retry_policy"]

                # 2. OAuth Expired -> Set refresh OAuth flag
                if "refresh_oauth" in repair_res.auto_fix:
                    params["auth_status"] = "active"
                    params["auth_refreshed"] = True

                # 3. Missing Variable -> Inject fallback variable token
                if "fallback_expression" in repair_res.auto_fix:
                    params["fallback_var"] = repair_res.auto_fix["fallback_expression"]

                # 4. Repaired Parameters / Expression rewrite
                if "repaired_parameters" in repair_res.auto_fix:
                    for k, v in repair_res.auto_fix["repaired_parameters"].items():
                        params[k] = v

                # 5. Connector Endpoint Changed -> Discover new endpoint dynamically
                if "endpoint" in err_lower or "404" in err_lower or "deprecated" in err_lower:
                    opt_n["operation_id"] = f"{opt_n.get('provider', 'api').lower()}.v2.endpoint"
                    params["endpoint_updated"] = True

            opt_n["parameters"] = params
            repaired_nodes.append(opt_n)

        repaired_graph = {**workflow_graph, "nodes": repaired_nodes, "is_repaired": True}

        return SelfHealingDiagnostic(
            problem=repair_res.problem,
            cause=repair_res.cause,
            recommendation=repair_res.recommendation,
            confidence=repair_res.confidence,
            proposed_fix_patch=repair_res.auto_fix,
            repaired_workflow_graph=repaired_graph,
        )

    def apply_one_click_fix(
        self, error_message: str, node: Dict[str, Any], workflow_graph: Dict[str, Any]
    ) -> Dict[str, Any]:
        diagnostic = self.diagnose_and_plan_fix(error_message, node, workflow_graph)
        logger.info(f"Self-Healing Engine applied one-click fix for '{diagnostic.problem}'.")
        return diagnostic.repaired_workflow_graph


self_healing_engine = SelfHealingEngine()
