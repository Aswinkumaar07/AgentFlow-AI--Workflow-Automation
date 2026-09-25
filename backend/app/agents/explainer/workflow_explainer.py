import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agentflow.agents.explainer")


class StepExplanation(BaseModel):
    step_id: str
    label: str
    provider: str
    operation: str
    explanation: str


class ExplanationResult(BaseModel):
    summary: str
    step_explanations: List[StepExplanation] = Field(default_factory=list)
    variables_used: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    execution_order: List[str] = Field(default_factory=list)
    estimated_runtime_ms: int = 1200
    estimated_cost_usd: float = 0.0004
    potential_failures: List[str] = Field(default_factory=list)
    optimization_suggestions: List[str] = Field(default_factory=list)
    connector_descriptions: Dict[str, str] = Field(default_factory=dict)
    markdown_report: str = ""


class WorkflowExplainer:
    """
    AgentFlow AI - AI Workflow Explainer & Optimization Engine
    Analyzes DAG graphs, generating step-by-step natural language explanations, execution order,
    estimated runtime & cost telemetry, potential failures, optimization tips, and Markdown reports.
    """

    CONNECTOR_DESCRIPTIONS = {
        "Gmail": "Google Mail API connector for sending and reading messages.",
        "Slack": "Slack API connector for post messaging and team notifications.",
        "Google Sheets": "Google Sheets API connector for reading and updating row matrices.",
        "Google Drive": "Google Drive API connector for file uploads and folder storage.",
        "GitHub": "GitHub REST/GraphQL API connector for managing repositories and PRs.",
        "AI": "OpenAI / Gemini LLM API connector for text summarization and extraction.",
        "Webhook": "HTTP Webhook trigger listener endpoint.",
        "Schedule": "Cron schedule trigger for automated recurring execution.",
        "Condition": "Logical evaluation node for IF/ELSE branching.",
        "Loop": "Iteration node for looping over arrays and collections.",
        "Merge": "Control flow node for joining parallel execution branches.",
        "Generic REST": "Generic HTTP REST request client for custom API endpoints.",
    }

    def explain_workflow(self, workflow_graph: Dict[str, Any]) -> ExplanationResult:
        nodes = workflow_graph.get("nodes", [])
        edges = workflow_graph.get("edges", [])
        trigger = workflow_graph.get("trigger", {})

        title = workflow_graph.get("title", "Automated Workflow")
        intent = workflow_graph.get("intent", "AUTOMATION")

        summary = f"Workflow '{title}' automatically executes {len(nodes)} step(s) triggered via {trigger.get('type', 'Manual')} trigger."

        step_explanations: List[StepExplanation] = []
        execution_order: List[str] = []
        variables_used: List[str] = []
        dependencies: List[str] = []
        conn_descs: Dict[str, str] = {}
        potential_failures: List[str] = []
        optimizations: List[str] = []

        for edge in edges:
            src = edge.get("source", "")
            tgt = edge.get("target", "")
            dependencies.append(f"{src} -> {tgt}")

        for idx, node in enumerate(nodes):
            nid = node.get("id", f"step_{idx+1}")
            provider = node.get("provider", "Generic")
            op_id = node.get("operation_id", "action")
            label = node.get("label", nid)

            execution_order.append(nid)

            if provider in self.CONNECTOR_DESCRIPTIONS:
                conn_descs[provider] = self.CONNECTOR_DESCRIPTIONS[provider]

            exp_text = f"Step {idx+1} ({label}) uses provider '{provider}' executing operation '{op_id}'."
            step_explanations.append(
                StepExplanation(
                    step_id=nid,
                    label=label,
                    provider=provider,
                    operation=op_id,
                    explanation=exp_text,
                )
            )

            # Scan parameters for variables
            params = node.get("parameters", {})
            for v in params.values():
                if isinstance(v, str) and "{{" in v:
                    variables_used.append(v)

            # Scan potential failures
            if provider in ["Gmail", "Slack", "Google Drive", "Google Sheets", "GitHub"]:
                potential_failures.append(f"Provider '{provider}' requires OAuth2 token refresh if token expires.")
            if provider == "Generic REST":
                potential_failures.append("Target REST endpoint may return HTTP 500 or timeout.")

        # Optimizations
        if len(nodes) > 3:
            optimizations.append("Consider grouping sequential read operations to reduce API overhead.")
        if "Loop" in [n.get("provider") for n in nodes]:
            optimizations.append("Enable batching on Loop items to accelerate execution speed.")
        if not optimizations:
            optimizations.append("Workflow graph topology is optimal for single-pass execution.")

        est_runtime_ms = max(300, len(nodes) * 280)
        est_cost_usd = round(len(nodes) * 0.0001, 5)

        # Build Markdown Report
        md_lines = [
            f"# 📖 Workflow Explanation Report: {title}",
            "",
            f"**Summary:** {summary}",
            "",
            "## ⏱️ Telemetry & Cost Estimates",
            f"- **Estimated Runtime:** `{est_runtime_ms} ms`",
            f"- **Estimated Execution Cost:** `${est_cost_usd}`",
            f"- **Total Execution Steps:** `{len(nodes)}`",
            "",
            "## 🔄 Execution Order & Steps",
        ]

        for se in step_explanations:
            md_lines.append(f"1. **{se.label}** (`{se.step_id}`) - *{se.provider}* ({se.operation}): {se.explanation}")

        if variables_used:
            md_lines.extend(["", "## 🔑 Variables Referenced"])
            for var in set(variables_used):
                md_lines.append(f"- `{var}`")

        if potential_failures:
            md_lines.extend(["", "## ⚠️ Potential Failure Modes"])
            for pf in potential_failures:
                md_lines.append(f"- {pf}")

        if optimizations:
            md_lines.extend(["", "## 🚀 Optimization Suggestions"])
            for opt in optimizations:
                md_lines.append(f"- {opt}")

        markdown_report = "\n".join(md_lines)

        return ExplanationResult(
            summary=summary,
            step_explanations=step_explanations,
            variables_used=list(set(variables_used)),
            dependencies=dependencies,
            execution_order=execution_order,
            estimated_runtime_ms=est_runtime_ms,
            estimated_cost_usd=est_cost_usd,
            potential_failures=potential_failures,
            optimization_suggestions=optimizations,
            connector_descriptions=conn_descs,
            markdown_report=markdown_report,
        )


workflow_explainer = WorkflowExplainer()
