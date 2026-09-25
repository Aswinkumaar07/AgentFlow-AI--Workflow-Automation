import json
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from app.dependencies.auth import get_current_user
from app.models.users import User
from app.agents.reasoning_stream import reasoning_stream_service

router = APIRouter(prefix="/reasoning", tags=["Live Reasoning Stream"])


class StreamReasoningRequest(BaseModel):
    prompt: str = Field(..., description="Natural language workflow prompt")


@router.post("/stream", status_code=status.HTTP_200_OK)
async def stream_reasoning_pipeline_endpoint(
    req: StreamReasoningRequest,
    current_user: User = Depends(get_current_user),
):
    """Stream live AI reasoning stages, confidence, runtime/cost telemetry, and DAG graph via SSE."""

    async def event_generator():
        async for event in reasoning_stream_service.stream_plan(req.prompt):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
