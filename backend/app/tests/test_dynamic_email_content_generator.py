import pytest
from app.services.ai_email_writer import ai_email_writer
from app.agents.planner.planner_v4 import intelligent_planner_v4


def test_dynamic_email_content_apology():
    prompt = "Write an apology email to client"
    content = ai_email_writer.generate_email_content(prompt)

    assert isinstance(content, dict)
    assert "subject" in content
    assert "body" in content
    assert len(content["subject"]) > 0
    assert len(content["body"]) > 0
    assert "apolog" in content["subject"].lower() or "apolog" in content["body"].lower() or "sorry" in content["body"].lower()


def test_dynamic_email_content_welcome():
    prompt = "Write a welcome email to Sarah"
    content = ai_email_writer.generate_email_content(prompt)

    assert isinstance(content, dict)
    assert "subject" in content
    assert "body" in content
    assert len(content["subject"]) > 0
    assert len(content["body"]) > 0
    assert "welcome" in content["subject"].lower() or "welcome" in content["body"].lower()


def test_dynamic_email_content_follow_up():
    prompt = "Write follow-up email"
    content = ai_email_writer.generate_email_content(prompt)

    assert isinstance(content, dict)
    assert "subject" in content
    assert "body" in content
    assert len(content["subject"]) > 0
    assert len(content["body"]) > 0
    assert "follow" in content["subject"].lower() or "follow" in content["body"].lower()


def test_dynamic_email_content_json_schema():
    prompts = [
        "Compose a newsletter announcement",
        "Generate a meeting follow-up email",
        "Draft a project status report",
    ]
    for p in prompts:
        res = ai_email_writer.generate_email_content(p)
        assert isinstance(res, dict)
        assert set(res.keys()) == {"subject", "body"}
        assert isinstance(res["subject"], str)
        assert isinstance(res["body"], str)


def test_planner_integration_dynamic_email():
    plan = intelligent_planner_v4.plan("Write an apology email to client@corp.com")
    nodes = [n for n in plan.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]]
    assert len(nodes) > 0
    params = nodes[0]["parameters"]
    assert "subject" in params and len(params["subject"]) > 0
    assert "body" in params and len(params["body"]) > 0
