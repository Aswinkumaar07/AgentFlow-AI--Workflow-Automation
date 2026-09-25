import logging
from typing import Any, Dict
from app.agents.explainer.workflow_explainer import workflow_explainer, ExplanationResult

logger = logging.getLogger("agentflow.agents.explainer.service")


class ExplainerAIService:
    """AI Explainer Service serving step breakdowns, cost & runtime telemetry, and Markdown reports."""

    def explain(self, workflow_graph: Dict[str, Any]) -> ExplanationResult:
        """Explains workflow graph returning structured ExplanationResult."""
        res = workflow_explainer.explain_workflow(workflow_graph)
        logger.info(f"AI Workflow Explainer generated report for '{workflow_graph.get('title')}' ({len(res.step_explanations)} steps).")
        return res


explainer_ai_service = ExplainerAIService()
