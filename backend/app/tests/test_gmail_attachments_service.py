import base64
import os
import pytest
from app.services.gmail_attachment_service import gmail_attachment_service, GmailAttachmentService
from app.agents.planner.planner_v4 import intelligent_planner_v4


def test_mime_type_detection_for_supported_formats():
    service = GmailAttachmentService()

    assert service.get_mime_type("report.pdf") == "application/pdf"
    assert service.get_mime_type("image.png") == "image/png"
    assert service.get_mime_type("photo.jpeg") == "image/jpeg"
    assert service.get_mime_type("document.docx") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert service.get_mime_type("legacy.doc") == "application/msword"
    assert service.get_mime_type("spreadsheet.xlsx") == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert service.get_mime_type("data.xls") == "application/vnd.ms-excel"
    assert service.get_mime_type("archive.zip") == "application/zip"


def test_build_mime_with_attachment_and_encode():
    service = GmailAttachmentService()
    sample_content = b"%PDF-1.4 Mock PDF Content"

    b64_mime = service.build_mime_with_attachments(
        to_addr="john@example.com",
        subject="Monthly Financial Report",
        body="Please find attached the report.",
        attachments=[
            {
                "filename": "Q3_Financials.pdf",
                "content_bytes": sample_content,
                "mime_type": "application/pdf",
            }
        ],
    )

    assert isinstance(b64_mime, str)
    assert len(b64_mime) > 0

    # Decode and check headers & filename presence
    decoded_mime = base64.urlsafe_b64decode(b64_mime).decode("utf-8", errors="ignore")
    assert "john@example.com" in decoded_mime
    assert "Monthly Financial Report" in decoded_mime
    assert "Q3_Financials.pdf" in decoded_mime


def test_save_attachment_payload(tmp_path):
    service = GmailAttachmentService()
    raw_bytes = b"Hello, this is a test excel file content."
    b64_urlsafe = base64.urlsafe_b64encode(raw_bytes).decode("utf-8")

    meta = service.save_attachment_payload(
        attachment_id="att_12345",
        filename="test_sheet.xlsx",
        base64_data=b64_urlsafe,
        save_dir=str(tmp_path),
    )

    assert meta["status"] == "saved"
    assert meta["filename"] == "test_sheet.xlsx"
    assert meta["mime_type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert meta["size_bytes"] == len(raw_bytes)
    assert os.path.exists(meta["saved_path"])


def test_planner_detects_attachment_intent():
    prompt_dl = "Download attachment report.pdf from message msg_123"
    plan_dl = intelligent_planner_v4.plan(prompt_dl)
    node_dl = [n for n in plan_dl.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]][0]
    op_dl = node_dl.get("operation") or node_dl.get("operation_id")
    assert op_dl == "gmail.attachments.download"
    assert node_dl["parameters"]["filename"] == "report.pdf"

    prompt_send = "Send email to alice@example.com with attachment invoice.xlsx"
    plan_send = intelligent_planner_v4.plan(prompt_send)
    node_send = [n for n in plan_send.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]][0]
    op_send = node_send.get("operation") or node_send.get("operation_id")
    assert op_send == "gmail.messages.send"
    assert "attachments" in node_send["parameters"]
    assert node_send["parameters"]["attachments"][0]["filename"] == "invoice.xlsx"
