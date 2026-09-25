import pytest
from app.agents.task_decomposer import enterprise_task_decomposer, TaskDecompositionResult
from app.agents.planner.planner_v4 import intelligent_planner_v4


def test_task_decomposition_scheduled_email():
    # Prompt 1: "Tomorrow send John an email" -> 3 tasks
    res = enterprise_task_decomposer.decompose("Tomorrow send John an email")
    assert isinstance(res, TaskDecompositionResult)
    assert len(res.tasks) == 3

    t1, t2, t3 = res.tasks[0], res.tasks[1], res.tasks[2]
    assert t1.step == 1
    assert t1.provider == "schedule"
    assert t2.step == 2
    assert t2.provider == "ai"
    assert t3.step == 3
    assert t3.provider == "gmail"
    assert 1 in t3.depends_on and 2 in t3.depends_on


def test_task_decomposition_read_summarize():
    # Prompt 2: "Read unread emails and summarize" -> 4 tasks (AI-8: adds Send Email Summary)
    res = enterprise_task_decomposer.decompose("Read unread emails and summarize")
    assert isinstance(res, TaskDecompositionResult)
    assert len(res.tasks) >= 3  # List, Read, Summarize (optionally + Send)

    t1, t2, t3 = res.tasks[0], res.tasks[1], res.tasks[2]
    assert t1.step == 1
    assert t1.operation == "gmail.messages.list"
    assert t2.step == 2
    assert t2.operation == "gmail.messages.get"
    assert t3.step == 3
    assert t3.operation == "ai.summarize"


def test_task_decomposition_four_node_workflow():
    # Prompt 3: "Search invoices, download attachment, upload to Drive, and notify Slack" -> 4 tasks
    res = enterprise_task_decomposer.decompose("Search invoices, download attachment, upload to Drive, and notify Slack")
    assert isinstance(res, TaskDecompositionResult)
    assert len(res.tasks) == 4

    providers = [t.provider for t in res.tasks]
    assert providers == ["gmail", "gmail", "drive", "slack"]


def test_task_decomposition_single_action():
    # Single action prompt -> 1 task
    res = enterprise_task_decomposer.decompose("Send email to sarah@example.com")
    assert len(res.tasks) == 1
    assert res.tasks[0].provider == "gmail"


def test_planner_v4_task_decomposition_integration():
    plan = intelligent_planner_v4.plan("Read unread emails and summarize")
    assert any("Stage 0.5 [Task Decomposition]" in trace for trace in plan.reasoning_trace)
