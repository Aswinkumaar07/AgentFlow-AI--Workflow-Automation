import logging
import time
from typing import Any, Dict, Optional
from app.engine.models import WorkflowStatus
from app.engine.state_machine import state_machine

logger = logging.getLogger("agentflow.engine.human.approval")


class HumanApprovalHandler:
    """Enterprise Human Approval Step Handler managing workflow pauses and resume events."""

    def __init__(self) -> None:
        self.state_store = state_machine

    async def pause_for_approval(self, execution_id: str, step_id: str) -> None:
        """Transitions step and workflow state to WAITING_FOR_APPROVAL."""
        logger.info(f"Pausing workflow execution [{execution_id}] for human approval at step [{step_id}]...")
        state = await self.state_store.get_state(execution_id)
        if state:
            state.status = WorkflowStatus.WAITING_FOR_APPROVAL
            await self.state_store.transition_step(
                execution_id, step_id, WorkflowStatus.WAITING_FOR_APPROVAL, {"approval_required": True}
            )

    async def approve_step(self, execution_id: str, step_id: str, approver_id: str = "admin") -> bool:
        """Approves pending step and resumes workflow execution."""
        logger.info(f"Human approval granted by [{approver_id}] for step [{step_id}] in execution [{execution_id}].")
        state = await self.state_store.get_state(execution_id)
        if not state:
            return False

        state.status = WorkflowStatus.RUNNING
        await self.state_store.transition_step(
            execution_id, step_id, WorkflowStatus.COMPLETED, {"approved_by": approver_id, "approved_at": time.time()}
        )
        return True


human_approval_handler = HumanApprovalHandler()
