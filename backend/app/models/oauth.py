import time
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class OAuthConnectionModel(BaseModel):
    """Database model representation for an OAuth connection."""

    id: str = Field(..., description="Unique connection ID.")
    user_id: str = Field(..., description="User ID owner.")
    provider: str = Field(..., description="Provider name (e.g. Google, Slack, GitHub).")
    access_token: str = Field(..., description="OAuth Access token (encrypted in store).")
    refresh_token: Optional[str] = Field(default=None, description="OAuth Refresh token.")
    expires_at: Optional[float] = Field(default=None, description="Token expiration epoch timestamp.")
    scopes: List[str] = Field(default_factory=list, description="Authorized OAuth scopes.")
    status: str = Field(default="CONNECTED", description="Connection status.")
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    model_config = ConfigDict(arbitrary_types_allowed=True)
