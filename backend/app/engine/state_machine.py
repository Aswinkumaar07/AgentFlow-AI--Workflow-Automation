import asyncio
import logging
import threading
from typing import Dict, Optional
from app.engine.interfaces import BaseWorkflowStateStore
from app.engine.models import (
    StepExecutionStateModel,
    WorkflowExecutionStateModel,
    WorkflowStatus,
)

logger = logging.getLogger("agentflow.engine.state_machine")


class WorkflowStateMachine(BaseWorkflowStateStore):
    """Thread-safe State Machine with Persistent Execution Checkpoint Storage."""

    def __init__(self) -> None:
        self._states: Dict[str, WorkflowExecutionStateModel] = {}
        self._lock = threading.Lock()

    async def save_state(self, state: WorkflowExecutionStateModel) -> None:
        with self._lock:
            self._states[state.execution_id] = state
            logger.debug(f"Saved state checkpoint for execution [{state.execution_id}]: status={state.status.value}")

    async def get_state(self, execution_id: str) -> Optional[WorkflowExecutionStateModel]:
        with self._lock:
            return self._states.get(execution_id)

    async def transition_step(
        self, execution_id: str, step_id: str, status: WorkflowStatus, result_data: Optional[Dict] = None, error_message: Optional[str] = None
    ) -> None:
        state = await self.get_state(execution_id)
        if not state:
            return

        with self._lock:
            if step_id not in state.step_states:
                state.step_states[step_id] = StepExecutionStateModel(step_id=step_id)

            step_state = state.step_states[step_id]
            step_state.status = status
            if result_data:
                step_state.result_data.update(result_data)
            if error_message:
                step_state.error_message = error_message

        await self.save_state(state)


state_machine = WorkflowStateMachine()
