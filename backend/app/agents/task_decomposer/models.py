from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DecomposedTask(BaseModel):
    step: int = Field(description="1-indexed execution step order")
    name: str = Field(description="Human readable title of the atomic task")
    provider: str = Field(description="Target provider e.g. gmail, drive, slack, github, schedule, ai")
    operation: str = Field(description="Target operation ID e.g. gmail.messages.send, gmail.messages.list, ai.email_writer")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Task parameters or dependency references")
    depends_on: List[int] = Field(default_factory=list, description="Step indices this task depends on")
    read_only: bool = Field(default=True, description="Whether this individual task operation is read-only")
    side_effect: bool = Field(default=False, description="Whether this task modifies system state")


class TaskDecompositionResult(BaseModel):
    prompt: str
    intent: str
    tasks: List[DecomposedTask] = Field(default_factory=list)
    reasoning: str = Field(default="")
