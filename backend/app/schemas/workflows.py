import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict

class WorkflowCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255, description="Workflow title")
    description: Optional[str] = Field(None, max_length=2000, description="Workflow description")
    trigger_type: str = Field("manual", description="Trigger type: manual, webhook, cron, event")
    definition: Dict[str, Any] = Field(default_factory=dict, description="DAG Definition object containing nodes & edges")

class WorkflowUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = Field(None, pattern="^(draft|active|paused|archived)$")
    trigger_type: Optional[str] = Field(None)
    definition: Optional[Dict[str, Any]] = None

class WorkflowResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: str
    version: int
    trigger_type: str
    definition: Dict[str, Any]
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WorkflowExecutionRequest(BaseModel):
    input_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Input variables for workflow execution")

class ExecutionLogResponse(BaseModel):
    id: uuid.UUID
    node_id: Optional[str] = None
    level: str
    message: str
    payload: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WorkflowExecutionResponse(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    status: str
    trigger_source: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
