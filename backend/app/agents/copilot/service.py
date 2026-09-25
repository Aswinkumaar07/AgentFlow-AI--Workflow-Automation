import logging
from typing import Any, Dict
from app.agents.copilot.conversation_manager import conversation_manager
from app.agents.copilot.conversation_memory import conversation_memory_store

logger = logging.getLogger("agentflow.agents.copilot.service")


class CopilotAIService:
    """AI Copilot Service serving multi-turn chat sessions and session memory."""

    def chat_turn(self, session_id: str, message: str) -> Dict[str, Any]:
        """Processes a conversation turn and returns AI response."""
        return conversation_manager.process_turn(session_id, message)

    def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """Retrieves session history and collected parameters."""
        session = conversation_memory_store.get_or_create_session(session_id)
        return session.model_dump()

    def reset_session(self, session_id: str) -> Dict[str, Any]:
        """Resets conversation session."""
        conversation_memory_store.delete_session(session_id)
        return {"session_id": session_id, "reset": True}


copilot_ai_service = CopilotAIService()
