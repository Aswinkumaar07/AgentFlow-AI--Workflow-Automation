import pytest
from app.agents.parameter_ai import parameter_generator, parameter_ai_service


def test_parameter_generator_good_morning_email():
    res = parameter_generator.generate_parameters_for_operation(
        "Send good morning email", "gmail.messages.send", "Gmail"
    )
    assert res.parameters.get("subject") == "Good Morning ☀️"
    assert "Good Morning" in res.parameters.get("body", "")
    assert res.parameters.get("to") is None
    assert "recipient_email" in res.missing_inputs


def test_parameter_generator_explicit_email():
    res = parameter_generator.generate_parameters_for_operation(
        "Send email to john@example.com", "gmail.messages.send", "Gmail"
    )
    assert res.parameters.get("to") == "john@example.com"
    assert "recipient_email" not in res.missing_inputs


def test_parameter_generator_slack_and_folder():
    entities = parameter_generator.extract_entities(
        "Notify Slack in #engineering and save invoice to folder: Invoices"
    )
    assert entities.get("slack_channel") == "#engineering"
    assert entities.get("folder") == "Invoices"


def test_parameter_generator_github_repo_and_branch():
    entities = parameter_generator.extract_entities(
        "List pull requests for repo: AgentFlow-AI/TERRAWATCH on branch: main"
    )
    assert entities.get("github_repo") == "AgentFlow-AI/TERRAWATCH"
    assert entities.get("github_branch") == "main"


def test_parameter_ai_service_populate_nodes():
    nodes = [
        {"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.send"}
    ]
    populated, missing = parameter_ai_service.populate_node_parameters("Send good morning email", nodes)
    assert len(populated) == 1
    assert populated[0]["parameters"]["subject"] == "Good Morning ☀️"
    assert "recipient_email" in missing
