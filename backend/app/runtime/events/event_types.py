import time
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class RuntimeEventType(str, Enum):
    WORKFLOW_STARTED = "WorkflowStarted"
    WORKFLOW_PAUSED = "WorkflowPaused"
    WORKFLOW_RESUMED = "WorkflowResumed"
    WORKFLOW_COMPLETED = "WorkflowCompleted"
    WORKFLOW_CANCELLED = "WorkflowCancelled"
    WORKFLOW_FAILED = "WorkflowFailed"
    NODE_STARTED = "NodeStarted"
    NODE_COMPLETED = "NodeCompleted"
    NODE_FAILED = "NodeFailed"
    NODE_RETRYING = "NodeRetrying"


class RuntimeEvent(BaseModel):
    event_type: RuntimeEventType
    execution_id: str
    workflow_id: str
    node_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)
