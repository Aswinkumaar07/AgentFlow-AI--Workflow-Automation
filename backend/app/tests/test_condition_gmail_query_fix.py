import pytest
from app.agents.planner.gmail_search_query_builder import build_gmail_search_query
from app.agents.task_decomposer.decomposer import EnterpriseTaskDecomposer
from app.agents.planner.planner_v4 import intelligent_planner_v4


def test_conditional_gmail_query_pollution_fix():
    """
    Test exact bug fix:
    Prompt: 'If my latest Gmail email contains the word "urgent", send a Slack message to #all-agentflow-ai saying "Urgent email found"; otherwise do nothing.'
    Must produce:
    - q == ""
    - max_results == 1
    - Condition parameters: left == "{{step_2.snippet}}", operator == "contains", right == "urgent"
    """
    prompt = 'If my latest Gmail email contains the word "urgent", send a Slack message to #all-agentflow-ai saying "Urgent email found"; otherwise do nothing.'

    # 1. Query Builder
    q = build_gmail_search_query(prompt)
    assert q == "", f"Expected q == '', got '{q}'"

    # 2. Decomposer
    decomposer = EnterpriseTaskDecomposer()
    res = decomposer.decompose(prompt)
    step1 = next(t for t in res.tasks if t.step == 1)
    assert step1.parameters.get("q") == "", f"Expected step 1 q == '', got '{step1.parameters.get('q')}'"
    assert step1.parameters.get("max_results") == 1, f"Expected step 1 max_results == 1, got {step1.parameters.get('max_results')}"

    cond_task = next(t for t in res.tasks if t.provider == "condition")
    assert cond_task.parameters.get("left") == "{{step_2.snippet}}"
    assert cond_task.parameters.get("operator") == "contains"
    assert cond_task.parameters.get("right") == "urgent"

    # 3. Planner V4
    plan_res = intelligent_planner_v4.plan(prompt)
    nodes = plan_res.workflow_graph.get("nodes", [])
    n1 = next(n for n in nodes if n.get("id") == "step_1")
    n3 = next(n for n in nodes if n.get("id") == "step_3")

    assert n1["parameters"].get("q") == "", f"Expected n1 q == '', got '{n1['parameters'].get('q')}'"
    assert n1["parameters"].get("max_results") == 1, f"Expected n1 max_results == 1, got {n1['parameters'].get('max_results')}"
    assert n3["parameters"].get("left") == "{{step_2.snippet}}"
    assert n3["parameters"].get("operator") == "contains"
    assert n3["parameters"].get("right") == "urgent"


def test_existing_gmail_search_queries_regression():
    """
    Regression test for existing Gmail search query builder behavior.
    """
    # Latest Gmail email
    assert build_gmail_search_query("Get my latest Gmail email") == ""

    # 5 most recent emails from LinkedIn
    q_linkedin = build_gmail_search_query("Find my 5 most recent Gmail emails from LinkedIn")
    assert q_linkedin == "from:linkedin", f"Expected 'from:linkedin', got '{q_linkedin}'"

    # Sender search
    q_sender = build_gmail_search_query("Find emails from LinkedIn")
    assert q_sender == "from:linkedin", f"Expected 'from:linkedin', got '{q_sender}'"

    # Unread search
    q_unread = build_gmail_search_query("Find unread emails")
    assert q_unread == "is:unread", f"Expected 'is:unread', got '{q_unread}'"

    # Invoice search
    q_invoice = build_gmail_search_query("Find Gmail emails about invoices")
    assert "invoice" in q_invoice, f"Expected 'invoice' in q, got '{q_invoice}'"
