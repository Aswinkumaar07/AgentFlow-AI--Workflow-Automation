import pytest
from app.agents.planner.planner_v4 import intelligent_planner_v4


def test_ai_email_generator_good_night():
    prompt = "Send good night email"
    plan = intelligent_planner_v4.plan(prompt)

    gmail_node = next(n for n in plan.workflow_graph["nodes"] if n["provider"] == "gmail")
    assert "Good Night" in gmail_node["parameters"]["subject"]
    assert "Good Night" in gmail_node["parameters"]["body"]
    assert "Sleep well." in gmail_node["parameters"]["body"]


def test_ai_email_generator_happy_birthday_sarah():
    prompt = "Wish Sarah happy birthday"
    plan = intelligent_planner_v4.plan(prompt)

    gmail_node = next(n for n in plan.workflow_graph["nodes"] if n["provider"] == "gmail")
    assert "Happy Birthday" in gmail_node["parameters"]["subject"]
    assert "Happy Birthday" in gmail_node["parameters"]["body"]
    assert "Have an amazing day." in gmail_node["parameters"]["body"]


def test_ai_email_generator_apology():
    prompt = "Send apology email"
    plan = intelligent_planner_v4.plan(prompt)

    gmail_node = next(n for n in plan.workflow_graph["nodes"] if n["provider"] == "gmail")
    assert "Apology" in gmail_node["parameters"]["subject"]
    assert "Dear" in gmail_node["parameters"]["body"]
    assert "apologies" in gmail_node["parameters"]["body"]
    assert "Best regards" in gmail_node["parameters"]["body"]
