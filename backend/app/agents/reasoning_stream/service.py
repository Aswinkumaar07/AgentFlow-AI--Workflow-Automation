import logging
from typing import AsyncGenerator, Dict, Any
from app.agents.reasoning_stream.reasoning_engine import reasoning_stream_engine

logger = logging.getLogger("agentflow.agents.reasoning_stream.service")


class ReasoningStreamService:
    """Service serving AI live reasoning stages and SSE streaming generator."""

    async def stream_plan(self, prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Async generator streaming live planning stages."""
        async for event in reasoning_stream_engine.stream_reasoning_pipeline(prompt):
            yield event


reasoning_stream_service = ReasoningStreamService()
