import pytest
from app.agents.planner.gmail_search_query_builder import build_gmail_search_query
from app.api.v1.ai import generate_workflow
from app.schemas.ai import AIGenerateRequest
from app.models.users import User


def test_conversational_prompts_return_empty_query():
    """
    Conversational instructions with no search filter must return an empty query q == '',
    never the raw prompt text.
    """
    conversational_prompts = [
        "Summarize my emails and send to Slack",
        "Check my inbox",
        "Fetch my emails",
        "Check my emails and summarize them",
        "Summarize my emails",
        "Fetch my emails and send summary to Slack",
        "Check my inbox and notify me on Slack",
        "Read my last email",
        "List all emails and notify me",
        "Send summary of my emails to Slack #general",
        "Read my inbox and send to slack",
        "Check my email inbox",
    ]
    for prompt in conversational_prompts:
        q = build_gmail_search_query(prompt)
        assert q == "", f"Expected empty query for '{prompt}', got: '{q}'"


def test_valid_gmail_filters_preserved():
    """
    Genuine Gmail filters (from:, subject:, is:unread) must be preserved.
    """
    # 1. from: filter
    assert build_gmail_search_query("Find emails from john@example.com") == "from:john@example.com"
    assert build_gmail_search_query("Summarize emails from aswin@example.com and send to Slack") == "from:aswin@example.com"
    assert build_gmail_search_query("Fetch emails from Stripe") == "from:stripe"

    # 2. is:unread filter
    assert build_gmail_search_query("Summarize my unread emails and send to Slack") == "is:unread"
    assert build_gmail_search_query("Fetch unread emails") == "is:unread"
    assert build_gmail_search_query("Find unread emails from boss@example.com") == "from:boss@example.com is:unread"

    # 3. subject: and topic searches
    assert build_gmail_search_query("Find emails with subject invoice") == "subject:invoice"
    assert build_gmail_search_query("Fetch emails about budget and post to Slack") == "subject:budget"
    assert "invoice" in build_gmail_search_query("Find emails about invoices")


def test_topic_searches_with_quotes_and_keywords():
    """
    Legitimate topic searches using quotes or keywords must be extracted.
    """
    q_quoted = build_gmail_search_query("Find emails about 'Q3 roadmap'")
    assert q_quoted == "subject:Q3 roadmap", f"Expected 'subject:Q3 roadmap', got '{q_quoted}'"

    q_keyword = build_gmail_search_query("Search emails with keyword deployment")
    assert q_keyword == "subject:deployment", f"Expected 'subject:deployment', got '{q_keyword}'"


@pytest.mark.asyncio
async def test_e2e_generate_workflow_conversational_prompt():
    """
    End-to-end: 'Summarize my emails and send to Slack' must produce
    gmail.messages.list node with q == '' (not the conversational prompt).
    """
    prompt = "Summarize my emails and send to Slack"
    req = AIGenerateRequest(prompt=prompt)
    mock_user = User(id="usr_1", email="test@example.com")

    res = await generate_workflow(req=req, current_user=mock_user)
    wf_json = res.get("data", {}).get("workflow_json") or {}
    nodes = wf_json.get("nodes", [])

    assert len(nodes) >= 1
    list_node = next(
        n for n in nodes
        if (n.get("operation") or n.get("data", {}).get("operation_id")) == "gmail.messages.list"
    )
    params = list_node.get("parameters") or list_node.get("data", {}).get("parameters") or {}

    assert params.get("q") == "", f"Expected q == '', got: '{params.get('q')}'"
    assert params.get("q") != prompt, "Raw prompt must never leak into search query q"


@pytest.mark.asyncio
async def test_e2e_generate_workflow_filtered_prompt():
    """
    End-to-end: 'Find emails from Stripe and send to Slack'
    must preserve genuine filters in q.
    """
    prompt = "Find emails from Stripe and send to Slack"
    req = AIGenerateRequest(prompt=prompt)
    mock_user = User(id="usr_1", email="test@example.com")

    res = await generate_workflow(req=req, current_user=mock_user)
    wf_json = res.get("data", {}).get("workflow_json") or {}
    nodes = wf_json.get("nodes", [])

    assert len(nodes) >= 1
    list_node = next(
        n for n in nodes
        if (n.get("operation") or n.get("data", {}).get("operation_id")) == "gmail.messages.list" or
           (n.get("operation") or n.get("data", {}).get("operation_id")) == "gmail.messages.search"
    )
    params = list_node.get("parameters") or list_node.get("data", {}).get("parameters") or {}
    q_val = params.get("q", "")

    assert q_val == "from:stripe", f"Expected 'from:stripe' in q, got '{q_val}'"
