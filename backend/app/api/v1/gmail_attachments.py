import base64
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from app.dependencies.auth import get_current_user
from app.models.users import User
from app.connectors.manager import connector_manager
from app.utils.gmail_attachment_normalizer import sanitize_filename, MAX_ATTACHMENT_SIZE

logger = logging.getLogger("agentflow.api.v1.gmail_attachments")
router = APIRouter(prefix="/gmail", tags=["Gmail Attachments"])


@router.get("/messages/{message_id}/attachments/{attachment_id}", status_code=status.HTTP_200_OK)
async def get_gmail_attachment(
    message_id: str,
    attachment_id: str,
    filename: str = Query("attachment.bin"),
    mime_type: str = Query("application/octet-stream"),
    current_user: User = Depends(get_current_user),
):
    """
    Sprint AI-22: Secure, authenticated Gmail attachment proxy endpoint.
    Retrieves attachment binary payload through backend OAuth credentials without exposing tokens to frontend.
    """
    user_id = str(current_user.id) if current_user and hasattr(current_user, "id") and current_user.id else "usr_1"
    logger.info(f"[AI-22][ATTACHMENT_FETCH] message_id={message_id} attachment_id={attachment_id}")

    try:
        res = await connector_manager.execute(
            provider="Gmail",
            operation_id="gmail.attachments.download",
            parameters={
                "message_id": message_id,
                "attachment_id": attachment_id,
                "filename": filename,
                "save_to_disk": False,
            },
            tenant_id=user_id,
        )

        if not res.success or not res.data:
            err_msg = res.error_message or "Failed to download attachment from Gmail API"
            logger.error(f"[AI-22][ATTACHMENT_FAILURE] message_id={message_id} attachment_id={attachment_id} error='{err_msg}'")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

        data_obj = res.data or {}
        raw_b64 = data_obj.get("data") or data_obj.get("body", {}).get("data") or ""

        if not raw_b64:
            logger.error(f"[AI-22][ATTACHMENT_FAILURE] message_id={message_id} attachment_id={attachment_id} error='Empty payload returned'")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment payload is empty")

        clean_b64 = raw_b64.replace("-", "+").replace("_", "/")
        missing_padding = len(clean_b64) % 4
        if missing_padding:
            clean_b64 += "=" * (4 - missing_padding)

        file_bytes = base64.b64decode(clean_b64)
        file_size = len(file_bytes)

        if file_size > MAX_ATTACHMENT_SIZE:
            logger.warning(f"[AI-22][ATTACHMENT_SKIPPED] reason='exceeds_max_size' filename={filename} size={file_size}")
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Attachment exceeds maximum allowed size of 10 MB")

        clean_name = sanitize_filename(filename)
        out_mime = data_obj.get("mimeType") or mime_type or "application/octet-stream"

        logger.info(f"[AI-22][ATTACHMENT_SUCCESS] filename={clean_name} mime_type={out_mime} size={file_size}")

        disposition = "inline" if out_mime.startswith("image/") or out_mime == "application/pdf" else "attachment"
        return Response(
            content=file_bytes,
            media_type=out_mime,
            headers={
                "Content-Disposition": f'{disposition}; filename="{clean_name}"',
                "Cache-Control": "private, max-age=3600",
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[AI-22][ATTACHMENT_FAILURE] message_id={message_id} attachment_id={attachment_id} error='{str(exc)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal attachment retrieval error: {str(exc)}")
