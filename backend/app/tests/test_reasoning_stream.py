import pytest
from app.agents.reasoning_stream import reasoning_stream_engine, StreamedPlanningEvent


@pytest.mark.asyncio
async def test_reasoning_stream_pipeline():
    prompt = "Send a good morning email to john@example.com"
    events = []

    async for evt in reasoning_stream_engine.stream_reasoning_pipeline(prompt):
        events.append(evt)

    assert len(events) >= 8
    assert events[0]["stage"] == "intent"
    assert events[-1]["stage"] == "completed"
    assert events[-1]["is_completed"] is True
    assert events[-1]["confidence"] > 0.8
    assert events[-1]["workflow_graph"] is not None
