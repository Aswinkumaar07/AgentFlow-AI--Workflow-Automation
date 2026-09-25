import pytest
from app.connectors.registry import connector_registry
from app.connectors.models import ConnectorMetadataModel, OperationSchemaModel, ParameterSchemaModel
from app.core.security import create_access_token


def test_registry_contains_all_16_connectors():
    expected_providers = [
        "gmail", "drive", "sheets", "slack", "github", "notion",
        "discord", "stripe", "openai", "generic_rest", "webhook",
        "schedule", "condition", "loop", "merge", "approval",
    ]
    for p in expected_providers:
        meta = connector_registry.get_connector_metadata(p)
        assert meta is not None, f"Provider '{p}' metadata missing from registry."
        assert meta.provider.strip() != "", f"Provider '{p}' has empty provider string."
        assert len(meta.supported_operations) > 0, f"Provider '{p}' has no supported operations."


def test_connector_metadata_fields():
    meta = connector_registry.get_connector_metadata("gmail")
    assert meta.provider == "Gmail"
    assert meta.display_name == "Google Gmail"
    assert meta.icon == "gmail"
    assert meta.auth_type == "OAuth2"
    assert meta.version == "1.0.0"
    assert meta.documentation_url.startswith("http")
    assert "gmail.messages.send" in meta.supported_operations
    assert "gmail.messages.send" in meta.operation_schemas


def test_gmail_messages_send_parameter_schemas():
    schema = connector_registry.get_operation_schema("gmail", "gmail.messages.send")
    assert schema is not None, "Operation schema for 'gmail.messages.send' missing."
    assert isinstance(schema, OperationSchemaModel)
    assert schema.display_name == "Send Email"

    req_param_names = [p.name for p in schema.required_parameters]
    opt_param_names = [p.name for p in schema.optional_parameters]

    assert "to" in req_param_names
    assert "subject" in req_param_names
    assert "body" in req_param_names
    assert "cc" in opt_param_names
    assert "bcc" in opt_param_names
    assert "attachments" in opt_param_names

    # Check to parameter details
    to_param = next(p for p in schema.required_parameters if p.name == "to")
    assert to_param.required is True
    assert to_param.type in ["string", "email"]


def test_openai_chat_completions_schema():
    schema = connector_registry.get_operation_schema("openai", "openai.chat.completions")
    assert schema is not None
    assert schema.display_name == "Chat Completion / LLM Prompt"
    req_names = [p.name for p in schema.required_parameters]
    opt_names = [p.name for p in schema.optional_parameters]
    assert "prompt" in req_names
    assert "model" in opt_names

    model_param = next(p for p in schema.optional_parameters if p.name == "model")
    assert model_param.type == "select"
    assert len(model_param.options) >= 3


def test_condition_evaluate_schema():
    schema = connector_registry.get_operation_schema("condition", "condition.evaluate")
    assert schema is not None
    req_names = [p.name for p in schema.required_parameters]
    assert "left_value" in req_names
    assert "operator" in req_names
    assert "right_value" in req_names


@pytest.mark.asyncio
async def test_connectors_api_endpoints(async_client):
    token = create_access_token("usr_1")
    auth_headers = {"Authorization": f"Bearer {token}"}

    # GET /api/v1/connectors
    res = await async_client.get("/api/v1/connectors", headers=auth_headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["success"] is True
    data = payload["data"]
    assert len(data) >= 16

    # GET /api/v1/connectors/gmail
    res_gmail = await async_client.get("/api/v1/connectors/gmail", headers=auth_headers)
    assert res_gmail.status_code == 200
    g_data = res_gmail.json()["data"]
    assert g_data["provider"] == "Gmail"

    # GET /api/v1/connectors/gmail/gmail.messages.send
    res_schema = await async_client.get("/api/v1/connectors/gmail/gmail.messages.send", headers=auth_headers)
    assert res_schema.status_code == 200
    s_data = res_schema.json()["data"]
    assert s_data["id"] == "gmail.messages.send"
