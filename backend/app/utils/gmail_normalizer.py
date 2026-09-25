import base64
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def decode_base64url(base64_url: str) -> str:
    """Decode Gmail base64url data string with UTF-8 support."""
    if not base64_url or not isinstance(base64_url, str):
        return ""
    try:
        # Replace base64url characters and fix padding
        clean = base64_url.replace("-", "+").replace("_", "/")
        padding = len(clean) % 4
        if padding > 0:
            clean += "=" * (4 - padding)
        decoded_bytes = base64.b64decode(clean)
        return decoded_bytes.decode("utf-8", errors="replace")
    except Exception:
        return base64_url


def strip_html_tags(html: str) -> str:
    """Strip HTML tags and convert formatting for plain text display."""
    if not html or not isinstance(html, str):
        return ""
    # Strip script/style
    clean = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", html, flags=re.IGNORECASE)
    clean = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"<br\s*/?>", "\n", clean, flags=re.IGNORECASE)
    clean = re.sub(r"</p>", "\n\n", clean, flags=re.IGNORECASE)
    clean = re.sub(r"<[^>]+>", "", clean)
    clean = clean.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    clean = re.sub(r"\n\s*\n", "\n\n", clean)
    return clean.strip()


def extract_body_from_payload(payload: Dict[str, Any]) -> str:
    """Recursively extract plain-text or HTML content from Gmail message payload."""
    if not payload or not isinstance(payload, dict):
        return ""

    # CASE A: Simple plain text or HTML body
    body_data = payload.get("body", {}).get("data")
    mime_type = str(payload.get("mimeType", "")).lower()
    if body_data:
        decoded = decode_base64url(body_data)
        if "html" in mime_type:
            stripped = strip_html_tags(decoded)
            return stripped if stripped else decoded
        return decoded

    # CASE B & C: Multipart / alternative / nested parts
    parts = payload.get("parts")
    if isinstance(parts, list) and parts:
        text_plain_part = ""
        text_html_part = ""

        def walk_parts(part_list: List[Dict[str, Any]]):
            nonlocal text_plain_part, text_html_part
            for part in part_list:
                if not isinstance(part, dict):
                    continue
                p_mime = str(part.get("mimeType", "")).lower()
                p_body_data = part.get("body", {}).get("data")

                if p_body_data:
                    decoded_part = decode_base64url(p_body_data)
                    if p_mime == "text/plain" and not text_plain_part:
                        text_plain_part = decoded_part
                    elif p_mime == "text/html" and not text_html_part:
                        stripped_part = strip_html_tags(decoded_part)
                        text_html_part = stripped_part if stripped_part else decoded_part

                sub_parts = part.get("parts")
                if isinstance(sub_parts, list) and sub_parts:
                    walk_parts(sub_parts)

        walk_parts(parts)

        if text_plain_part:
            return text_plain_part.strip()
        if text_html_part:
            return text_html_part.strip()

    return ""


def extract_gmail_message_details(input_data: Any) -> Dict[str, Any]:
    """
    Extracts structured Gmail message details:
    messageId, threadId, sender, subject, date, content, labels, isDetailed
    """
    msg = input_data
    if not msg:
        return {
            "messageId": "—",
            "threadId": "—",
            "sender": "Unknown Sender",
            "subject": "(No Subject)",
            "date": "—",
            "content": "No message content available.",
            "labels": [],
            "isDetailed": False,
        }

    # Handle workflow execution result objects with node_results
    if isinstance(msg, dict) and isinstance(msg.get("node_results"), list) and msg["node_results"]:
        node_results = msg["node_results"]
        # Prefer node result from a `gmail.messages.get` step if present
        get_step = None
        for r in reversed(node_results):
            op = r.get("operation", "")
            out = r.get("output", {})
            if op in ["gmail.messages.get", "gmail.get"] or (isinstance(out, dict) and (out.get("body", {}).get("payload") or out.get("payload"))):
                get_step = r
                break
        target_step = get_step if get_step else node_results[-1]
        msg = target_step.get("output", target_step)

    # Unwrap nested response/body structures
    if isinstance(msg, dict):
        if isinstance(msg.get("messages"), list) and msg["messages"]:
            msg = msg["messages"][0]
        if "body" in msg and isinstance(msg["body"], dict):
            msg = msg["body"]
        if "response" in msg and isinstance(msg["response"], dict):
            msg = msg["response"]
        if "body" in msg and isinstance(msg["body"], dict):
            msg = msg["body"]

    if not isinstance(msg, dict):
        return {
            "messageId": "—",
            "threadId": "—",
            "sender": "Unknown Sender",
            "subject": "(No Subject)",
            "date": "—",
            "content": "No message content available.",
            "labels": [],
            "isDetailed": False,
        }

    # Extract ID / Thread / Labels
    message_id = str(msg.get("id") or msg.get("messageId") or "—")
    thread_id = str(msg.get("threadId") or "—")
    labels = msg.get("labelIds") if isinstance(msg.get("labelIds"), list) else []

    # Extract Headers (case-insensitive From, Subject, Date)
    payload = msg.get("payload") if isinstance(msg.get("payload"), dict) else msg
    headers = payload.get("headers") if isinstance(payload.get("headers"), list) else msg.get("headers", [])

    sender = ""
    subject = ""
    date_val = ""

    if isinstance(headers, list):
        for h in headers:
            if not isinstance(h, dict) or not h.get("name"):
                continue
            name_lower = str(h["name"]).lower()
            if name_lower == "from" and not sender:
                sender = str(h.get("value") or "")
            if name_lower == "subject" and not subject:
                subject = str(h.get("value") or "")
            if name_lower == "date" and not date_val:
                date_val = str(h.get("value") or "")

    # Fallback for Date if missing from headers
    if not date_val and msg.get("internalDate"):
        try:
            ms = int(msg["internalDate"])
            date_val = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        except Exception:
            pass

    # Extract Body Content
    content = extract_body_from_payload(payload)
    if not content and isinstance(msg.get("snippet"), str) and msg["snippet"].strip():
        content = msg["snippet"].strip()

    if not content:
        content = "No message content available."

    is_detailed = bool(sender or subject or (isinstance(payload, dict) and payload.get("headers")))

    return {
        "messageId": message_id,
        "threadId": thread_id,
        "sender": sender or "Unknown Sender",
        "subject": subject or "(No Subject)",
        "date": date_val or "—",
        "content": content,
        "labels": labels,
        "isDetailed": is_detailed,
    }
