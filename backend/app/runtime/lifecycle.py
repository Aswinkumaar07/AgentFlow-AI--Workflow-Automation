from enum import Enum
from typing import Dict, Set
from app.runtime.exceptions import RuntimeException


class WorkflowLifecycleState(str, Enum):
    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    ROLLING_BACK = "ROLLING_BACK"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class WorkflowLifecycle:
    """State Machine validating allowable workflow state transitions."""

    VALID_TRANSITIONS: Dict[WorkflowLifecycleState, Set[WorkflowLifecycleState]] = {
        WorkflowLifecycleState.CREATED: {WorkflowLifecycleState.VALIDATING, WorkflowLifecycleState.CANCELLED},
        WorkflowLifecycleState.VALIDATING: {WorkflowLifecycleState.READY, WorkflowLifecycleState.FAILED, WorkflowLifecycleState.CANCELLED},
        WorkflowLifecycleState.READY: {WorkflowLifecycleState.RUNNING, WorkflowLifecycleState.CANCELLED},
        WorkflowLifecycleState.RUNNING: {WorkflowLifecycleState.WAITING, WorkflowLifecycleState.PAUSED, WorkflowLifecycleState.FAILED, WorkflowLifecycleState.ROLLING_BACK, WorkflowLifecycleState.COMPLETED, WorkflowLifecycleState.CANCELLED},
        WorkflowLifecycleState.WAITING: {WorkflowLifecycleState.RUNNING, WorkflowLifecycleState.FAILED, WorkflowLifecycleState.CANCELLED},
        WorkflowLifecycleState.PAUSED: {WorkflowLifecycleState.RUNNING, WorkflowLifecycleState.CANCELLED},
        WorkflowLifecycleState.FAILED: {WorkflowLifecycleState.ROLLING_BACK, WorkflowLifecycleState.RUNNING, WorkflowLifecycleState.CANCELLED},
        WorkflowLifecycleState.ROLLING_BACK: {WorkflowLifecycleState.FAILED, WorkflowLifecycleState.CANCELLED},
        WorkflowLifecycleState.COMPLETED: set(),
        WorkflowLifecycleState.CANCELLED: set(),
    }

    @classmethod
    def validate_transition(cls, current: WorkflowLifecycleState, target: WorkflowLifecycleState) -> bool:
        if current == target:
            return True

        allowed = cls.VALID_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise RuntimeException(f"Invalid workflow state transition from [{current.value}] to [{target.value}].")
        return True
