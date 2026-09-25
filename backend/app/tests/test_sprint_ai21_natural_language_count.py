import pytest
from app.agents.planner.gmail_search_query_builder import (
    extract_gmail_result_count,
    build_gmail_search_query,
)
from app.agents.task_decomposer.decomposer import enterprise_task_decomposer
from app.agents.planner.planner_v4 import intelligent_planner_v4


def test_1_extract_result_count_various_prompts():
    """Sprint AI-21 Test 1: Extract numeric and word result counts accurately."""
    assert extract_gmail_result_count("Find my unread emails and show the first 5.") == 5
    assert extract_gmail_result_count("Find my unread emails and show the first 15.") == 15
    assert extract_gmail_result_count("Find emails from john@example.com and show the first 20.") == 20
    assert extract_gmail_result_count("Find unread emails.") is None
    assert extract_gmail_result_count("Find emails from john@example.com.") is None
    assert extract_gmail_result_count("Show the first 5 unread emails.") == 5
    assert extract_gmail_result_count("Give me the first five unread emails.") == 5
    assert extract_gmail_result_count("Show the first 50 unread emails.") == 50
    assert extract_gmail_result_count("Show the first 100 unread emails.") == 100
    assert extract_gmail_result_count("Find my unread emails and show the first 5. Do not send, reply, forward, delete or modify anything.") == 5


def test_2_query_cleanliness_no_number_leakage():
    """Sprint AI-21 Test 2: Search query q does NOT leak count numbers into search terms."""
    q1 = build_gmail_search_query("Find my unread emails and show the first 5.")
    assert "5" not in q1
    assert q1 == "is:unread"

    q2 = build_gmail_search_query("Find emails from john@example.com and show the first 20.")
    assert "20" not in q2
    assert q2 == "from:john@example.com"

    q3 = build_gmail_search_query("Show the first 5 unread emails.")
    assert "5" not in q3
    assert q3 == "is:unread"

    q4 = build_gmail_search_query("Give me the first five unread emails.")
    assert "five" not in q4
    assert q4 == "is:unread"


def test_3_task_decomposer_applies_extracted_count_and_capping(caplog):
    """Sprint AI-21 Test 3: TaskDecomposer sets max_results from prompt and caps at 50."""
    with caplog.at_level("INFO"):
        res5 = enterprise_task_decomposer.decompose("Find my unread emails and show the first 5.")
        assert res5.tasks[0].parameters["max_results"] == 5
        assert "[AI-21][RESULT_COUNT_PROMPT]" in caplog.text
        assert "[AI-21][RESULT_COUNT_APPLIED]" in caplog.text

    caplog.clear()
    with caplog.at_level("INFO"):
        res100 = enterprise_task_decomposer.decompose("Show the first 100 unread emails.")
        assert res100.tasks[0].parameters["max_results"] == 50
        assert "[AI-21][RESULT_COUNT_CAPPED]" in caplog.text


def test_4_planner_v4_propagates_extracted_count():
    """Sprint AI-21 Test 4: PlannerV4 builds DAG nodes with explicit max_results."""
    plan_5 = intelligent_planner_v4.plan("Find my unread emails and show the first 5.")
    node_5 = next(n for n in plan_5.workflow_graph["nodes"] if n["operation_id"] in ["gmail.messages.list", "gmail.messages.search"])
    assert node_5["parameters"]["max_results"] == 5

    plan_15 = intelligent_planner_v4.plan("Find my unread emails and show the first 15.")
    node_15 = next(n for n in plan_15.workflow_graph["nodes"] if n["operation_id"] in ["gmail.messages.list", "gmail.messages.search"])
    assert node_15["parameters"]["max_results"] == 15

    plan_default = intelligent_planner_v4.plan("Find my unread emails.")
    node_default = next(n for n in plan_default.workflow_graph["nodes"] if n["operation_id"] in ["gmail.messages.list", "gmail.messages.search"])
    assert node_default["parameters"]["max_results"] == 10


def test_5_read_only_constraint_with_count():
    """Sprint AI-21 Test 5: Negative read-only constraints preserve max_results and omit side effect operations."""
    prompt = "Find my unread emails and show the first 5. Do not send, reply, forward, delete or modify anything."
    res = enterprise_task_decomposer.decompose(prompt)
    assert len(res.tasks) == 2
    assert res.tasks[0].operation in ["gmail.messages.list", "gmail.messages.search"]
    assert res.tasks[0].parameters["max_results"] == 5
    assert res.tasks[1].operation == "gmail.messages.get"

    # Confirm no write operations (send, reply, delete) were generated
    ops = [t.operation for t in res.tasks]
    assert "gmail.messages.send" not in ops
    assert "gmail.messages.delete" not in ops
