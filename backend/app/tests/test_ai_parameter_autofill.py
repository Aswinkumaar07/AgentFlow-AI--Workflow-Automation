import pytest
from app.agents.parameter_autofill.parameter_autofill_engine import parameter_autofill_engine
from app.core.security import create_access_token


def test_entity_extraction_from_prompt():
    prompt_email = "Send good morning email to john@example.com"
    entities_1 = parameter_autofill_engine.extract_entities_from_prompt(prompt_email)
    assert entities_1["email"] == "john@example.com"
    assert entities_1["to"] == "john@example.com"

    prompt_slack = "Notify Slack #engineering with daily summary"
    entities_2 = parameter_autofill_engine.extract_entities_from_prompt(prompt_slack)
    assert entities_2["channel"] == "#engineering"

    prompt_cron = "Run backup every 5 minutes"
    entities_5 = parameter_autofill_engine.extract_entities_from_prompt(prompt_cron)
    assert entities_5["cron"] == "*/5 * * * *"


def test_autofill_node_confidence_scores_and_missing_params():
    # Prompt with email specified but missing required fields
    params_1, scores_1, missing_1 = parameter_autofill_engine.autofill_node(
        provider="Gmail",
        operation_id="gmail.messages.send",
        prompt="Send email to alice@company.com"
    )
    assert params_1["to"] == "alice@company.com"
    assert scores_1["to"] == 0.95

    # Prompt missing required recipient
    params_2, scores_2, missing_2 = parameter_autofill_engine.autofill_node(
        provider="Gmail",
        operation_id="gmail.messages.send",
        prompt="Send email notification"
    )
    assert "to" in missing_2
    assert scores_2["to"] == 0.0


def test_slack_channel_extraction_cases():
    # Case A: Hashtag with hyphen (#all-agentflow-ai)
    p_a = "Send a message to #all-agentflow-ai regarding release"
    ent_a = parameter_autofill_engine.extract_entities_from_prompt(p_a)
    assert ent_a["channel"] == "#all-agentflow-ai"

    # Case B: Plain text channel name (channel all-agentflow-ai / in all-agentflow-ai channel)
    p_b1 = "Send message to channel all-agentflow-ai"
    ent_b1 = parameter_autofill_engine.extract_entities_from_prompt(p_b1)
    assert ent_b1["channel"] == "#all-agentflow-ai"

    p_b2 = "Post update in all-agentflow-ai channel"
    ent_b2 = parameter_autofill_engine.extract_entities_from_prompt(p_b2)
    assert ent_b2["channel"] == "#all-agentflow-ai"

    # Case C: #general explicitly
    p_c = "Send message to #general"
    ent_c = parameter_autofill_engine.extract_entities_from_prompt(p_c)
    assert ent_c["channel"] == "#general"

    # Case D: Non-#general channel (#dev-alerts)
    p_d = "Post alert to #dev-alerts"
    ent_d = parameter_autofill_engine.extract_entities_from_prompt(p_d)
    assert ent_d["channel"] == "#dev-alerts"


def test_slack_channel_override_default_schema_value():
    # Case E: Existing params has "#general" from schema/default, prompt specifies "#all-agentflow-ai"
    existing = {"channel": "#general", "text": "Hello"}
    prompt = "Send status update to #all-agentflow-ai"

    params, scores, missing = parameter_autofill_engine.autofill_node(
        provider="Slack",
        operation_id="slack.chat.postMessage",
        existing_params=existing,
        prompt=prompt,
    )

    assert params["channel"] == "#all-agentflow-ai"
    assert scores["channel"] == 0.95


def test_slack_channel_workflow_graph_pipeline_survival():
    # Case F: Full workflow graph parameter autofill pipeline preserves explicit channel
    graph = {
        "nodes": [
            {
                "id": "slack_1",
                "provider": "Slack",
                "operation_id": "slack.chat.postMessage",
                "parameters": {"channel": "#general", "text": "Test"}
            }
        ]
    }
    prompt = "Notify #all-agentflow-ai about project status"

    result_graph = parameter_autofill_engine.autofill_workflow_nodes(graph, prompt=prompt)
    assert result_graph["nodes"][0]["parameters"]["channel"] == "#all-agentflow-ai"


@pytest.mark.asyncio
async def test_parameter_autofill_api_extract_endpoint(async_client):
    token = create_access_token("usr_1")
    headers = {"Authorization": f"Bearer {token}"}

    extract_payload = {
        "provider": "Gmail",
        "operation_id": "gmail.messages.send",
        "prompt": "Send good morning email to boss@company.com",
        "existing_parameters": {"subject": "Good Morning", "body": "Hello boss"}
    }

    res = await async_client.post("/api/v1/parameter-autofill/extract", json=extract_payload, headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["parameters"]["to"] == "boss@company.com"
    assert data["confidence_scores"]["to"] == 0.95
    assert data["is_complete"] is True
