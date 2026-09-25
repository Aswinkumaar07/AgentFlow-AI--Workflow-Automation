from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class IntentCategory(str, Enum):
    READ_ONLY = "READ_ONLY"
    SEARCH = "SEARCH"
    SEND = "SEND"
    REPLY = "REPLY"
    FORWARD = "FORWARD"
    DELETE = "DELETE"
    MODIFY = "MODIFY"
    DRAFT = "DRAFT"
    SCHEDULE = "SCHEDULE"
    MULTI_STEP = "MULTI_STEP"
    UNKNOWN = "UNKNOWN"


class IntentType(str, Enum):
    EMAIL_SEND = "EMAIL_SEND"
    EMAIL_GENERATE = "EMAIL_GENERATE"
    EMAIL_REPLY = "EMAIL_REPLY"
    EMAIL_FORWARD = "EMAIL_FORWARD"
    EMAIL_READ = "EMAIL_READ"
    EMAIL_READ_LATEST = "EMAIL_READ_LATEST"
    EMAIL_READ_UNREAD = "EMAIL_READ_UNREAD"
    EMAIL_SEARCH = "EMAIL_SEARCH"
    EMAIL_SEARCH_BY_SENDER = "EMAIL_SEARCH_BY_SENDER"
    EMAIL_SEARCH_BY_SUBJECT = "EMAIL_SEARCH_BY_SUBJECT"
    EMAIL_SUMMARIZE = "EMAIL_SUMMARIZE"
    EMAIL_DELETE = "EMAIL_DELETE"
    EMAIL_MARK_READ = "EMAIL_MARK_READ"
    EMAIL_MARK_UNREAD = "EMAIL_MARK_UNREAD"
    EMAIL_DRAFT = "EMAIL_DRAFT"
    EMAIL_SCHEDULE = "EMAIL_SCHEDULE"

    DRIVE_UPLOAD = "DRIVE_UPLOAD"
    DRIVE_DOWNLOAD = "DRIVE_DOWNLOAD"

    SLACK_SEND = "SLACK_SEND"

    GITHUB_CREATE_ISSUE = "GITHUB_CREATE_ISSUE"

    CALENDAR_CREATE_EVENT = "CALENDAR_CREATE_EVENT"

    MULTI_STEP_WORKFLOW = "MULTI_STEP_WORKFLOW"

    UNKNOWN = "UNKNOWN"


class IntentClassificationResult(BaseModel):
    intent: IntentType
    category: IntentCategory = Field(default=IntentCategory.READ_ONLY)
    confidence: float = Field(ge=0.0, le=1.0, default=0.95)
    reasoning: str = Field(default="")
    entities: Dict[str, Any] = Field(default_factory=dict)
    
    # AI-14 Semantic Flags
    side_effect: bool = Field(default=False)
    read_only: bool = Field(default=True)
    requires_message_lookup: bool = Field(default=False)
    requires_send: bool = Field(default=False)
    requires_reply: bool = Field(default=False)
    requires_modify: bool = Field(default=False)
