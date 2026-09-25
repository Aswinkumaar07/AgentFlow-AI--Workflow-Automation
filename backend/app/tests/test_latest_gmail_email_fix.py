import pytest
from app.api.v1.ai import generate_workflow
from app.schemas.ai import AIGenerateRequest


@pytest.mark.asyncio
async def test_get_my_latest_gmail_email_and_summarize_its_content():
    """Requirement 6: Test exact real browser prompt 'Get my latest Gmail email and summarize its content'."""
    prompt = "Get my latest Gmail email and summarize its content"
    req = AIGenerateRequest(prompt=prompt)
    res = await generate_workflow(req, current_user=None)
    wf = res.get("data", {}).get("workflow_json") or res.get("workflow_json") or {}

    nodes = wf.get("nodes", [])
    ops = [n.get("operation") or n.get("data", {}).get("operation_id") for n in nodes]

    assert "gmail.messages.list" in ops, "gmail.messages.list must exist"
    assert "gmail.messages.get" in ops, "gmail.messages.get must exist"
    assert "ai.summarize" in ops, "ai.summarize must exist"
    assert "loop.forEach" not in ops, "no loop.forEach should be introduced"

    list_node = next(n for n in nodes if (n.get("operation") or n.get("data", {}).get("operation_id")) == "gmail.messages.list")
    params = list_node.get("parameters") or list_node.get("data", {}).get("parameters") or {}
    assert params.get("q") == "", f"q must be empty string, got '{params.get('q')}'"
    assert params.get("max_results") == 1, f"max_results must be 1, got {params.get('max_results')}"

    get_node = next(n for n in nodes if (n.get("operation") or n.get("data", {}).get("operation_id")) == "gmail.messages.get")
    get_params = get_node.get("parameters") or get_node.get("data", {}).get("parameters") or {}
    assert get_params.get("message_id") == "{{step_1.messages[0].id}}", f"message_id must be '{{step_1.messages[0].id}}', got '{get_params.get('message_id')}'"


@pytest.mark.asyncio
async def test_latest_gmail_email_variations():
    """Requirement 6: Verify variations of latest Gmail email prompts."""
    variations = [
        "Get my latest Gmail email",
        "Find my latest email",
        "Get my newest Gmail email",
        "Get my most recent Gmail email",
    ]
    for prompt in variations:
        req = AIGenerateRequest(prompt=prompt)
        res = await generate_workflow(req, current_user=None)
        wf = res.get("data", {}).get("workflow_json") or res.get("workflow_json") or {}
        nodes = wf.get("nodes", [])
        ops = [n.get("operation") or n.get("data", {}).get("operation_id") for n in nodes]

        assert "gmail.messages.list" in ops, f"gmail.messages.list missing for '{prompt}'"
        assert "gmail.messages.get" in ops, f"gmail.messages.get missing for '{prompt}'"

        list_node = next(n for n in nodes if (n.get("operation") or n.get("data", {}).get("operation_id")) == "gmail.messages.list")
        params = list_node.get("parameters") or list_node.get("data", {}).get("parameters") or {}
        assert params.get("q") == "", f"q must be empty string for '{prompt}', got '{params.get('q')}'"
        assert params.get("max_results") == 1, f"max_results must be 1 for '{prompt}', got {params.get('max_results')}"


@pytest.mark.asyncio
async def test_multiple_emails_and_loop_preservation():
    """Requirement 6 & 5: Ensure 'Get my latest 5 emails and summarize each' preserves count=5 and loop."""
    prompt = "Get my latest 5 emails and summarize each"
    req = AIGenerateRequest(prompt=prompt)
    res = await generate_workflow(req, current_user=None)
    wf = res.get("data", {}).get("workflow_json") or res.get("workflow_json") or {}

    nodes = wf.get("nodes", [])
    ops = [n.get("operation") or n.get("data", {}).get("operation_id") for n in nodes]

    assert "gmail.messages.list" in ops
    assert "loop.forEach" in ops

    list_node = next(n for n in nodes if (n.get("operation") or n.get("data", {}).get("operation_id")) == "gmail.messages.list")
    params = list_node.get("parameters") or list_node.get("data", {}).get("parameters") or {}
    assert params.get("max_results") == 5, f"max_results must be 5, got {params.get('max_results')}"
