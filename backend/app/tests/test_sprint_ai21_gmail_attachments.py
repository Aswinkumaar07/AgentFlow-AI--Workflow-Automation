import pytest
from typing import Dict, Any, List
from app.utils.gmail_attachment_normalizer import (
    extract_gmail_attachments,
    safe_base64url_decode,
    sanitize_filename,
    resolve_cids_in_html,
    MAX_ATTACHMENT_SIZE,
)


def test_1_plain_text_email_no_attachments():
    msg = {
        "id": "msg_plain_001",
        "payload": {
            "mimeType": "text/plain",
            "body": {"data": "SGVsbG8gd29ybGQ="},
        },
    }
    res = extract_gmail_attachments(msg)
    assert len(res["attachments"]) == 0
    assert len(res["inline_images"]) == 0
    assert len(res["all_attachments"]) == 0


def test_2_html_email_no_attachments():
    msg = {
        "id": "msg_html_002",
        "payload": {
            "mimeType": "multipart/alternative",
            "parts": [
                {"mimeType": "text/plain", "body": {"data": "SGVsbG8="}},
                {"mimeType": "text/html", "body": {"data": "<p>Hello</p>"}},
            ],
        },
    }
    res = extract_gmail_attachments(msg)
    assert len(res["attachments"]) == 0
    assert len(res["inline_images"]) == 0


def test_3_single_png_attachment():
    msg = {
        "id": "msg_png_003",
        "payload": {
            "parts": [
                {"mimeType": "text/plain", "body": {"data": "SGVsbG8="}},
                {
                    "filename": "screenshot.png",
                    "mimeType": "image/png",
                    "headers": [{"name": "Content-Disposition", "value": "attachment; filename=\"screenshot.png\""}],
                    "body": {"attachmentId": "att_png_123", "size": 102400},
                },
            ]
        },
    }
    res = extract_gmail_attachments(msg)
    assert len(res["attachments"]) == 1
    png_att = res["attachments"][0]
    assert png_att["filename"] == "screenshot.png"
    assert png_att["mime_type"] == "image/png"
    assert png_att["is_image"] is True
    assert png_att["is_inline"] is False


def test_4_single_jpeg_attachment():
    msg = {
        "id": "msg_jpg_004",
        "payload": {
            "parts": [
                {
                    "filename": "photo.jpg",
                    "mimeType": "image/jpeg",
                    "headers": [{"name": "Content-Disposition", "value": "attachment; filename=\"photo.jpg\""}],
                    "body": {"attachmentId": "att_jpg_456", "size": 204800},
                }
            ]
        },
    }
    res = extract_gmail_attachments(msg)
    assert len(res["attachments"]) == 1
    jpg_att = res["attachments"][0]
    assert jpg_att["filename"] == "photo.jpg"
    assert jpg_att["mime_type"] == "image/jpeg"
    assert jpg_att["is_image"] is True


def test_5_multiple_attachments():
    msg = {
        "id": "msg_multi_005",
        "payload": {
            "parts": [
                {"filename": "doc1.pdf", "mimeType": "application/pdf", "body": {"attachmentId": "a1", "size": 5000}},
                {"filename": "img1.png", "mimeType": "image/png", "body": {"attachmentId": "a2", "size": 6000}},
                {"filename": "data.csv", "mimeType": "text/csv", "body": {"attachmentId": "a3", "size": 7000}},
            ]
        },
    }
    res = extract_gmail_attachments(msg)
    assert len(res["all_attachments"]) == 3
    assert len(res["attachments"]) == 3


def test_6_nested_multipart_attachment():
    msg = {
        "id": "msg_nested_006",
        "payload": {
            "mimeType": "multipart/mixed",
            "parts": [
                {
                    "mimeType": "multipart/related",
                    "parts": [
                        {
                            "mimeType": "multipart/alternative",
                            "parts": [
                                {"mimeType": "text/plain", "body": {"data": "Plain text"}},
                                {"mimeType": "text/html", "body": {"data": "<p>HTML</p>"}},
                            ],
                        },
                        {
                            "filename": "deep_nested.pdf",
                            "mimeType": "application/pdf",
                            "body": {"attachmentId": "att_deep_999", "size": 15000},
                        },
                    ],
                }
            ],
        },
    }
    res = extract_gmail_attachments(msg)
    assert len(res["all_attachments"]) == 1
    assert res["all_attachments"][0]["filename"] == "deep_nested.pdf"


def test_7_inline_image_with_content_id():
    msg = {
        "id": "msg_inline_007",
        "payload": {
            "parts": [
                {
                    "filename": "logo.png",
                    "mimeType": "image/png",
                    "headers": [
                        {"name": "Content-ID", "value": "<logo_cid_001>"},
                        {"name": "Content-Disposition", "value": "inline; filename=\"logo.png\""},
                    ],
                    "body": {"attachmentId": "att_inline_1", "size": 1200},
                }
            ]
        },
    }
    res = extract_gmail_attachments(msg)
    assert len(res["inline_images"]) == 1
    inline_img = res["inline_images"][0]
    assert inline_img["content_id"] == "logo_cid_001"
    assert inline_img["is_inline"] is True
    assert inline_img["disposition"] == "inline"


def test_8_html_body_referencing_cid():
    html_body = '<html><body><h1>Welcome</h1><img src="cid:logo_cid_001"></body></html>'
    cid_map = {"logo_cid_001": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="}
    resolved = resolve_cids_in_html(html_body, cid_map)
    assert "data:image/png;base64," in resolved
    assert "cid:logo_cid_001" not in resolved


def test_9_attachment_with_attachment_id():
    msg = {
        "id": "msg_attid_009",
        "payload": {
            "parts": [
                {"filename": "report.pdf", "mimeType": "application/pdf", "body": {"attachmentId": "att_valid_123", "size": 3400}}
            ]
        },
    }
    res = extract_gmail_attachments(msg)
    assert res["all_attachments"][0]["attachment_id"] == "att_valid_123"


def test_10_attachment_with_missing_attachment_id():
    msg = {
        "id": "msg_noattid_010",
        "payload": {
            "parts": [
                {"filename": "embedded_note.txt", "mimeType": "text/plain", "body": {"data": "Tm90ZQ==", "size": 50}}
            ]
        },
    }
    res = extract_gmail_attachments(msg)
    assert len(res["all_attachments"]) == 1
    assert res["all_attachments"][0]["filename"] == "embedded_note.txt"


def test_11_pdf_attachment():
    msg = {
        "id": "msg_pdf_011",
        "payload": {
            "parts": [
                {"filename": "contract.pdf", "mimeType": "application/pdf", "body": {"attachmentId": "att_pdf_111", "size": 88000}}
            ]
        },
    }
    res = extract_gmail_attachments(msg)
    att = res["all_attachments"][0]
    assert att["is_pdf"] is True
    assert att["is_document"] is True
    assert att["is_image"] is False


def test_12_zip_attachment():
    msg = {
        "id": "msg_zip_012",
        "payload": {
            "parts": [
                {"filename": "archive.zip", "mimeType": "application/zip", "body": {"attachmentId": "att_zip_222", "size": 450000}}
            ]
        },
    }
    res = extract_gmail_attachments(msg)
    att = res["all_attachments"][0]
    assert att["filename"] == "archive.zip"
    assert att["mime_type"] == "application/zip"


def test_13_multiple_emails_mixed_attachments():
    msg1 = {"id": "m1", "payload": {"parts": [{"filename": "f1.png", "mimeType": "image/png", "body": {"attachmentId": "a1"}}]}}
    msg2 = {"id": "m2", "payload": {"mimeType": "text/plain", "body": {"data": "No file"}}}
    
    r1 = extract_gmail_attachments(msg1)
    r2 = extract_gmail_attachments(msg2)
    
    assert len(r1["all_attachments"]) == 1
    assert len(r2["all_attachments"]) == 0


def test_14_attachment_api_failure_fallback():
    # If attachment size exceeds MAX_ATTACHMENT_SIZE limit
    msg = {
        "id": "msg_fail_014",
        "payload": {
            "parts": [
                {"filename": "oversized.iso", "mimeType": "application/octet-stream", "body": {"attachmentId": "a_huge", "size": 50 * 1024 * 1024}}
            ]
        },
    }
    res = extract_gmail_attachments(msg)
    att = res["all_attachments"][0]
    assert att["available"] is False
    assert "exceeds" in att["error"].lower()


def test_15_large_attachment_safety():
    # Large attachment size safety threshold check
    msg = {
        "id": "msg_large_015",
        "payload": {
            "parts": [
                {"filename": "dataset.csv", "mimeType": "text/csv", "body": {"attachmentId": "att_large", "size": 15 * 1024 * 1024}}
            ]
        },
    }
    res = extract_gmail_attachments(msg)
    att = res["all_attachments"][0]
    assert att["download_available"] is False
    assert att["size"] == 15 * 1024 * 1024


def test_16_empty_gmail_search_compatibility():
    res = extract_gmail_attachments({})
    assert res["attachments"] == []
    assert res["inline_images"] == []
    assert res["all_attachments"] == []


def test_17_existing_single_email_workflow_compatibility():
    from app.utils.gmail_attachment_normalizer import safe_base64url_decode
    encoded = "SGVsbG8gRnJvbSBHbWFpbCAh"
    decoded = safe_base64url_decode(encoded).decode("utf-8")
    assert decoded == "Hello From Gmail !"


def test_18_existing_multi_email_fanout_compatibility():
    emails_payload = [
        {"id": "msg_1", "payload": {"parts": [{"filename": "img.png", "mimeType": "image/png", "body": {"attachmentId": "a1"}}]}},
        {"id": "msg_2", "payload": {"mimeType": "text/plain", "body": {"data": "Plain text"}}},
    ]
    extracted = [extract_gmail_attachments(e) for e in emails_payload]
    assert len(extracted[0]["all_attachments"]) == 1
    assert len(extracted[1]["all_attachments"]) == 0
