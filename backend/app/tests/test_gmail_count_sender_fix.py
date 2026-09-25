import pytest
from app.agents.planner.gmail_search_query_builder import extract_gmail_result_count, build_gmail_search_query
from app.agents.task_decomposer.decomposer import EnterpriseTaskDecomposer
from app.api.v1.ai import generate_workflow
from app.schemas.ai import AIGenerateRequest
from app.models.users import User


def test_extract_gmail_result_count_variations():
    """Verify result count extraction for 5 most recent, 5 latest, etc."""
    assert extract_gmail_result_count("Find my 5 most recent Gmail emails from LinkedIn") == 5
    assert extract_gmail_result_count("5 most recent emails") == 5
    assert extract_gmail_result_count("5 most recent Gmail emails") == 5
    assert extract_gmail_result_count("5 latest emails") == 5
    assert extract_gmail_result_count("5 latest Gmail messages") == 5
    assert extract_gmail_result_count("Find my latest 5 Gmail emails") == 5
    assert extract_gmail_result_count("Get my latest Gmail email") is None


def test_sender_filter_and_fallback_cleanup():
    """Verify sender filter extraction and fallback noise cleanup."""
    q1 = build_gmail_search_query("Find emails from LinkedIn")
    assert q1 == "from:linkedin"

    q2 = build_gmail_search_query("Find my 5 most recent Gmail emails from LinkedIn")
    assert q2 == "from:linkedin"

    # Regression test for malformed fallback cleanup output ("5 s")
    assert "5 s" not in q2
    assert "Find my" not in q2
    assert "most recent" not in q2
    assert "Gmail" not in q2


@pytest.mark.asyncio
async def test_exact_failing_prompt_generation():
    """Requirement 1: Exact failing prompt 'Find my 5 most recent Gmail emails from LinkedIn'."""
    prompt = "Find my 5 most recent Gmail emails from LinkedIn"
    req = AIGenerateRequest(prompt=prompt)
    mock_user = User(id="usr_1", email="user@example.com")
    res = await generate_workflow(req=req, current_user=mock_user)

    wf = res.get("data", {}).get("workflow_json") or {}
    nodes = wf.get("nodes", [])
    assert len(nodes) >= 1

    list_node = next(n for n in nodes if (n.get("operation") or n.get("data", {}).get("operation_id")) in ["gmail.messages.list", "gmail.messages.search"])
    params = list_node.get("parameters") or list_node.get("data", {}).get("parameters") or {}

    assert params.get("q") == "from:linkedin", f"Expected q='from:linkedin', got '{params.get('q')}'"
    assert params.get("max_results") == 5, f"Expected max_results=5, got {params.get('max_results')}"

    # Confirm garbage phrases are absent
    q_val = params.get("q", "")
    for garbage in ["Find my", "5", "most recent", "Gmail", "s"]:
        if garbage == "s":
            assert " 5 s " not in f" {q_val} ", "stray '5 s' phrase found in q"
        else:
            assert garbage.lower() not in q_val.lower(), f"Garbage phrase '{garbage}' found in q"


@pytest.mark.asyncio
async def test_find_my_latest_gmail_email_preserved():
    """Requirement 2: 'Find my latest Gmail email' preserves single-email behavior."""
    prompt = "Find my latest Gmail email"
    req = AIGenerateRequest(prompt=prompt)
    res = await generate_workflow(req=req, current_user=None)
    wf = res.get("data", {}).get("workflow_json") or {}
    nodes = wf.get("nodes", [])

    list_node = next(n for n in nodes if (n.get("operation") or n.get("data", {}).get("operation_id")) == "gmail.messages.list")
    params = list_node.get("parameters") or list_node.get("data", {}).get("parameters") or {}

    assert params.get("q") == ""
    assert params.get("max_results") == 1


@pytest.mark.asyncio
async def test_find_my_latest_5_gmail_emails():
    """Requirement 3 & 4: Multi-email prompts preserve count=5."""
    for prompt in ["Find my latest 5 Gmail emails", "Find my 5 most recent Gmail emails"]:
        req = AIGenerateRequest(prompt=prompt)
        res = await generate_workflow(req=req, current_user=None)
        wf = res.get("data", {}).get("workflow_json") or {}
        nodes = wf.get("nodes", [])

        list_node = next(n for n in nodes if (n.get("operation") or n.get("data", {}).get("operation_id")) in ["gmail.messages.list", "gmail.messages.search"])
        params = list_node.get("parameters") or list_node.get("data", {}).get("parameters") or {}
        assert params.get("max_results") == 5, f"Expected max_results=5 for '{prompt}', got {params.get('max_results')}"
