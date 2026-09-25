import pytest
from app.connectors.registry import connector_registry
from app.agents.parameter_autofill.parameter_autofill_engine import ParameterAutofillEngine


def test_gmail_dynamic_schema_fields():
    schema = connector_registry.get_operation_schema("Gmail", "gmail.messages.send")
    assert schema is not None

    req_names = [p.name for p in schema.required_parameters]
    opt_names = [p.name for p in schema.optional_parameters]

    # Required fields validation
    assert "to" in req_names
    assert "subject" in req_names
    assert "body" in req_names

    # Optional fields validation
    assert "cc" in opt_names
    assert "bcc" in opt_names
    assert "reply_to" in opt_names
    assert "html" in opt_names
    assert "attachments" in opt_names


def test_gmail_autofill_good_night_prompt():
    engine = ParameterAutofillEngine()
    prompt = "Send Good Night email to john@example.com"
    params, scores, missing = engine.autofill_node(
        "Gmail", "gmail.messages.send",
        existing_params={"subject": "Good Night", "body": "Good Night"},
        prompt=prompt
    )

    assert params.get("to") == "john@example.com"
    assert params.get("body") == "Good Night"
    assert params.get("subject") == "Good Night"


def test_gmail_autofill_happy_birthday_prompt():
    engine = ParameterAutofillEngine()
    prompt = "Send Happy Birthday email to alice@example.com"
    params, scores, missing = engine.autofill_node(
        "Gmail", "gmail.messages.send",
        existing_params={"subject": "Happy Birthday", "body": "Happy Birthday"},
        prompt=prompt
    )

    assert params.get("to") == "alice@example.com"
    assert params.get("body") == "Happy Birthday"
    assert params.get("subject") == "Happy Birthday"


def test_gmail_no_forced_good_morning_defaults():
    engine = ParameterAutofillEngine()
    prompt = "Send custom update email to user@example.com"
    params, scores, missing = engine.autofill_node("Gmail", "gmail.messages.send", prompt=prompt)

    assert params.get("to") == "user@example.com"
    assert params.get("body") != "Good Morning ☀️"
    assert "Good morning" not in str(params.get("body"))
