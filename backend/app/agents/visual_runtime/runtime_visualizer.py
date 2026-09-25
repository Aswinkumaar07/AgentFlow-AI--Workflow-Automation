import time
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agentflow.agents.visual_runtime")


class NodeExecutionStep(BaseModel):
    step_id: str
    node_id: str
    label: str
    provider: str
    operation: str
    status: str = "Pending"  # 'Pending' (Blue), 'Running' (Yellow), 'Success' (Green), 'Failed' (Red), 'Waiting' (Orange)
    status_color: str = "#3B82F6"  # Blue hex by default
    latency_ms: int = 0
    retries: int = 0
    input_payload: Dict[str, Any] = Field(default_factory=dict)
    output_response: Dict[str, Any] = Field(default_factory=dict)
    logs: List[str] = Field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class ExecutionTimelineSnapshot(BaseModel):
    execution_id: str
    status: str = "running"
    total_duration_ms: int = 0
    active_node_id: str = ""
    steps: List[NodeExecutionStep] = Field(default_factory=list)
    runtime_variables: Dict[str, Any] = Field(default_factory=dict)
    animated_edges: List[str] = Field(default_factory=list)


class VisualRuntimeEngine:
    """
    AgentFlow AI v2.0 - Visual Runtime Engine
    Tracks real-time node state color coding, latency, retries, input/output payloads,
    animated edges, and execution timelines for replay and step inspection.
    """

    COLOR_MAP = {
        "Pending": "#3B82F6",   # Blue
        "Running": "#EAB308",   # Yellow
        "Success": "#22C55E",   # Green
        "Failed": "#EF4444",    # Red
        "Waiting": "#F97316",   # Orange
    }

    def __init__(self) -> None:
        self.snapshots: Dict[str, ExecutionTimelineSnapshot] = {}

    def initialize_execution(self, execution_id: str, nodes: List[Dict[str, Any]]) -> ExecutionTimelineSnapshot:
        steps = []
        for idx, node in enumerate(nodes):
            nid = node.get("id", f"node_{idx}")
            steps.append(
                NodeExecutionStep(
                    step_id=f"step_{nid}",
                    node_id=nid,
                    label=node.get("label", nid),
                    provider=node.get("provider", "Generic"),
                    operation=node.get("operation_id", "action"),
                    status="Pending",
                    status_color=self.COLOR_MAP["Pending"],
                    input_payload=node.get("parameters", {}),
                )
            )

        snap = ExecutionTimelineSnapshot(execution_id=execution_id, steps=steps)
        self.snapshots[execution_id] = snap
        return snap

    def update_node_status(
        self,
        execution_id: str,
        node_id: str,
        status: str,
        latency_ms: int = 0,
        retries: int = 0,
        output_response: Optional[Dict[str, Any]] = None,
        log_message: Optional[str] = None,
    ) -> ExecutionTimelineSnapshot:
        snap = self.snapshots.get(execution_id)
        if not snap:
            return ExecutionTimelineSnapshot(execution_id=execution_id)

        snap.active_node_id = node_id
        for step in snap.steps:
            if step.node_id == node_id:
                step.status = status
                step.status_color = self.COLOR_MAP.get(status, "#3B82F6")
                step.latency_ms = latency_ms
                step.retries = retries
                if output_response:
                    step.output_response = output_response
                if log_message:
                    step.logs.append(log_message)

        self.snapshots[execution_id] = snap
        return snap

    def get_timeline(self, execution_id: str) -> ExecutionTimelineSnapshot:
        return self.snapshots.get(execution_id, ExecutionTimelineSnapshot(execution_id=execution_id))


visual_runtime_engine = VisualRuntimeEngine()
