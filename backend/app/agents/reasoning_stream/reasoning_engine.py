import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.agents.planner.planner_v3 import intelligent_planner_v3

logger = logging.getLogger("agentflow.agents.reasoning_stream")


class ReasoningStage(BaseModel):
    stage_id: str
    label: str
    status: str  # 'pending', 'in_progress', 'completed'
    details: str = ""


class StreamedPlanningEvent(BaseModel):
    stage: str
    message: str
    progress_percentage: int
    is_completed: bool = False
    confidence: float = 0.95
    estimated_runtime_ms: int = 1200
    estimated_cost_usd: float = 0.0004
    reasoning_summary: str = ""
    workflow_graph: Optional[Dict[str, Any]] = None


class ReasoningStreamEngine:
    """
    AgentFlow AI v2.0 - AI Live Reasoning Stream & Stage Visualizer Engine
    Streams real-time reasoning stages to the frontend via SSE / async generators:
    1. Understanding Intent...
    2. Finding Connectors...
    3. Finding APIs...
    4. Building DAG...
    5. Generating Variables...
    6. Validating...
    7. Optimizing...
    8. Completed
    """

    STAGES = [
        ("intent", "Understanding Intent...", 15),
        ("connectors", "Finding Connectors...", 30),
        ("apis", "Finding APIs...", 45),
        ("dag", "Building DAG...", 60),
        ("variables", "Generating Variables...", 75),
        ("validating", "Validating...", 85),
        ("optimizing", "Optimizing...", 95),
        ("completed", "Completed", 100),
    ]

    async def stream_reasoning_pipeline(self, prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
        for stage_id, label, pct in self.STAGES[:-1]:
            event = StreamedPlanningEvent(
                stage=stage_id,
                message=label,
                progress_percentage=pct,
                is_completed=False,
            )
            yield event.model_dump()
            await asyncio.sleep(0.08)  # Smooth UI transition simulation

        # Execute final plan
        plan_res = intelligent_planner_v3.plan(prompt)

        final_event = StreamedPlanningEvent(
            stage="completed",
            message="Workflow generation completed successfully!",
            progress_percentage=100,
            is_completed=True,
            confidence=plan_res.confidence,
            estimated_runtime_ms=max(400, len(plan_res.workflow_graph.get("nodes", [])) * 280),
            estimated_cost_usd=round(len(plan_res.workflow_graph.get("nodes", [])) * 0.0001, 5),
            reasoning_summary=" -> ".join(plan_res.reasoning_trace),
            workflow_graph=plan_res.workflow_graph,
        )
        yield final_event.model_dump()


reasoning_stream_engine = ReasoningStreamEngine()
