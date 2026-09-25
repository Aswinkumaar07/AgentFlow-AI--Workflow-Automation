import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=512)

class UserSettingsUpdateRequest(BaseModel):
    theme: Optional[str] = Field("dark", pattern="^(dark|light|system)$")
    email_notifications: Optional[bool] = True
    webhook_notifications: Optional[bool] = False
    auto_heal_enabled: Optional[bool] = True
    max_parallel_executions: Optional[int] = Field(5, ge=1, le=20)

class UserSettingsResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    theme: str
    email_notifications: bool
    webhook_notifications: bool
    auto_heal_enabled: bool
    max_parallel_executions: int

    model_config = ConfigDict(from_attributes=True)
