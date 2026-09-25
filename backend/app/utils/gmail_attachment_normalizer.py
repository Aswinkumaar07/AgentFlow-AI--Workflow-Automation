import base64
import os
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("agentflow.utils.gmail_attachment_normalizer")

MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 MB limit for inline loading

IMAGE_MIME_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"}
PDF_MIME_TYPES = {"application/pdf"}
DOCUMENT_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/json",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/zip",
    "application/x-zip-compressed",
}

MULTIPART_CONTAINERS = {
    "multipart/mixed",
    "multipart/alternative",
    "multipart/related",
    "multipart/digest",
    "multipart/signed",
    "multipart/parallel",
}


def safe_base64url_decode(b64_str: str) -> bytes:
    """
    Safely decodes Gmail base64url encoded strings.
    Handles '-' -> '+', '_' -> '/', and missing '=' padding.
    """
    if not b64_str or not isinstance(b64_str, str):
        return b""
    clean = b64_str.replace("-", "+").replace("_", "/")
    missing_padding = len(clean) % 4
    if missing_padding:
        clean += "=" * (4 - missing_padding)
    try:
        return base64.b64decode(clean)
    except Exception as exc:
        logger.warning(f"Base64URL decode failed: {exc}")
        return b""
        

def sanitize_filename(filename: str) -> str:
    """Sanitizes filename to prevent path traversal and unsafe header injections."""
    if not filename:
        return "attachment.bin"
    clean = os.path.basename(filename)
    clean = re.sub(r"[^\w\.-]", "_", clean)
    return clean or "attachment.bin"


def extract_gmail_attachments(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sprint AI-21: Recursively walks Gmail message payload tree to extract all attachments and inline images.
    Supports multipart/mixed, multipart/alternative, multipart/related, and nested subparts.
    
    Returns:
    {
        "attachments": [...],
        "inline_images": [...],
        "all_attachments": [...],
        "cid_map": { content_id: data_url_or_obj }
    }
    """
    if not isinstance(message, dict):
        return {
            "attachments": [],
            "inline_images": [],
            "all_attachments": [],
            "cid_map": {},
        }

    attachments: List[Dict[str, Any]] = []
    inline_images: List[Dict[str, Any]] = []
    all_attachments: List[Dict[str, Any]] = []
    cid_map: Dict[str, str] = {}
    seen_keys = set()

    msg_id = message.get("id") or message.get("messageId") or "unknown"
    payload = message.get("payload") or message.get("body", {}).get("payload") or message

    def _walk_part(part: Dict[str, Any]):
        if not isinstance(part, dict):
            return

        filename = (part.get("filename") or "").strip()
        mime_type = (part.get("mimeType") or "").strip().lower()
        body = part.get("body") or {}
        attachment_id = (body.get("attachmentId") or part.get("attachmentId") or "").strip()
        size = body.get("size") or part.get("size") or 0
        raw_b64_data = body.get("data") or part.get("data") or ""

        # Check headers for Content-Disposition & Content-ID
        headers = part.get("headers") or []
        content_disposition = ""
        content_id = ""
        for h in headers:
            if not isinstance(h, dict):
                continue
            h_name = (h.get("name") or "").lower()
            h_val = h.get("value") or ""
            if h_name == "content-disposition":
                content_disposition = h_val
            elif h_name == "content-id":
                content_id = h_val.strip("<>")

        # Determine if this part is an attachment or inline image
        is_attachment_part = False
        if filename or attachment_id or content_id:
            is_attachment_part = True
        elif mime_type and mime_type not in MULTIPART_CONTAINERS and mime_type not in ["text/plain", "text/html"]:
            is_attachment_part = True

        if is_attachment_part:
            is_inline = "inline" in content_disposition.lower() or bool(content_id)
            is_img = mime_type in IMAGE_MIME_TYPES or mime_type.startswith("image/")
            is_pdf_file = mime_type in PDF_MIME_TYPES
            is_doc_file = mime_type in DOCUMENT_MIME_TYPES or is_pdf_file or mime_type.startswith("text/")

            unique_key = attachment_id or content_id or f"{filename}_{size}_{mime_type}"
            if unique_key not in seen_keys:
                seen_keys.add(unique_key)
                clean_name = sanitize_filename(filename or f"attachment_{attachment_id[:8] if attachment_id else 'file'}.bin")

                # Format base64 data URL if body data is embedded directly
                data_url = None
                data_b64 = None
                if raw_b64_data:
                    decoded_bytes = safe_base64url_decode(raw_b64_data)
                    if decoded_bytes:
                        data_b64 = base64.b64encode(decoded_bytes).decode("utf-8")
                        data_url = f"data:{mime_type or 'application/octet-stream'};base64,{data_b64}"
                elif attachment_id:
                    # Provide backend proxy URL
                    data_url = f"/api/v1/gmail/messages/{msg_id}/attachments/{attachment_id}?filename={clean_name}&mime_type={mime_type}"

                att_obj = {
                    "attachment_id": attachment_id,
                    "filename": clean_name,
                    "mime_type": mime_type or "application/octet-stream",
                    "size": size,
                    "content_id": content_id,
                    "disposition": "inline" if is_inline else "attachment",
                    "is_inline": is_inline,
                    "is_image": is_img,
                    "is_pdf": is_pdf_file,
                    "is_document": is_doc_file,
                    "data": data_url or data_b64,
                    "data_b64": data_b64,
                    "available": size <= MAX_ATTACHMENT_SIZE,
                    "download_available": size <= MAX_ATTACHMENT_SIZE,
                    "error": None if size <= MAX_ATTACHMENT_SIZE else "Attachment exceeds maximum size limit of 10 MB",
                }

                if size > MAX_ATTACHMENT_SIZE:
                    logger.warning(f"[AI-21][ATTACHMENT_SKIPPED] reason='exceeds_max_size' filename={clean_name} size={size}")

                all_attachments.append(att_obj)

                if is_inline or (is_img and content_id):
                    inline_images.append(att_obj)
                    if content_id and data_url:
                        cid_map[content_id] = data_url
                    logger.info(
                        f"[AI-21][INLINE_IMAGE_DETECTED] message_id={msg_id} "
                        f"content_id={content_id} mime_type={mime_type}"
                    )
                else:
                    attachments.append(att_obj)
                    logger.info(
                        f"[AI-21][ATTACHMENT_DETECTED] message_id={msg_id} "
                        f"attachment_id={attachment_id} filename={clean_name} mime_type={mime_type}"
                    )

        # Recursively walk subparts
        subparts = part.get("parts") or []
        for subpart in subparts:
            _walk_part(subpart)

    _walk_part(payload)

    if not all_attachments:
        logger.info(f"[AI-21][NO_ATTACHMENTS] message_id={msg_id}")

    return {
        "attachments": attachments,
        "inline_images": inline_images,
        "all_attachments": all_attachments,
        "cid_map": cid_map,
    }


def resolve_cids_in_html(html_body: str, cid_map: Dict[str, str]) -> str:
    """
    Replaces src="cid:CONTENT_ID" references in HTML email body with resolved data URLs or proxy URLs.
    """
    if not html_body or not cid_map:
        return html_body or ""

    def _replace_match(match):
        prefix = match.group(1)  # e.g., 'src="' or "src='"
        cid = match.group(2).strip("<>")
        suffix = match.group(3)
        if cid in cid_map:
            return f"{prefix}{cid_map[cid]}{suffix}"
        return match.group(0)

    # Replace src="cid:..." and src='cid:...'
    pattern = re.compile(r"""(src=["']cid:)([^"']+)(["'])""", re.IGNORECASE)
    return pattern.sub(_replace_match, html_body)
