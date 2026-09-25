import pytest
from app.agents.task_decomposer.decomposer import enterprise_task_decomposer


def test_approval_generation_target_prompt():
    """
    A. Test target prompt:
    'Search my Gmail for my 3 most recent emails from LinkedIn, get the details of those emails, and wait for my human approval before completing the workflow.'
    Must produce:
    1. Gmail search
    2. Gmail get
    3. Human Approval (provider='human_approval', operation='approval.wait')
    """
    prompt = (
        "Search my Gmail for my 3 most recent emails from LinkedIn, "
        "get the details of those emails, and wait for my human approval before completing the workflow."
    )
    res = enterprise_task_decomposer.decompose(prompt)
    assert res is not None
    assert len(res.tasks) == 3

    assert res.tasks[0].provider == "gmail"
    assert res.tasks[0].operation in ("gmail.messages.search", "gmail.messages.list")

    assert res.tasks[1].provider == "gmail"
    assert res.tasks[1].operation == "gmail.messages.get"

    assert res.tasks[2].provider == "human_approval"
    assert res.tasks[2].operation == "approval.wait"
    assert res.tasks[2].name == "Human Approval"


def test_no_approval_when_not_requested():
    """
    B. Test Gmail search + get WITHOUT approval phrase.
    Must NOT generate a Human Approval task.
    """
    prompt = "Search my Gmail for my 3 most recent emails from LinkedIn and get the details of those emails."
    res = enterprise_task_decomposer.decompose(prompt)
    assert res is not None
    assert len(res.tasks) == 2
    assert not any(t.provider == "human_approval" for t in res.tasks)


def test_existing_slack_approval_pattern_single_approval_node():
    """
    C. Test existing Gmail + summarize + Slack pattern requesting approval.
    Must produce exactly ONE Human Approval task.
    """
    prompt = (
        "Search Gmail for my unread emails, summarize them, wait for my human approval, "
        "and send summary to Slack #general."
    )
    res = enterprise_task_decomposer.decompose(prompt)
    assert res is not None
    approval_tasks = [t for t in res.tasks if t.provider == "human_approval" or t.operation == "approval.wait"]
    assert len(approval_tasks) == 1
    assert approval_tasks[0].step == 4


def test_no_duplicate_approval_tasks():
    """
    D. Test that approval language does not produce duplicate approval tasks.
    """
    prompt = (
        "Search my Gmail for my 3 most recent emails from LinkedIn, get details, "
        "wait for my approval, confirm before completing, verify before finishing."
    )
    res = enterprise_task_decomposer.decompose(prompt)
    assert res is not None
    approval_tasks = [t for t in res.tasks if t.provider == "human_approval" or t.operation == "approval.wait"]
    assert len(approval_tasks) == 1
