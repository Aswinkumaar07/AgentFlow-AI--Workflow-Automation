import pytest
from app.agents.graph import langgraph_orchestrator
from app.agents.registry import provider_registry
from app.agents.tools import validator_tool

@pytest.mark.asyncio
async def test_provider_registry_default_mvp():
    providers = provider_registry.list_providers()
    assert "github" in providers
    assert "slack" in providers
    assert "gmail" in providers
    assert "drive" in providers
    assert "sheets" in providers
    assert "notion" in providers

@pytest.mark.asyncio
async def test_langgraph_orchestrator_pipeline():
    prompt = "Summarize GitHub PRs and post to Slack"
    state = await langgraph_orchestrator.run(prompt)

    assert state["user_prompt"] == prompt
    assert len(state["logs"]) > 0
    assert state["is_valid"] is True
    assert "nodes" in state["workflow_json"]

@pytest.mark.asyncio
async def test_workflow_validator_tool():
    valid_dag = {
        "nodes": [{"id": "n1"}, {"id": "n2"}],
        "edges": [{"source": "n1", "target": "n2"}]
    }
    report = validator_tool.validate(valid_dag)
    assert report["is_valid"] is True
    assert len(report["errors"]) == 0
