import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agentflow.agents.copilot.memory")


class UserPreferences(BaseModel):
    preferred_slack_channels: List[str] = Field(default_factory=lambda: ["#general", "#engineering"])
    preferred_drive_folders: List[str] = Field(default_factory=lambda: ["Invoices", "Reports"])
    preferred_email_signature: str = "Sent via AgentFlow AI Automation"
    connected_accounts: List[str] = Field(default_factory=lambda: ["Gmail", "Google Drive", "Google Sheets", "Slack", "GitHub"])
    recently_used_connectors: List[str] = Field(default_factory=lambda: ["Gmail", "Slack", "Google Sheets"])


class ConversationTurn(BaseModel):
    role: str  # 'user' or 'assistant'
    message: str
    timestamp: str
    suggested_replies: List[str] = Field(default_factory=list)


class ConversationSession(BaseModel):
    session_id: str
    user_goal: str = ""
    collected_entities: Dict[str, Any] = Field(default_factory=dict)
    missing_inputs: List[str] = Field(default_factory=list)
    history: List[ConversationTurn] = Field(default_factory=list)
    user_preferences: UserPreferences = Field(default_factory=UserPreferences)
    is_ready_to_generate: bool = False
    proposed_graph: Optional[Dict[str, Any]] = None


class ConversationMemoryStore:
    """In-memory conversation session and user preference store."""

    def __init__(self) -> None:
        self.sessions: Dict[str, ConversationSession] = {}

    def get_or_create_session(self, session_id: str) -> ConversationSession:
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationSession(session_id=session_id)
        return self.sessions[session_id]

    def update_session(self, session: ConversationSession) -> None:
        self.sessions[session.session_id] = session

    def delete_session(self, session_id: str) -> None:
        if session_id in self.sessions:
            del self.sessions[session_id]


conversation_memory_store = ConversationMemoryStore()
