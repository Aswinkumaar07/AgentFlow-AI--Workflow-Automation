import base64
import pytest
from app.services.rich_html_email_service import rich_html_email_service, RichHTMLEmailService
from app.services.gmail_attachment_service import gmail_attachment_service
from app.agents.planner.planner_v4 import intelligent_planner_v4


def test_is_rich_html_requested():
    service = RichHTMLEmailService()

    assert service.is_rich_html_requested("Send a beautiful email to john@example.com") is True
    assert service.is_rich_html_requested("Send an HTML email newsletter") is True
    assert service.is_rich_html_requested("Send styled email with table and button") is True
    assert service.is_rich_html_requested("Send simple email") is False


def test_generate_rich_html_structure():
    service = RichHTMLEmailService()

    html = service.generate_rich_html(
        subject="Monthly Performance Report",
        body_text="Here is your monthly summary.\n\nPlease review the attached metrics.",
        button_label="View Analytics Dashboard",
        button_url="https://app.agentflow.ai/dashboard",
        table_data={
            "headers": ["Metric", "Value", "Status"],
            "rows": [
                ["Deliverability", "99.8%", "Optimal"],
                ["Open Rate", "45.2%", "High"],
            ],
        },
        list_items=["Review API latencies.", "Deploy v2.5 release."],
    )

    assert "<!DOCTYPE html>" in html
    assert "Monthly Performance Report" in html
    assert "View Analytics Dashboard" in html
    assert "Deliverability" in html
    assert "Review API latencies." in html
    assert "background: linear-gradient" in html


def test_multipart_alternative_mime_building():
    plain = "Hello John, please see update."
    html = "<html><body><h1>Update</h1><p>Hello John</p></body></html>"

    b64_mime = gmail_attachment_service.build_mime_with_attachments(
        to_addr="john@example.com",
        subject="Project Update",
        body=plain,
        html_body=html,
    )

    decoded = base64.urlsafe_b64decode(b64_mime).decode("utf-8", errors="ignore")
    assert "multipart/alternative" in decoded
    assert "Content-Type: text/plain" in decoded
    assert "Content-Type: text/html" in decoded
    assert plain in decoded
    assert html in decoded


def test_planner_detects_beautiful_email_intent():
    prompt = "Send a beautiful email to john@example.com Subject: Quarterly Review Body: Great job team!"
    plan = intelligent_planner_v4.plan(prompt)

    nodes = [n for n in plan.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]]
    assert len(nodes) > 0
    node = nodes[0]

    assert "html_body" in node["parameters"]
    assert "<!DOCTYPE html>" in node["parameters"]["html_body"]
    assert "Quarterly Review" in node["parameters"]["html_body"]
