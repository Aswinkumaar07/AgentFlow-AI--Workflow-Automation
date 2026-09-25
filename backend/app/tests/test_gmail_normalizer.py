import base64
import pytest
from app.utils.gmail_normalizer import (
    decode_base64url,
    extract_gmail_message_details,
    strip_html_tags,
)


def encode_base64url(text: str) -> str:
    """Helper to convert string to base64url string used by Gmail API."""
    encoded = base64.b64encode(text.encode("utf-8")).decode("utf-8")
    return encoded.replace("+", "-").replace("/", "_").rstrip("=")


def test_1_simple_text_gmail_message():
    """Test 1: Simple plain-text Gmail message with root payload.body.data."""
    plain_text = "Hello Aswin, here is your project status update."
    b64_data = encode_base64url(plain_text)

    msg = {
        "id": "1a03499609b8e702",
        "threadId": "1a03499609b8e702",
        "labelIds": ["SENT"],
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "From", "value": "john@example.com"},
                {"name": "Subject", "value": "Project Status Report"},
                {"name": "Date", "value": "Mon, 24 Aug 2026 14:00:00 GMT"},
            ],
            "body": {"data": b64_data},
        },
    }

    details = extract_gmail_message_details(msg)
    assert details["messageId"] == "1a03499609b8e702"
    assert details["threadId"] == "1a03499609b8e702"
    assert details["sender"] == "john@example.com"
    assert details["subject"] == "Project Status Report"
    assert details["date"] == "Mon, 24 Aug 2026 14:00:00 GMT"
    assert details["content"] == plain_text
    assert details["labels"] == ["SENT"]


def test_2_multipart_alternative_gmail_message():
    """Test 2: Multipart/alternative message with text/plain and text/html parts."""
    plain_text = "Plain text content for multipart."
    html_text = "<p>HTML text content</p>"

    msg = {
        "id": "msg_multipart_123",
        "threadId": "thread_123",
        "labelIds": ["INBOX"],
        "payload": {
            "mimeType": "multipart/alternative",
            "headers": [
                {"name": "From", "value": "alice@company.com"},
                {"name": "Subject", "value": "Multipart Meeting Request"},
                {"name": "Date", "value": "Mon, 24 Aug 2026 15:30:00 GMT"},
            ],
            "parts": [
                {"mimeType": "text/plain", "body": {"data": encode_base64url(plain_text)}},
                {"mimeType": "text/html", "body": {"data": encode_base64url(html_text)}},
            ],
        },
    }

    details = extract_gmail_message_details(msg)
    assert details["sender"] == "alice@company.com"
    assert details["subject"] == "Multipart Meeting Request"
    assert details["content"] == plain_text


def test_3_nested_multipart_message():
    """Test 3: Deeply nested multipart message (parts -> parts -> parts)."""
    deep_text = "Deeply nested email text payload."

    msg = {
        "id": "msg_nested_999",
        "threadId": "thread_999",
        "payload": {
            "mimeType": "multipart/mixed",
            "headers": [
                {"name": "FROM", "value": "support@service.io"},
                {"name": "SUBJECT", "value": "Nested Alert"},
                {"name": "DATE", "value": "Mon, 24 Aug 2026 16:00:00 GMT"},
            ],
            "parts": [
                {
                    "mimeType": "multipart/related",
                    "parts": [
                        {
                            "mimeType": "multipart/alternative",
                            "parts": [
                                {
                                    "mimeType": "text/plain",
                                    "body": {"data": encode_base64url(deep_text)},
                                }
                            ],
                        }
                    ],
                }
            ],
        },
    }

    details = extract_gmail_message_details(msg)
    assert details["sender"] == "support@service.io"
    assert details["subject"] == "Nested Alert"
    assert details["content"] == deep_text


def test_4_missing_subject():
    """Test 4: Missing Subject header falls back to (No Subject)."""
    msg = {
        "id": "msg_nosubject_1",
        "payload": {
            "headers": [
                {"name": "From", "value": "user@test.org"},
                {"name": "Date", "value": "Mon, 24 Aug 2026 10:00:00 GMT"},
            ],
            "body": {"data": encode_base64url("Content with no subject.")},
        },
    }

    details = extract_gmail_message_details(msg)
    assert details["subject"] == "(No Subject)"
    assert details["sender"] == "user@test.org"


def test_5_missing_date():
    """Test 5: Missing Date header falls back to internalDate Unix ms timestamp."""
    msg = {
        "id": "msg_nodate_1",
        "internalDate": "1787580000000",  # Unix ms timestamp
        "payload": {
            "headers": [
                {"name": "From", "value": "cron@server.internal"},
                {"name": "Subject", "value": "Automated Backup"},
            ],
            "body": {"data": encode_base64url("Backup successful.")},
        },
    }

    details = extract_gmail_message_details(msg)
    assert details["sender"] == "cron@server.internal"
    assert details["subject"] == "Automated Backup"
    assert "2026" in details["date"]  # Formatted UTC date string contains 2026


def test_6_html_only_email():
    """Test 6: HTML-only email strips tags and formats readable plain text."""
    html_content = "<div><h1>Welcome!</h1><p>Thank you for subscribing to <strong>AgentFlow AI</strong>.</p></div>"

    msg = {
        "id": "msg_html_1",
        "payload": {
            "mimeType": "text/html",
            "headers": [
                {"name": "From", "value": "newsletter@agentflow.ai"},
                {"name": "Subject", "value": "Welcome to AgentFlow"},
            ],
            "body": {"data": encode_base64url(html_content)},
        },
    }

    details = extract_gmail_message_details(msg)
    assert "Welcome!" in details["content"]
    assert "Thank you for subscribing" in details["content"]
    assert "<h1>" not in details["content"]
    assert "<strong>" not in details["content"]


def test_7_base64url_decoding():
    """Test 7: Base64url decoder correctly converts -, _, and handles missing padding."""
    raw_str = "Special Characters & Symbols: 12345 !@#$%^&*()_+~`|}{[]:;?><,./-"
    b64_url = encode_base64url(raw_str)

    decoded = decode_base64url(b64_url)
    assert decoded == raw_str


def test_8_gmail_message_with_id_threadid_labelids_and_nested_payload():
    """Test 8: Gmail message containing id, threadId, labelIds, and nested payload."""
    msg = {
        "id": "1904b9876543210a",
        "threadId": "1904b9876543210a",
        "labelIds": ["INBOX", "UNREAD", "IMPORTANT"],
        "snippet": "Short preview snippet...",
        "payload": {
            "headers": [
                {"name": "From", "value": "CEO <ceo@enterprise.com>"},
                {"name": "Subject", "value": "Q4 Strategy Update"},
                {"name": "Date", "value": "Mon, 24 Aug 2026 18:00:00 GMT"},
            ],
            "body": {"data": encode_base64url("Full strategy document attached.")},
        },
    }

    details = extract_gmail_message_details(msg)
    assert details["messageId"] == "1904b9876543210a"
    assert details["threadId"] == "1904b9876543210a"
    assert details["labels"] == ["INBOX", "UNREAD", "IMPORTANT"]
    assert details["sender"] == "CEO <ceo@enterprise.com>"
    assert details["subject"] == "Q4 Strategy Update"
    assert details["content"] == "Full strategy document attached."


def test_9_real_workflow_list_then_get():
    """Test 9: Real workflow execution containing step_1: gmail.messages.list -> step_2: gmail.messages.get."""
    workflow_result = {
        "ok": True,
        "status": "COMPLETED",
        "execution_id": "exec_flow_2nodes",
        "nodes_executed": 2,
        "total_nodes": 2,
        "node_results": [
            {
                "node_id": "step_1",
                "operation": "gmail.messages.list",
                "status": "SUCCESS",
                "output": {
                    "body": {
                        "messages": [{"id": "1a03499609b8e702", "threadId": "1a03499609b8e702"}],
                        "resultSizeEstimate": 1,
                    }
                },
            },
            {
                "node_id": "step_2",
                "operation": "gmail.messages.get",
                "status": "SUCCESS",
                "output": {
                    "body": {
                        "id": "1a03499609b8e702",
                        "threadId": "1a03499609b8e702",
                        "labelIds": ["INBOX"],
                        "payload": {
                            "headers": [
                                {"name": "From", "value": "aswinkumaarsr.cs24@bitsathy.ac.in"},
                                {"name": "Subject", "value": "Assignment Submission"},
                                {"name": "Date", "value": "Mon, 24 Aug 2026 19:15:00 GMT"},
                            ],
                            "body": {"data": encode_base64url("Attached is the final lab report.")},
                        },
                    }
                },
            },
        ],
    }

    details = extract_gmail_message_details(workflow_result)
    assert details["messageId"] == "1a03499609b8e702"
    assert details["sender"] == "aswinkumaarsr.cs24@bitsathy.ac.in"
    assert details["subject"] == "Assignment Submission"
    assert details["date"] == "Mon, 24 Aug 2026 19:15:00 GMT"
    assert details["content"] == "Attached is the final lab report."


def test_10_real_workflow_unread_search_then_get():
    """Test 10: Real workflow: gmail.messages.list with q='is:unread' -> gmail.messages.get."""
    workflow_result = {
        "ok": True,
        "status": "COMPLETED",
        "execution_id": "exec_unread_flow",
        "nodes_executed": 2,
        "total_nodes": 2,
        "node_results": [
            {
                "node_id": "step_1",
                "operation": "gmail.messages.list",
                "status": "SUCCESS",
                "output": {
                    "body": {
                        "messages": [{"id": "unread_msg_777", "threadId": "thread_777"}],
                        "resultSizeEstimate": 1,
                    }
                },
            },
            {
                "node_id": "step_2",
                "operation": "gmail.messages.get",
                "status": "SUCCESS",
                "output": {
                    "body": {
                        "id": "unread_msg_777",
                        "threadId": "thread_777",
                        "labelIds": ["UNREAD", "INBOX"],
                        "payload": {
                            "headers": [
                                {"name": "From", "value": "billing@cloudservice.com"},
                                {"name": "Subject", "value": "Monthly Invoice #9982"},
                                {"name": "Date", "value": "Mon, 24 Aug 2026 20:00:00 GMT"},
                            ],
                            "body": {"data": encode_base64url("Your monthly statement is ready.")},
                        },
                    }
                },
            },
        ],
    }

    details = extract_gmail_message_details(workflow_result)
    assert details["messageId"] == "unread_msg_777"
    assert details["sender"] == "billing@cloudservice.com"
    assert details["subject"] == "Monthly Invoice #9982"
    assert details["content"] == "Your monthly statement is ready."
    assert "UNREAD" in details["labels"]
