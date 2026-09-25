import logging
from typing import Any, Dict, List
from app.agents.visual_runtime.runtime_visualizer import visual_runtime_engine, ExecutionTimelineSnapshot

logger = logging.getLogger("agentflow.agents.visual_runtime.service")


class VisualRuntimeService:
    """Service serving visual execution timeline, node animations, and step inspection."""

    def start_execution_visuals(self, execution_id: str, nodes: List[Dict[str, Any]]) -> ExecutionTimelineSnapshot:
        """Initializes visual execution snapshot with pending node statuses."""
        return visual_runtime_engine.initialize_execution(execution_id, nodes)

    def record_node_event(
        self,
        execution_id: str,
        node_id: str,
        status: str,
        latency_ms: int = 0,
        retries: int = 0,
        output_response: Dict[str, Any] = None,
        log_message: str = None,
    ) -> ExecutionTimelineSnapshot:
        """Updates live node status, color, latency, and logs."""
        return visual_runtime_engine.update_node_status(
            execution_id, node_id, status, latency_ms, retries, output_response, log_message
        )

    def get_timeline_snapshot(self, execution_id: str) -> ExecutionTimelineSnapshot:
        """Retrieves timeline snapshot for replay or step inspection."""
        return visual_runtime_engine.get_timeline(execution_id)


visual_runtime_service = VisualRuntimeService()
