import logging
from typing import Any, Dict
from app.agents.optimizer.workflow_optimizer import workflow_optimizer_engine, OptimizationAnalysisResult

logger = logging.getLogger("agentflow.agents.optimizer.service")


class OptimizerAIService:
    """Service serving AI workflow optimization and one-click graph transformation."""

    def analyze(self, workflow_graph: Dict[str, Any]) -> OptimizationAnalysisResult:
        """Analyzes graph topology and generates speedup & cost reduction suggestions."""
        return workflow_optimizer_engine.analyze_and_optimize(workflow_graph)

    def apply_optimization(self, workflow_graph: Dict[str, Any]) -> Dict[str, Any]:
        """Applies one-click graph optimization directly to workflow DAG."""
        return workflow_optimizer_engine.apply_one_click_optimization(workflow_graph)


optimizer_ai_service = OptimizerAIService()
