import pytest
from unittest.mock import patch
from app.services.ai_email_writer import ai_email_writer, AIEmailWriter
from app.agents.planner.planner_v4 import intelligent_planner_v4


def test_ai_email_writer_json_cleaning():
    writer = AIEmailWriter()

    raw_markdown = """```json
{
  "subject": "Apology Regarding Recent Delay",
  "body": "Dear Customer,\\n\\nPlease accept our apologies.\\n\\nBest regards,\\nAgentFlow"
}
```"""

    cleaned = writer.clean_and_parse_json(raw_markdown)
    assert cleaned["subject"] == "Apology Regarding Recent Delay"
    assert "Please accept our apologies." in cleaned["body"]
    assert "\r" not in cleaned["subject"] and "\n" not in cleaned["subject"]


def test_ai_email_writer_llm_mock_generation():
    writer = AIEmailWriter()
    mock_json = '```json\n{"subject": "Happy Birthday Sarah!", "body": "Happy Birthday Sarah! Have a great day."}\n```'

    cleaned = writer.clean_and_parse_json(mock_json)
    assert cleaned["subject"] == "Happy Birthday Sarah!"
    assert "Have a great day." in cleaned["body"]


def test_ai_email_writer_apology_prompt():
    prompt = "Write a professional apology email"
    plan = intelligent_planner_v4.plan(prompt)

    nodes = [n for n in plan.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]]
    assert len(nodes) > 0
    params = nodes[0]["parameters"]

    assert "Apology" in params["subject"] or "Delay" in params["subject"]
    assert "apologies" in params["body"].lower() or "sorry" in params["body"].lower()


def test_ai_email_writer_birthday_prompt():
    prompt = "Write a birthday email"
    plan = intelligent_planner_v4.plan(prompt)

    nodes = [n for n in plan.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]]
    assert len(nodes) > 0
    params = nodes[0]["parameters"]

    assert "Birthday" in params["subject"]
    assert "Birthday" in params["body"]
