from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PositionModel(BaseModel):
    x: float = Field(default=250.0)
    y: float = Field(default=100.0)


class DAGNodeModel(BaseModel):
    id: str = Field(description="Node unique ID e.g. step_1")
    step_id: str = Field(description="Step ID e.g. step_1")
    label: str = Field(description="Human readable display label")
    type: str = Field(default="action", description="Node type: trigger, action, condition, loop")
    provider: str = Field(description="Provider name e.g. gmail, slack, drive, schedule")
    operation: str = Field(description="Operation ID e.g. gmail.messages.send")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    position: PositionModel = Field(default_factory=PositionModel)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="UI visualization metadata (icon, color, category)")


class DAGEdgeModel(BaseModel):
    id: str = Field(description="Edge unique ID e.g. e1-2")
    source: str = Field(description="Source node ID")
    target: str = Field(description="Target node ID")
    condition_branch: Optional[str] = Field(default=None, description="Branch label e.g. true, false")


class WorkflowGraphResult(BaseModel):
    nodes: List[DAGNodeModel] = Field(default_factory=list)
    edges: List[DAGEdgeModel] = Field(default_factory=list)
    visualization: Dict[str, Any] = Field(default_factory=dict)
