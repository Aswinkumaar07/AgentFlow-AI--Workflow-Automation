import pytest
from app.agents.connector_studio import connector_studio_ai_service, GeneratedConnectorSpec
from app.agents.connector_ai import connector_selector
from app.agents.planner.planner_v3 import intelligent_planner_v3


def test_connector_studio_openapi_generation():
    twilio_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Twilio Messaging API", "version": "v1"},
        "paths": {
            "/v1/Messages": {
                "post": {
                    "summary": "Send SMS message",
                    "operationId": "twilio.messages.create",
                    "parameters": [
                        {"name": "To", "required": True},
                        {"name": "Body", "required": True},
                    ],
                }
            }
        },
    }

    res = connector_studio_ai_service.generate_connector(twilio_spec)
    assert isinstance(res, GeneratedConnectorSpec)
    assert res.provider == "Twilio Messaging API"
    assert res.icon == "MessageSquare"
    assert res.is_registered is True
    assert len(res.operations) == 1
    assert "def test_generated_" in res.generated_test_code

    # Verify live registration in ConnectorSelector
    candidates = connector_selector.select_connectors("Twilio Messaging API")
    providers = [c.provider for c in candidates]
    assert "Twilio Messaging API" in providers

    # Verify Planner V3 immediately uses it
    plan_res = intelligent_planner_v3.plan("Send SMS alert via Twilio Messaging API")
    assert "Twilio Messaging API" in plan_res.selected_connectors
