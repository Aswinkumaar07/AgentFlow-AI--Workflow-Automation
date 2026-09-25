import uuid
from typing import Optional, Any
from sqlalchemy import String, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

class ActivityLog(BaseModel):
    __tablename__ = "activity_logs"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False) # workflow_created, workflow_executed, login, etc.
    description: Mapped[str] = mapped_column(Text, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    extra_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(50), default="info", nullable=False) # info, success, warning, error
    read: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    link: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

class Settings(BaseModel):
    __tablename__ = "settings"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    theme: Mapped[str] = mapped_column(String(20), default="dark", nullable=False)
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    webhook_notifications: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_heal_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_parallel_executions: Mapped[int] = mapped_column(default=5, nullable=False)
    extra_preferences: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    entity_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False) # User, Workflow, APIKey
    entity_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(50), index=True, nullable=False) # CREATE, UPDATE, DELETE
    changes: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
