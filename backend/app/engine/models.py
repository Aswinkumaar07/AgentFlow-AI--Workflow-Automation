import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class WorkflowStatus(str, Enum):
    """Workflow Execution Status States."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"
    CANCELLED = "CANCELLED"


class StepType(str, Enum):
    """Workflow Step Types."""

    CONNECTOR_ACTION = "CONNECTOR_ACTION"
    CONDITION = "CONDITION"
    PARALLEL = "PARALLEL"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    TRANSFORMATION = "TRANSFORMATION"


class StepDefinitionModel(BaseModel):
    """Step definition inside a Workflow Definition."""

    step_id: str = Field(..., description="Unique step identifier (e.g., step_1).")
    step_type: StepType = Field(default=StepType.CONNECTOR_ACTION, description="Step type enum.")
    provider: str = Field(default="Generic", description="Target provider (e.g. Gmail, Slack).")
    operation_id: str = Field(default="", description="Operation ID to execute.")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Step parameters.")
    dependencies: List[str] = Field(default_factory=list, description="IDs of prerequisite steps.")
    retry_attempts: int = Field(default=3, description="Maximum retry attempts.")
    timeout_seconds: float = Field(default=30.0, description="Step execution timeout.")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class WorkflowDefinitionModel(BaseModel):
    """Workflow Definition DAG Specification."""

    workflow_id: str = Field(..., description="Unique workflow identifier.")
    name: str = Field(..., description="Human-readable workflow name.")
    version: str = Field(default="v1", description="Workflow version.")
    tenant_id: str = Field(default="default", description="Tenant owner ID.")
    steps: List[StepDefinitionModel] = Field(default_factory=list, description="List of DAG steps.")
    cron_schedule: Optional[str] = Field(default=None, description="Optional cron schedule expression.")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class StepExecutionStateModel(BaseModel):
    """State record for a single step execution."""

    step_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    result_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None
    retries_used: int = 0


class WorkflowExecutionStateModel(BaseModel):
    """State record for an entire workflow execution instance."""

    execution_id: str = Field(..., description="Unique execution instance ID.")
    workflow_id: str
    tenant_id: str = "default"
    status: WorkflowStatus = WorkflowStatus.PENDING
    step_states: Dict[str, StepExecutionStateModel] = Field(default_factory=dict)
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None
    context_data: Dict[str, Any] = Field(default_factory=dict)
