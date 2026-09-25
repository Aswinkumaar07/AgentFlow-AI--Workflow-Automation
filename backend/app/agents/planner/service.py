from typing import Any, Dict, Optional
from app.agents.planner.interface import BasePlannerService
from app.agents.planner.planner_v4 import intelligent_planner_v4


class PlannerAgent(BasePlannerService):
    """Planner Agent Node converting natural language prompts into structured execution plans via Planner V4."""

    async def create_execution_plan(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generates an execution plan using Intelligent Workflow Planning Engine V4 pure reasoning pipeline."""
        plan_v4 = intelligent_planner_v4.plan(prompt, context)

        wf_graph = plan_v4.workflow_graph
        nodes = wf_graph.get("nodes", [])
        edges = wf_graph.get("edges", [])

        return {
            "title": wf_graph.get("title", prompt.capitalize()),
            "description": wf_graph.get("description", ""),
            "intent": plan_v4.intent,
            "goal": prompt,
            "entities": plan_v4.entities,
            "trigger": wf_graph.get("trigger", {}),
            "services": plan_v4.selected_connectors,
            "selected_operations": plan_v4.selected_operations,
            "tasks": nodes,
            "nodes": nodes,
            "edges": edges,
            "variables": plan_v4.variables,
            "missing_inputs": plan_v4.missing_inputs,
            "confidence_score": plan_v4.confidence,
            "reasoning_trace": plan_v4.reasoning_trace,
        }


planner_agent = PlannerAgent()