import uuid
from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy import String, Boolean, ForeignKey, Text, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel

class Workflow(BaseModel):
    __tablename__ = "workflows"

    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", index=True, nullable=False) # draft, active, paused, archived
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # DAG Definition JSON (Nodes & Edges)
    definition: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(50), default="manual", index=True, nullable=False) # manual, webhook, cron, event

    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    owner: Mapped["User"] = relationship("User", back_populates="workflows")

    executions: Mapped[List["WorkflowExecution"]] = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")

class WorkflowExecution(BaseModel):
    __tablename__ = "workflow_executions"

    workflow_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workflows.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True, nullable=False) # pending, running, completed, failed, cancelled
    trigger_source: Mapped[str] = mapped_column(String(100), default="manual", nullable=False)
    
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    input_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    workflow: Mapped[Workflow] = relationship(Workflow, back_populates="executions")
    logs: Mapped[List["ExecutionLog"]] = relationship("ExecutionLog", back_populates="execution", cascade="all, delete-orphan")

class ExecutionLog(BaseModel):
    __tablename__ = "execution_logs"

    execution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workflow_executions.id", ondelete="CASCADE"), index=True, nullable=False)
    node_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    level: Mapped[str] = mapped_column(String(20), default="INFO", nullable=False, index=True) # INFO, WARNING, ERROR, DEBUG
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    execution: Mapped[WorkflowExecution] = relationship(WorkflowExecution, back_populates="logs")

class WorkflowTemplate(BaseModel):
    __tablename__ = "workflow_templates"

    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False) # DevOps, Marketing, Sales, Support
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    definition: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
