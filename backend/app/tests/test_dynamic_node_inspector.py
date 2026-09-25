import pytest
from app.connectors.registry import connector_registry
from app.connectors.models import ParameterSchemaModel


def test_parameter_schema_supports_all_15_types():
    supported_types = [
        "text", "textarea", "number", "boolean", "date", "select", "multi_select",
        "file", "json", "expression", "password", "email", "url", "array", "object"
    ]
    
    for t in supported_types:
        param = ParameterSchemaModel(name=f"test_{t}", display_name=f"Test {t}", type=t)
        assert param.type == t
        assert param.display_name == f"Test {t}"


def test_gmail_send_email_has_email_textarea_file_types():
    schema = connector_registry.get_operation_schema("gmail", "gmail.messages.send")
    assert schema is not None
    
    to_param = next(p for p in schema.required_parameters if p.name == "to")
    assert to_param.type == "email"
    
    subject_param = next(p for p in schema.required_parameters if p.name == "subject")
    assert subject_param.type == "text"
    
    body_param = next(p for p in schema.required_parameters if p.name == "body")
    assert body_param.type == "textarea"
    
    attachment_param = next(p for p in schema.optional_parameters if p.name == "attachments")
    assert attachment_param.type == "file"


def test_slack_and_openai_schema_parameter_types():
    slack_schema = connector_registry.get_operation_schema("slack", "slack.chat.postMessage")
    assert slack_schema is not None
    channel_param = next(p for p in slack_schema.required_parameters if p.name == "channel")
    assert channel_param.required is True

    openai_schema = connector_registry.get_operation_schema("openai", "openai.chat.completions")
    assert openai_schema is not None
    model_param = next(p for p in openai_schema.optional_parameters if p.name == "model")
    assert model_param.type == "select"
    assert len(model_param.options) > 0
