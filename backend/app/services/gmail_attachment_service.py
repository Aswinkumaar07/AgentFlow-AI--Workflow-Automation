import base64
import mimetypes
import os
import re
import logging
from email.message import EmailMessage
from typing import Dict, Any, List, Optional

logger = logging.getLogger("agentflow.services.gmail_attachment_service")

MIME_TYPE_MAP = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".zip": "application/zip",
    ".csv": "text/csv",
    ".txt": "text/plain",
}


class GmailAttachmentService:
    """
    Manages Gmail MIME building with attachments, file uploads/downloads,
    and metadata extraction across PDF, Image, Word, Excel, ZIP formats.
    """

    def detect_attachment_intent(self, prompt: str) -> Dict[str, Any]:
        p_lower = prompt.lower().strip()

        # Check action
        is_download = any(k in p_lower for k in ["download attachment", "save attachment", "get attachment", "fetch attachment"])
        is_send = any(k in p_lower for k in ["with attachment", "attach file", "send attachment", "upload attachment"])

        # Extract file names
        file_match = re.search(r"\b([\w-]+\.(?:pdf|png|jpg|jpeg|docx|doc|xlsx|xls|zip|csv|txt))\b", prompt, re.IGNORECASE)
        filename = file_match.group(1) if file_match else None

        op_id = "gmail.attachments.download" if is_download else "gmail.messages.send"
        return {
            "is_attachment_intent": is_download or is_send or filename is not None,
            "operation_id": op_id,
            "filename": filename,
        }

    def get_mime_type(self, filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        if ext in MIME_TYPE_MAP:
            return MIME_TYPE_MAP[ext]
        guess, _ = mimetypes.guess_type(filename)
        return guess or "application/octet-stream"

    def build_mime_with_attachments(
        self,
        to_addr: str,
        subject: str,
        body: str,
        from_addr: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        html_body: Optional[str] = None,
    ) -> str:
        """
        Builds a MIME EmailMessage containing optional file attachments and HTML alternative body,
        encodes to Base64URL string.
        """
        mime_msg = EmailMessage()
        mime_msg["To"] = to_addr
        mime_msg["Subject"] = subject
        mime_msg["MIME-Version"] = "1.0"
        if from_addr:
            mime_msg["From"] = from_addr
        if cc:
            mime_msg["Cc"] = cc
        if bcc:
            mime_msg["Bcc"] = bcc

        mime_msg.set_content(body)
        if html_body:
            mime_msg.add_alternative(html_body, subtype="html")

        if attachments:
            for att in attachments:
                filename = att.get("filename") or "attachment.bin"
                raw_bytes = att.get("content_bytes")
                if not raw_bytes and att.get("base64_data"):
                    b64 = att["base64_data"]
                    b64_clean = b64.replace("-", "+").replace("_", "/")
                    missing_padding = len(b64_clean) % 4
                    if missing_padding:
                        b64_clean += "=" * (4 - missing_padding)
                    raw_bytes = base64.b64decode(b64_clean)
                elif not raw_bytes and att.get("file_path") and os.path.exists(att["file_path"]):
                    with open(att["file_path"], "rb") as f:
                        raw_bytes = f.read()

                if raw_bytes:
                    mime_type = att.get("mime_type") or self.get_mime_type(filename)
                    main_type, sub_type = mime_type.split("/", 1) if "/" in mime_type else ("application", "octet-stream")
                    mime_msg.add_attachment(
                        raw_bytes,
                        maintype=main_type,
                        subtype=sub_type,
                        filename=filename,
                    )

        raw_bytes = mime_msg.as_bytes()
        return base64.urlsafe_b64encode(raw_bytes).decode("utf-8")

    def save_attachment_payload(
        self,
        attachment_id: str,
        filename: str,
        base64_data: str,
        save_dir: str = "attachments_output",
    ) -> Dict[str, Any]:
        """Saves base64 attachment data to local file and returns metadata."""
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)

        clean_b64 = base64_data.replace("-", "+").replace("_", "/")
        missing_padding = len(clean_b64) % 4
        if missing_padding:
            clean_b64 += "=" * (4 - missing_padding)

        file_bytes = base64.b64decode(clean_b64)
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        mime_type = self.get_mime_type(filename)
        return {
            "attachment_id": attachment_id,
            "filename": filename,
            "mime_type": mime_type,
            "size_bytes": len(file_bytes),
            "saved_path": save_path,
            "status": "saved",
        }


gmail_attachment_service = GmailAttachmentService()
