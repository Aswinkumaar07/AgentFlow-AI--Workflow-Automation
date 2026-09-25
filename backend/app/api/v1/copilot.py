from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, status
from app.dependencies.auth import get_current_user
from app.models.users import User
from app.core.response import success_response
from app.agents.copilot import copilot_ai_service

router = APIRouter(prefix="/copilot", tags=["AI Copilot"])


class CopilotChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique conversation session ID")
    message: str = Field(..., description="User chat message string")


@router.post("/chat", status_code=status.HTTP_200_OK)
async def copilot_chat_turn(
    req: CopilotChatRequest,
    current_user: User = Depends(get_current_user),
):
    """Process a multi-turn conversation step with AI Copilot Assistant."""
    result = copilot_ai_service.chat_turn(req.session_id, req.message)
    return success_response(data=result, message="Copilot turn processed successfully")


@router.get("/sessions/{session_id}", status_code=status.HTTP_200_OK)
async def get_copilot_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get conversation session history and collected entities."""
    history = copilot_ai_service.get_session_history(session_id)
    return success_response(data=history, message="Copilot session history retrieved successfully")


@router.delete("/sessions/{session_id}", status_code=status.HTTP_200_OK)
async def reset_copilot_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """Reset or clear a conversation session."""
    res = copilot_ai_service.reset_session(session_id)
    return success_response(data=res, message="Copilot session reset successfully")
