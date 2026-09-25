import pytest
from app.utils.gmail_attachment_normalizer import (
    extract_gmail_attachments,
    sanitize_filename,
    MAX_ATTACHMENT_SIZE,
)


def test_sanitize_filename():
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\windows\\system32.dll") == "system32.dll"
    assert sanitize_filename("invoice 2026 #12.pdf") == "invoice_2026__12.pdf"
    assert sanitize_filename("") == "attachment.bin"


def test_extract_gmail_attachments_nested_payload():
    mock_message = {
        "id": "msg_test_123",
        "payload": {
            "mimeType": "multipart/mixed",
            "parts": [
                {
                    "mimeType": "multipart/alternative",
                    "parts": [
                        {"mimeType": "text/plain", "body": {"data": "SGVsbG8="}},
                        {"mimeType": "text/html", "body": {"data": "<p>Hello</p>"}},
                    ],
                },
                {
                    "filename": "photo.jpg",
                    "mimeType": "image/jpeg",
                    "headers": [
                        {"name": "Content-Disposition", "value": "attachment; filename=\"photo.jpg\""}
                    ],
                    "body": {
                        "attachmentId": "att_img_001",
                        "size": 150000,
                    },
                },
                {
                    "filename": "invoice.pdf",
                    "mimeType": "application/pdf",
                    "headers": [
                        {"name": "Content-Disposition", "value": "attachment; filename=\"invoice.pdf\""}
                    ],
                    "body": {
                        "attachmentId": "att_pdf_002",
                        "size": 850000,
                    },
                },
            ],
        },
    }

    attachments = extract_gmail_attachments(mock_message)

    assert len(attachments) == 2

    # Image attachment check
    img_att = next(a for a in attachments if a["attachment_id"] == "att_img_001")
    assert img_att["filename"] == "photo.jpg"
    assert img_att["mime_type"] == "image/jpeg"
    assert img_att["size"] == 150000
    assert img_att["is_image"] is True
    assert img_att["is_pdf"] is False
    assert img_att["available"] is True

    # PDF attachment check
    pdf_att = next(a for a in attachments if a["attachment_id"] == "att_pdf_002")
    assert pdf_att["filename"] == "invoice.pdf"
    assert pdf_att["mime_type"] == "application/pdf"
    assert pdf_att["size"] == 850000
    assert pdf_att["is_image"] is False
    assert pdf_att["is_pdf"] is True
    assert pdf_att["is_document"] is True
    assert pdf_att["available"] is True


def test_extract_gmail_attachments_oversized_file():
    mock_message = {
        "id": "msg_huge_456",
        "payload": {
            "parts": [
                {
                    "filename": "large_dataset.zip",
                    "mimeType": "application/zip",
                    "body": {
                        "attachmentId": "att_huge_001",
                        "size": 25 * 1024 * 1024,  # 25 MB
                    },
                }
            ]
        },
    }

    attachments = extract_gmail_attachments(mock_message)
    assert len(attachments) == 1
    huge_att = attachments[0]
    assert huge_att["filename"] == "large_dataset.zip"
    assert huge_att["available"] is False
    assert "exceeds" in huge_att["error"].lower()


def test_extract_gmail_attachments_empty():
    assert extract_gmail_attachments(None) == []
    assert extract_gmail_attachments({}) == []
    assert extract_gmail_attachments({"id": "123", "payload": {}}) == []
