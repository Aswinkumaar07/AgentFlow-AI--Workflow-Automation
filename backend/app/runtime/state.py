import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class WorkflowExecutionStateV2(BaseModel):
    """Runtime Engine v2 Persistent Execution State representation."""

    execution_id: str
    workflow_id: str
    tenant_id: str = "usr_1"
    version_id: Optional[str] = None
    version_number: Optional[int] = None
    trigger_type: str = "manual"  # manual, scheduled, webhook, event
    status: str = "PENDING"  # PENDING, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED
    node_records: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    context_data: Dict[str, Any] = Field(default_factory=dict)
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
