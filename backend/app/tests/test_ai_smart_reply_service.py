import pytest
from app.services.ai_smart_reply import ai_smart_reply_service, AISmartReplyService
from app.agents.planner.planner_v4 import intelligent_planner_v4


def test_smart_reply_thread_id_preservation():
    service = AISmartReplyService()
    original_email = {
        "id": "msg_9988776655443322",
        "thread_id": "thread_abc123",
        "sender": "client@corp.com",
        "subject": "Q3 Budget Review",
        "body": "Hi team, please find attached the Q3 budget summary.",
    }

    reply = service.generate_smart_reply(original_email, user_instruction="Acknowledge receipt and approve budget")
    assert reply["thread_id"] == "thread_abc123"
    assert reply["message_id"] == "msg_9988776655443322"
    assert reply["to"] == "client@corp.com"
    assert reply["subject"] == "Re: Q3 Budget Review"
    assert "Q3 Budget Review" in reply["body"] or "Thank you" in reply["body"] or "received" in reply["body"]


def test_smart_reply_subject_re_prefix():
    service = AISmartReplyService()
    email_already_re = {
        "id": "msg_001",
        "thread_id": "thread_001",
        "sender": "vendor@supply.io",
        "subject": "Re: Shipping Status",
        "body": "Package has shipped.",
    }

    reply = service.generate_smart_reply(email_already_re)
    assert reply["subject"] == "Re: Shipping Status"
    assert reply["thread_id"] == "thread_001"


def test_planner_smart_reply_workflow():
    prompt = "Reply to message msg_1234567890abcdef Body: Sounds good, thanks!"
    plan = intelligent_planner_v4.plan(prompt)

    nodes = [n for n in plan.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]]
    assert len(nodes) > 0
    node = nodes[0]

    op_id = node.get("operation") or node.get("operation_id")
    assert op_id == "gmail.messages.reply"
    params = node["parameters"]
    assert params["thread_id"] == "msg_1234567890abcdef"
    assert params["subject"].startswith("Re:")
