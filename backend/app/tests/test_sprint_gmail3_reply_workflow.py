import pytest
from app.agents.planner.planner_v4 import intelligent_planner_v4
from app.connectors.providers.gmail.adapter import GmailAdapter
from app.connectors.models import ConnectorRequestModel, ConnectorCredentialModel


def test_gmail3_planner_reply_to_latest_email_workflow():
    prompt = "Reply to latest email"
    plan = intelligent_planner_v4.plan(prompt)
    nodes = plan.workflow_graph["nodes"]
    edges = plan.workflow_graph["edges"]

    assert len(nodes) == 4
    assert len(edges) == 3

    # Step 1: list latest email
    assert nodes[0]["operation"] == "gmail.messages.list"
    assert nodes[0]["parameters"]["max_results"] == 1

    # Step 2: get email body and thread details
    assert nodes[1]["operation"] == "gmail.messages.get"
    assert nodes[1]["parameters"]["message_id"] == "{{step_1.messages[0].id}}"

    # Step 3: Gemini Smart Reply generation
    assert nodes[2]["operation"] == "ai.smart_reply"

    # Step 4: Gmail Thread Reply
    assert nodes[3]["operation"] == "gmail.messages.reply"
    assert nodes[3]["parameters"]["thread_id"] == "{{step_2.threadId}}"
    assert nodes[3]["parameters"]["message_id"] == "{{step_2.messageId}}"


def test_gmail3_thread_id_preservation():
    prompt = "Reply politely to latest email"
    plan = intelligent_planner_v4.plan(prompt)
    nodes = plan.workflow_graph["nodes"]

    reply_node = next(n for n in nodes if n["operation"] == "gmail.messages.reply")
    assert "thread_id" in reply_node["parameters"]
    assert reply_node["parameters"]["thread_id"] == "{{step_2.threadId}}"


@pytest.mark.asyncio
async def test_gmail3_adapter_reply_operation_preserves_thread_id():
    adapter = GmailAdapter()
    creds = ConnectorCredentialModel(
        tenant_id="usr_1",
        provider="Google",
        access_token="mock_access_token",
        account_label="aswinkumaar07@gmail.com",
    )

    req_reply = ConnectorRequestModel(
        tenant_id="usr_1",
        operation_id="gmail.messages.reply",
        parameters={
            "message_id": "msg_12345",
            "thread_id": "thread_99999",
            "to": "client@example.com",
            "subject": "Re: Project Inquiry",
            "body": "Thank you for reaching out!",
        },
    )

    res = await adapter.execute_operation(req_reply, credentials=creds)
    assert res is not None
    assert res.operation_id == "gmail.messages.reply"
