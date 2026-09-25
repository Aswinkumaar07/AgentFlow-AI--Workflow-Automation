import pytest
from app.agents.planner.slack_parameter_extractor import extract_slack_text, extract_slack_parameters
from app.agents.task_decomposer.decomposer import EnterpriseTaskDecomposer
from app.agents.parameter_ai.parameter_generator import parameter_generator
from app.agents.planner.deterministic_normalizer import deterministic_normalizer


def test_slack_text_extractor_case_a():
    prompt = 'Send a Slack message to #all-agentflow-ai saying "Hello world."'
    assert extract_slack_text(prompt) == "Hello world."


def test_slack_text_extractor_case_b():
    prompt = "Send a Slack message to #all-agentflow-ai saying 'Hello world.'"
    assert extract_slack_text(prompt) == "Hello world."


def test_slack_text_extractor_case_c():
    prompt = 'Send a Slack message to #all-agentflow-ai with message "Deployment complete."'
    assert extract_slack_text(prompt) == "Deployment complete."


def test_slack_text_extractor_case_d():
    prompt = 'Send "Hello world" to #all-agentflow-ai'
    assert extract_slack_text(prompt) == "Hello world"


def test_slack_text_extractor_case_e_dynamic():
    prompt = 'Send the Slack message "{{step_2.summary}}" to #all-agentflow-ai'
    assert extract_slack_text(prompt) == "{{step_2.summary}}"


def test_slack_text_extractor_exact_user_prompt():
    prompt = 'Send a Slack message to #all-agentflow-ai saying "AgentFlow AI integration test successful."'
    assert extract_slack_text(prompt) == "AgentFlow AI integration test successful."


def test_slack_text_decomposer_integration():
    decomposer = EnterpriseTaskDecomposer()
    prompt = 'Send a Slack message to #all-agentflow-ai saying "AgentFlow AI integration test successful."'
    res = decomposer.decompose(prompt)
    tasks = res.tasks
    assert len(tasks) == 1
    assert tasks[0].provider == "slack"
    assert tasks[0].parameters["channel"] == "#all-agentflow-ai"
    assert tasks[0].parameters["text"] == "AgentFlow AI integration test successful."


def test_slack_text_parameter_generator_integration():
    prompt = 'Send a Slack message to #all-agentflow-ai saying "AgentFlow AI integration test successful."'
    res = parameter_generator.generate_parameters_for_operation(
        prompt=prompt,
        operation_id="slack.chat.postMessage",
        provider="slack",
    )
    assert res.parameters["text"] == "AgentFlow AI integration test successful."


def test_slack_text_deterministic_normalizer_integration():
    prompt = 'Send a Slack message to #all-agentflow-ai saying "AgentFlow AI integration test successful."'
    raw_graph = {
        "nodes": [
            {
                "id": "step_1",
                "provider": "slack",
                "operation": "slack.chat.postMessage",
                "parameters": {"channel": "#all-agentflow-ai", "text": prompt}
            }
        ]
    }
    norm_graph = deterministic_normalizer.normalize_workflow_graph(prompt, raw_graph)
    assert norm_graph["nodes"][0]["parameters"]["text"] == "AgentFlow AI integration test successful."


def test_slack_structured_parameter_behavior_unchanged():
    # If parameters already contain a pre-structured custom text, normalizer/autofill should preserve it.
    raw_graph = {
        "nodes": [
            {
                "id": "step_1",
                "provider": "slack",
                "operation": "slack.chat.postMessage",
                "parameters": {"channel": "#general", "text": "{{step_2.summary}}"}
            }
        ]
    }
    norm_graph = deterministic_normalizer.normalize_workflow_graph("Post summary to Slack", raw_graph)
    assert norm_graph["nodes"][0]["parameters"]["text"] == "{{step_2.summary}}"
