import base64
import logging
import time
from email.message import EmailMessage
from typing import Any, Dict, List, Optional

import httpx
from app.connectors.interfaces import BaseProviderAdapter
from app.connectors.models import (
    ConnectorCredentialModel,
    ConnectorMetadataModel,
    ConnectorRequestModel,
    ConnectorResponseModel,
    OperationSchemaModel,
    ParameterSchemaModel,
)
from app.connectors.security.secret_manager import secret_manager
from app.core.config import settings

logger = logging.getLogger("agentflow.connectors.providers.gmail")


class GmailAdapter(BaseProviderAdapter):
    """Production Provider Adapter for Google Gmail REST API. Zero Mocks. Real API Execution Only."""

    @property
    def provider_name(self) -> str:
        return "Gmail"

    def get_metadata(self) -> ConnectorMetadataModel:
        send_schema = OperationSchemaModel(
            id="gmail.messages.send",
            display_name="Send Email",
            description="Sends an email message with recipient, subject, body, CC, BCC, and attachment parameters.",
            required_parameters=[
                ParameterSchemaModel(name="to", display_name="To Recipient", type="string", required=True, description="Recipient email address"),
                ParameterSchemaModel(name="subject", display_name="Subject", type="string", required=True, description="Email subject line"),
                ParameterSchemaModel(name="body", display_name="Message Body", type="text", required=True, description="Email content in plain text or HTML"),
            ],
            optional_parameters=[
                ParameterSchemaModel(name="cc", display_name="CC Recipient", type="string", required=False, description="Carbon copy recipient email"),
                ParameterSchemaModel(name="bcc", display_name="BCC Recipient", type="string", required=False, description="Blind carbon copy recipient email"),
                ParameterSchemaModel(name="attachments", display_name="Attachments", type="array", required=False, description="List of file attachment URLs or IDs"),
            ],
            default_values={
                "to": "{{$json.email}}",
                "subject": "AgentFlow AI Notification",
                "body": "Hello, please find the automated message below.",
            },
        )

        list_schema = OperationSchemaModel(
            id="gmail.messages.list",
            display_name="List Messages",
            description="Retrieves a list of messages matching a Gmail search query.",
            required_parameters=[],
            optional_parameters=[
                ParameterSchemaModel(name="q", display_name="Search Query", type="string", required=False, description="Gmail search query (e.g. is:unread, label:invoices)", default_value="label:invoices"),
                ParameterSchemaModel(name="max_results", display_name="Max Results", type="number", required=False, description="Maximum messages to fetch", default_value=10),
            ],
            default_values={"q": "label:invoices", "max_results": 10},
        )

        get_schema = OperationSchemaModel(
            id="gmail.messages.get",
            display_name="Get Message Details",
            description="Fetches full details and payload of a specific message ID.",
            required_parameters=[
                ParameterSchemaModel(name="message_id", display_name="Message ID", type="string", required=True, description="Gmail message unique ID"),
            ],
            optional_parameters=[],
            default_values={"message_id": "{{step_1.id}}"},
        )

        search_schema = OperationSchemaModel(
            id="gmail.messages.search",
            display_name="Search Messages",
            description="Searches Gmail messages matching a specific search query.",
            required_parameters=[
                ParameterSchemaModel(name="q", display_name="Search Query", type="string", required=True, description="Gmail search query string"),
            ],
            optional_parameters=[
                ParameterSchemaModel(name="max_results", display_name="Max Results", type="number", required=False, description="Maximum messages to return", default_value=10),
            ],
            default_values={"q": "is:unread", "max_results": 10},
        )

        reply_schema = OperationSchemaModel(
            id="gmail.messages.reply",
            display_name="Reply to Message",
            description="Replies to an existing message thread.",
            required_parameters=[
                ParameterSchemaModel(name="message_id", display_name="Message ID", type="string", required=True, description="Message ID to reply to"),
                ParameterSchemaModel(name="to", display_name="To Recipient", type="string", required=True, description="Recipient email address"),
                ParameterSchemaModel(name="body", display_name="Reply Content", type="text", required=True, description="Body content of reply"),
            ],
            optional_parameters=[
                ParameterSchemaModel(name="subject", display_name="Subject", type="string", required=False, description="Subject of reply"),
            ],
            default_values={"message_id": "{{step_1.id}}", "to": "{{step_1.from}}", "subject": "Re: Message", "body": "Thank you for your email."},
        )

        forward_schema = OperationSchemaModel(
            id="gmail.messages.forward",
            display_name="Forward Message",
            description="Forwards a message to a new recipient.",
            required_parameters=[
                ParameterSchemaModel(name="message_id", display_name="Message ID", type="string", required=True, description="Message ID to forward"),
                ParameterSchemaModel(name="to", display_name="Forward Recipient", type="string", required=True, description="Target recipient email"),
            ],
            optional_parameters=[
                ParameterSchemaModel(name="body", display_name="Forward Note", type="text", required=False, description="Additional note to prepend"),
            ],
            default_values={"message_id": "{{step_1.id}}", "to": "colleague@example.com", "body": "FYI - see forwarded message below."},
        )

        delete_schema = OperationSchemaModel(
            id="gmail.messages.delete",
            display_name="Delete Message",
            description="Moves a message to trash or permanently deletes it.",
            required_parameters=[
                ParameterSchemaModel(name="message_id", display_name="Message ID", type="string", required=True, description="Message ID to delete"),
            ],
            optional_parameters=[],
            default_values={"message_id": "{{step_1.id}}"},
        )

        mark_read_schema = OperationSchemaModel(
            id="gmail.messages.mark_read",
            display_name="Mark as Read",
            description="Removes UNREAD label from a message.",
            required_parameters=[
                ParameterSchemaModel(name="message_id", display_name="Message ID", type="string", required=True, description="Message ID to mark as read"),
            ],
            optional_parameters=[],
            default_values={"message_id": "{{step_1.id}}"},
        )

        mark_unread_schema = OperationSchemaModel(
            id="gmail.messages.mark_unread",
            display_name="Mark as Unread",
            description="Adds UNREAD label to a message.",
            required_parameters=[
                ParameterSchemaModel(name="message_id", display_name="Message ID", type="string", required=True, description="Message ID to mark as unread"),
            ],
            optional_parameters=[],
            default_values={"message_id": "{{step_1.id}}"},
        )

        labels_list_schema = OperationSchemaModel(
            id="gmail.labels.list",
            display_name="List Labels",
            description="Lists all user and system labels in Gmail account.",
            required_parameters=[],
            optional_parameters=[],
            default_values={},
        )

        labels_modify_schema = OperationSchemaModel(
            id="gmail.labels.modify",
            display_name="Modify Message Labels",
            description="Adds or removes labels from a message.",
            required_parameters=[
                ParameterSchemaModel(name="message_id", display_name="Message ID", type="string", required=True, description="Message ID to modify"),
            ],
            optional_parameters=[
                ParameterSchemaModel(name="add_labels", display_name="Add Label IDs", type="array", required=False, description="List of label IDs to add"),
                ParameterSchemaModel(name="remove_labels", display_name="Remove Label IDs", type="array", required=False, description="List of label IDs to remove"),
            ],
            default_values={"message_id": "{{step_1.id}}", "add_labels": ["STARRED"]},
        )

        draft_create_schema = OperationSchemaModel(
            id="gmail.drafts.create",
            display_name="Create Draft",
            description="Creates a new draft message in Gmail.",
            required_parameters=[
                ParameterSchemaModel(name="to", display_name="To Recipient", type="string", required=True, description="Recipient email address"),
                ParameterSchemaModel(name="subject", display_name="Subject", type="string", required=True, description="Draft subject"),
                ParameterSchemaModel(name="body", display_name="Body Content", type="text", required=True, description="Draft body text"),
            ],
            optional_parameters=[],
            default_values={"to": "draft@example.com", "subject": "Draft Subject", "body": "Draft content"},
        )

        draft_send_schema = OperationSchemaModel(
            id="gmail.drafts.send",
            display_name="Send Draft",
            description="Sends an existing draft by draft ID.",
            required_parameters=[
                ParameterSchemaModel(name="draft_id", display_name="Draft ID", type="string", required=True, description="Draft ID to send"),
            ],
            optional_parameters=[],
            default_values={"draft_id": "{{step_1.draft_id}}"},
        )

        attachment_schema = OperationSchemaModel(
            id="gmail.attachments.download",
            display_name="Download Attachment",
            description="Downloads an attachment payload from a message.",
            required_parameters=[
                ParameterSchemaModel(name="message_id", display_name="Message ID", type="string", required=True, description="Message ID containing attachment"),
                ParameterSchemaModel(name="attachment_id", display_name="Attachment ID", type="string", required=True, description="Attachment unique ID"),
            ],
            optional_parameters=[],
            default_values={"message_id": "{{step_1.id}}", "attachment_id": "{{step_1.attachment_id}}"},
        )

        all_ops = [
            "gmail.messages.send",
            "gmail.messages.list",
            "gmail.messages.get",
            "gmail.messages.search",
            "gmail.messages.reply",
            "gmail.messages.forward",
            "gmail.messages.delete",
            "gmail.messages.mark_read",
            "gmail.messages.mark_unread",
            "gmail.labels.list",
            "gmail.labels.modify",
            "gmail.drafts.create",
            "gmail.drafts.send",
            "gmail.attachments.download",
        ]

        op_schemas = {
            "gmail.messages.send": send_schema,
            "gmail.messages.list": list_schema,
            "gmail.messages.get": get_schema,
            "gmail.messages.search": search_schema,
            "gmail.messages.reply": reply_schema,
            "gmail.messages.forward": forward_schema,
            "gmail.messages.delete": delete_schema,
            "gmail.messages.mark_read": mark_read_schema,
            "gmail.messages.mark_unread": mark_unread_schema,
            "gmail.labels.list": labels_list_schema,
            "gmail.labels.modify": labels_modify_schema,
            "gmail.drafts.create": draft_create_schema,
            "gmail.drafts.send": draft_send_schema,
            "gmail.attachments.download": attachment_schema,
        }

        return ConnectorMetadataModel(
            provider="Gmail",
            display_name="Google Gmail",
            icon="gmail",
            auth_type="OAuth2",
            supported_operations=all_ops,
            operation_schemas=op_schemas,
            categories=["Communication", "Email"],
            version="2.0.0",
            documentation_url="https://developers.google.com/gmail/api",
        )

    def _build_mime_message(
        self,
        to_addr: str,
        subject: str,
        body: str,
        from_addr: Optional[str] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        html_body: Optional[str] = None,
    ) -> str:
        """Constructs an RFC-2822 MIME EmailMessage with optional attachments and HTML body, encodes to Base64URL string."""
        from app.services.gmail_attachment_service import gmail_attachment_service
        return gmail_attachment_service.build_mime_with_attachments(
            to_addr=to_addr,
            subject=subject,
            body=body,
            from_addr=from_addr,
            attachments=attachments,
            cc=cc,
            bcc=bcc,
            html_body=html_body,
        )

    async def _send_request_with_401_retry(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        headers: Dict[str, str],
        tenant_id: str,
        **kwargs
    ) -> httpx.Response:
        from app.oauth.manager import oauth_manager
        res = await client.request(method, url, headers=headers, **kwargs)
        if res.status_code == 401:
            logger.info("[AUTH-11] Provider returned HTTP 401 — attempting at most ONE OAuth refresh & retry...")
            refreshed = await oauth_manager.refresh_access_token(tenant_id, "Google")
            if refreshed and refreshed.access_token:
                headers["Authorization"] = f"Bearer {refreshed.access_token}"
                res = await client.request(method, url, headers=headers, **kwargs)
        return res

    async def execute_operation(
        self, request: ConnectorRequestModel, credentials: Optional[ConnectorCredentialModel] = None
    ) -> ConnectorResponseModel:
        from app.oauth.manager import oauth_manager
        start_time = time.perf_counter()
        tenant_id = request.tenant_id or "usr_1"

        # ── Phase 6: Verify SecretManager Account ─────────────────────────────
        cred_record = credentials
        account_label = getattr(cred_record, "account_label", None) if cred_record else None

        if not cred_record or not cred_record.access_token:
            cred_record = await secret_manager.get_secret(tenant_id, "Google")
            if not cred_record:
                cred_record = await secret_manager.get_secret(tenant_id, "Gmail")
            if cred_record and hasattr(cred_record, "account_label"):
                account_label = cred_record.account_label

        logger.info(f"[AUTH-11] OAuth account: tenant_id={tenant_id}")
        logger.info(f"[AUTH-11] SecretManager account: account_label={account_label or 'usr_1'}")

        access_token = cred_record.access_token if cred_record else None

        # ── Phase 2: Token Lifetime Check & Refresh ────────────────────────────
        if cred_record:
            exp_at = cred_record.token_expires_at or 0.0
            now = time.time()
            rem_lifetime = int(exp_at - now) if exp_at > 0 else 3600
            logger.info(
                f"[AUTH-11] Token check: provider=Google tenant_id={tenant_id} "
                f"expires_at={exp_at} remaining_lifetime={rem_lifetime}s"
            )

            if exp_at > 0 and rem_lifetime <= 60:
                logger.info("[AUTH-11] Token expiring or expired — attempting OAuth refresh...")
                refreshed = await oauth_manager.refresh_access_token(tenant_id, "Google")
                if refreshed and refreshed.access_token:
                    access_token = refreshed.access_token
                    logger.info("[AUTH-11] OAuth token refresh SUCCESS")
                else:
                    logger.warning("[AUTH-11] OAuth token refresh returned None — proceeding with existing access token")
                    access_token = cred_record.access_token

        if not access_token:
            conns = await oauth_manager.get_user_connections(tenant_id)
            g_conn = next((c for c in conns if c.provider.lower() in ("gmail", "google")), None)
            if g_conn:
                access_token = g_conn.access_token

        if not access_token:
            logger.error("[AUTH-11] No Google OAuth token available in SecretManager or session.")
            return ConnectorResponseModel(
                success=False,
                operation_id=request.operation_id,
                status_code=401,
                error_message="No valid Google OAuth token available for Gmail API execution.",
                latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            )

        logger.info(f"[AUTH-11] Runtime credential: provider=Google tenant_id={tenant_id}")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "AgentFlow-AI/2.0 Production-Engine",
        }

        params = request.parameters or {}
        op_id = request.operation_id

        async with httpx.AsyncClient(timeout=request.timeout_seconds or 20.0) as client:
            # ── Phase 1, 6 & 7: Verify Gmail Profile (users/me/profile) ───────
            profile_email = ""
            try:
                profile_res = await self._send_request_with_401_retry(
                    client, "GET", "https://gmail.googleapis.com/gmail/v1/users/me/profile", headers, tenant_id
                )
                if profile_res.status_code == 200:
                    p_data = profile_res.json()
                    profile_email = p_data.get("emailAddress", "")
                    logger.info(
                        f"[AUTH-11] Gmail profile: emailAddress={profile_email} "
                        f"messagesTotal={p_data.get('messagesTotal')} threadsTotal={p_data.get('threadsTotal')} HTTP_status=200"
                    )
                else:
                    logger.warning(f"[AUTH-11] Gmail profile check returned HTTP {profile_res.status_code}: {profile_res.text[:200]}")
                    return ConnectorResponseModel(
                        success=False,
                        operation_id=op_id,
                        status_code=profile_res.status_code,
                        error_message=f"Google OAuth token verification failed: HTTP {profile_res.status_code} {profile_res.text}",
                        latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
                    )
            except Exception as exc:
                logger.warning(f"[AUTH-11] Profile check exception: {exc}")
                return ConnectorResponseModel(
                    success=False,
                    operation_id=op_id,
                    status_code=401,
                    error_message=f"Google OAuth profile verification failed: {exc}",
                    latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
                )

            # Account mismatch check (Phase 6 & 7)
            if account_label and profile_email and account_label.lower() != profile_email.lower():
                logger.error(f"[AUTH-11] WRONG TOKEN LOADED: SecretManager account={account_label} vs Gmail profile={profile_email}")
                return ConnectorResponseModel(
                    success=False,
                    operation_id=op_id,
                    status_code=401,
                    error_message=f"WRONG TOKEN LOADED: SecretManager account ({account_label}) does not match profile ({profile_email}).",
                    latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
                )

            # ── Operation: gmail.messages.send (Phase 3 & 4) ─────────────────
            if op_id in ["gmail.messages.send", "gmail.send", "send_email"]:
                url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
                to_addr = str(params.get("to") or params.get("recipient") or "").strip()
                subject = str(params.get("subject") or "AgentFlow AI Message").strip()
                body_text = str(params.get("body") or params.get("message") or "").strip()
                cc_addr = params.get("cc")
                bcc_addr = params.get("bcc")
                from_addr = params.get("from") or profile_email or account_label or ""

                if not to_addr or to_addr in ("{{user.email}}", "me") or to_addr.startswith("{{"):
                    to_addr = from_addr or profile_email or account_label or "aswinkumaar07@gmail.com"

                # ── Sprint AUTH-13 Task 5: Runtime Verification ─────────────────
                logger.info("[AUTH-13] Runtime Gmail Parameters")
                logger.info({
                    "to": to_addr,
                    "subject": subject,
                    "body": body_text,
                })

                # ── Sprint AUTH-13 Task 6: Adapter Header Protection ───────────
                if "\n" in subject or "\r" in subject:
                    raise ValueError(f"[AUTH-13] Invalid carriage return or linefeed in subject: {repr(subject)}")
                if "\n" in to_addr or "\r" in to_addr:
                    raise ValueError(f"[AUTH-13] Invalid carriage return or linefeed in recipient: {repr(to_addr)}")

                # Build MIME message (Phase 3)
                raw_encoded = self._build_mime_message(
                    to_addr=to_addr,
                    subject=subject,
                    body=body_text,
                    from_addr=from_addr,
                    cc=cc_addr,
                    bcc=bcc_addr,
                    attachments=params.get("attachments"),
                    html_body=params.get("html_body"),
                )

                logger.info(f"[AUTH-11] MIME message: To={to_addr} From={from_addr} Subject={subject} BodySnippet={body_text[:60]}")
                logger.info(f"[AUTH-11] Gmail send request: endpoint={url} recipient={to_addr} subject={subject} payload_size={len(raw_encoded)}")

                payload = {"raw": raw_encoded}
                response = await self._send_request_with_401_retry(client, "POST", url, headers, tenant_id, json=payload)
                latency = round((time.perf_counter() - start_time) * 1000.0, 2)

                try:
                    res_body = response.json()
                except Exception:
                    res_body = {"raw_text": response.text}

                msg_id = res_body.get("id")
                thread_id = res_body.get("threadId")

                logger.info(f"[AUTH-11] Gmail response: status_code={response.status_code} messageId={msg_id} threadId={thread_id}")

                if response.is_success:
                    logger.info(f"[AUTH-11] Message ID: {msg_id}")
                    logger.info(f"[AUTH-11] Delivery SUCCESS: recipient={to_addr} message_id={msg_id}")
                    return ConnectorResponseModel(
                        success=True,
                        operation_id=op_id,
                        status_code=response.status_code,
                        data={
                            "messageId": msg_id,
                            "threadId": thread_id,
                            "labelIds": res_body.get("labelIds", []),
                            "historyId": res_body.get("historyId"),
                            "HTTP_status": response.status_code,
                            "latency_ms": latency,
                            "body": res_body,
                        },
                        latency_ms=latency,
                    )
                else:
                    error_msg = f"Google Gmail API returned error HTTP {response.status_code}: {response.text}"
                    logger.error(f"[AUTH-11] Gmail send FAILED: {error_msg}")
                    return ConnectorResponseModel(
                        success=False,
                        operation_id=op_id,
                        status_code=response.status_code,
                        error_message=error_msg,
                        data={
                            "HTTP_status": response.status_code,
                            "google_error": res_body,
                            "latency_ms": latency,
                        },
                        latency_ms=latency,
                    )

            # ----------------------------------------------------
            # Operation: gmail.messages.list
            # ----------------------------------------------------
            elif op_id in ["gmail.messages.list", "gmail.list", "list_messages"]:
                url = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
                query_params = {
                    "q": params.get("q", "is:unread"),
                    "maxResults": params.get("max_results", 10),
                }
                try:
                    response = await self._send_request_with_401_retry(client, "GET", url, headers, tenant_id, params=query_params)
                    latency = round((time.perf_counter() - start_time) * 1000.0, 2)
                    res_headers = dict(response.headers)

                    try:
                        res_body = response.json()
                    except Exception:
                        res_body = {"raw_text": response.text}

                    if response.is_success:
                        return ConnectorResponseModel(
                            success=True,
                            operation_id=op_id,
                            status_code=response.status_code,
                            data={
                                "messages": res_body.get("messages", []),
                                "nextPageToken": res_body.get("nextPageToken"),
                                "resultSizeEstimate": res_body.get("resultSizeEstimate", 0),
                                "HTTP_status": response.status_code,
                                "latency_ms": latency,
                                "headers": res_headers,
                                "body": res_body,
                            },
                            latency_ms=latency,
                        )
                    else:
                        return ConnectorResponseModel(
                            success=False,
                            operation_id=op_id,
                            status_code=response.status_code,
                            error_message=f"Gmail API list messages failed HTTP {response.status_code}: {response.text[:300]}",
                            data={"google_error": res_body, "HTTP_status": response.status_code},
                            latency_ms=latency,
                        )

                except Exception as exc:
                    latency = round((time.perf_counter() - start_time) * 1000.0, 2)
                    return ConnectorResponseModel(
                        success=False,
                        operation_id=op_id,
                        status_code=500,
                        error_message=f"Gmail list messages exception: {str(exc)}",
                        data={"error": str(exc)},
                        latency_ms=latency,
                    )

            # ----------------------------------------------------
            # Operation: gmail.messages.get
            # ----------------------------------------------------
            elif op_id == "gmail.messages.get":
                msg_id = params.get("message_id") or ""
                url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}"
                try:
                    response = await self._send_request_with_401_retry(client, "GET", url, headers, tenant_id)
                    latency = round((time.perf_counter() - start_time) * 1000.0, 2)
                    res_headers = dict(response.headers)

                    try:
                        res_body = response.json()
                    except Exception:
                        res_body = {"raw_text": response.text}

                    if response.is_success:
                        return ConnectorResponseModel(
                            success=True,
                            operation_id=op_id,
                            status_code=response.status_code,
                            data={
                                "messageId": res_body.get("id"),
                                "threadId": res_body.get("threadId"),
                                "snippet": res_body.get("snippet"),
                                "payload": res_body.get("payload"),
                                "HTTP_status": response.status_code,
                                "latency_ms": latency,
                                "headers": res_headers,
                                "body": res_body,
                            },
                            latency_ms=latency,
                        )
                    else:
                        return ConnectorResponseModel(
                            success=False,
                            operation_id=op_id,
                            status_code=response.status_code,
                            error_message=f"Gmail API get message details failed HTTP {response.status_code}: {response.text[:300]}",
                            data={"google_error": res_body, "HTTP_status": response.status_code},
                            latency_ms=latency,
                        )

                except Exception as exc:
                    latency = round((time.perf_counter() - start_time) * 1000.0, 2)
                    return ConnectorResponseModel(
                        success=False,
                        operation_id=op_id,
                        status_code=500,
                        error_message=f"Gmail get message exception: {str(exc)}",
                        data={"error": str(exc)},
                        latency_ms=latency,
                    )

            # ----------------------------------------------------
            # Operation: gmail.messages.search
            # ----------------------------------------------------
            elif op_id in ["gmail.messages.search", "gmail.search"]:
                url = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
                q_val = str(params.get("query") or params.get("q") or "is:unread").strip()
                max_res = params.get("max_results", 10)
                try:
                    response = await client.get(url, headers=headers, params={"q": q_val, "maxResults": max_res})
                    latency = round((time.perf_counter() - start_time) * 1000.0, 2)
                    res_body = response.json() if response.is_success else {"error": response.text}
                    return ConnectorResponseModel(
                        success=response.is_success,
                        operation_id=op_id,
                        status_code=response.status_code,
                        data={"messages": res_body.get("messages", []), "resultSizeEstimate": res_body.get("resultSizeEstimate", 0), "body": res_body},
                        latency_ms=latency,
                    )
                except Exception as exc:
                    return ConnectorResponseModel(success=False, operation_id=op_id, status_code=500, error_message=str(exc))

            # ----------------------------------------------------
            # Operation: gmail.messages.reply
            # ----------------------------------------------------
            elif op_id in ["gmail.messages.reply", "gmail.reply"]:
                msg_id = str(params.get("message_id") or params.get("id") or "").strip()
                thread_id = str(params.get("thread_id") or params.get("threadId") or msg_id).strip()
                to_addr = str(params.get("to") or params.get("recipient") or "").strip()
                subject = str(params.get("subject") or "").strip()
                body_text = str(params.get("body") or params.get("message") or "").strip()

                if (not to_addr or to_addr.startswith("{{")) and msg_id:
                    try:
                        orig_res = await client.get(
                            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
                            headers=headers,
                            params={"format": "metadata", "metadataHeaders": ["From", "Reply-To", "Subject"]}
                        )
                        if orig_res.is_success:
                            orig_json = orig_res.json()
                            orig_headers = orig_json.get("payload", {}).get("headers", [])
                            from_h = next((h.get("value") for h in orig_headers if h.get("name", "").lower() in ("reply-to", "from")), "")
                            subj_h = next((h.get("value") for h in orig_headers if h.get("name", "").lower() == "subject"), "")
                            if from_h:
                                import email.utils
                                _, parsed_email = email.utils.parseaddr(from_h)
                                to_addr = parsed_email or from_h
                            if subj_h and not subject:
                                subject = f"Re: {subj_h}" if not subj_h.lower().startswith("re:") else subj_h
                    except Exception as orig_exc:
                        logger.warning(f"Failed fetching original message {msg_id} metadata: {orig_exc}")

                if not to_addr or to_addr in ("{{user.email}}", "me") or to_addr.startswith("{{"):
                    to_addr = profile_email or account_label or "aswinkumaar07@gmail.com"

                if not subject:
                    subject = "Re: Message"
                elif not subject.lower().startswith("re:"):
                    subject = f"Re: {subject}"

                url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
                raw_encoded = self._build_mime_message(to_addr=to_addr, subject=subject, body=body_text, from_addr=profile_email)
                payload = {"raw": raw_encoded}
                if thread_id:
                    payload["threadId"] = thread_id
                try:
                    response = await client.post(url, headers=headers, json=payload)
                    latency = round((time.perf_counter() - start_time) * 1000.0, 2)
                    res_body = response.json() if response.is_success else {"error": response.text}
                    return ConnectorResponseModel(
                        success=response.is_success,
                        operation_id=op_id,
                        status_code=response.status_code,
                        data={"messageId": res_body.get("id"), "threadId": res_body.get("threadId"), "body": res_body},
                        latency_ms=latency,
                    )
                except Exception as exc:
                    return ConnectorResponseModel(success=False, operation_id=op_id, status_code=500, error_message=str(exc))

            # ----------------------------------------------------
            # Operation: gmail.messages.forward
            # ----------------------------------------------------
            elif op_id in ["gmail.messages.forward", "gmail.forward"]:
                to_addr = str(params.get("to") or "").strip()
                subject = str(params.get("subject") or "Fwd: Message").strip()
                body_text = str(params.get("body") or "").strip()
                if not subject.startswith("Fwd:"):
                    subject = f"Fwd: {subject}"
                url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
                raw_encoded = self._build_mime_message(to_addr=to_addr, subject=subject, body=body_text, from_addr=profile_email)
                try:
                    response = await client.post(url, headers=headers, json={"raw": raw_encoded})
                    latency = round((time.perf_counter() - start_time) * 1000.0, 2)
                    res_body = response.json() if response.is_success else {"error": response.text}
                    return ConnectorResponseModel(
                        success=response.is_success,
                        operation_id=op_id,
                        status_code=response.status_code,
                        data={"messageId": res_body.get("id"), "threadId": res_body.get("threadId"), "body": res_body},
                        latency_ms=latency,
                    )
                except Exception as exc:
                    return ConnectorResponseModel(success=False, operation_id=op_id, status_code=500, error_message=str(exc))

            # ----------------------------------------------------
            # Operation: gmail.messages.delete
            # ----------------------------------------------------
            elif op_id in ["gmail.messages.delete", "gmail.delete"]:
                msg_id = str(params.get("message_id") or params.get("id") or "").strip()
                url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}/trash"
                try:
                    response = await client.post(url, headers=headers)
                    latency = round((time.perf_counter() - start_time) * 1000.0, 2)
                    res_body = response.json() if response.is_success else {"error": response.text}
                    return ConnectorResponseModel(
                        success=response.is_success,
                        operation_id=op_id,
                        status_code=response.status_code,
                        data={"messageId": msg_id, "status": "TRASHED", "body": res_body},
                        latency_ms=latency,
                    )
                except Exception as exc:
                    return ConnectorResponseModel(success=False, operation_id=op_id, status_code=500, error_message=str(exc))

            # ----------------------------------------------------
            # Operation: gmail.messages.mark_read
            # ----------------------------------------------------
            elif op_id in ["gmail.messages.mark_read", "gmail.mark_read"]:
                msg_id = str(params.get("message_id") or params.get("id") or "").strip()
                url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}/modify"
                try:
                    response = await client.post(url, headers=headers, json={"removeLabelIds": ["UNREAD"]})
                    latency = round((time.perf_counter() - start_time) * 1000.0, 2)
                    res_body = response.json() if response.is_success else {"error": response.text}
                    return ConnectorResponseModel(
                        success=response.is_success,
                        operation_id=op_id,
                        status_code=response.status_code,
                        data={"messageId": msg_id, "status": "READ", "body": res_body},
                        latency_ms=latency,
                    )
                except Exception as exc:
                    return ConnectorResponseModel(success=False, operation_id=op_id, status_code=500, error_message=str(exc))

            # ----------------------------------------------------
            # Operation: gmail.messages.mark_unread
            # ----------------------------------------------------
            elif op_id in ["gmail.messages.mark_unread", "gmail.mark_unread"]:
                msg_id = str(params.get("message_id") or params.get("id") or "").strip()
                url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}/modify"
                try:
                    response = await client.post(url, headers=headers, json={"addLabelIds": ["UNREAD"]})
                    latency = round((time.perf_counter() - start_time) * 1000.0, 2)
                    res_body = response.json() if response.is_success else {"error": response.text}
                    return ConnectorResponseModel(
                        success=response.is_success,
                        operation_id=op_id,
                        status_code=response.status_code,
                        data={"messageId": msg_id, "status": "UNREAD", "body": res_body},
                        latency_ms=latency,
                    )
                except Exception as exc:
                    return ConnectorResponseModel(success=False, operation_id=op_id, status_code=500, error_message=str(exc))

            # ----------------------------------------------------
            # Operation: gmail.labels.list
            # ----------------------------------------------------
            elif op_id in ["gmail.labels.list", "gmail.labels"]:
                url = "https://gmail.googleapis.com/gmail/v1/users/me/labels"
                try:
                    response = await client.get(url, headers=headers)
                    latency = round((time.perf_counter() - start_time) * 1000.0, 2)
                    res_body = response.json() if response.is_success else {"error": response.text}
                    return ConnectorResponseModel(
                        success=response.is_success,
                        operation_id=op_id,
                        status_code=response.status_code,
                        data={"labels": res_body.get("labels", []), "body": res_body},
                        latency_ms=latency,
                    )
                except Exception as exc:
                    return ConnectorResponseModel(success=False, operation_id=op_id, status_code=500, error_message=str(exc))

            # ----------------------------------------------------
            # Operation: gmail.labels.modify
            # ----------------------------------------------------
            elif op_id in ["gmail.labels.modify", "gmail.modify_labels"]:
                msg_id = str(params.get("message_id") or params.get("id") or "").strip()
                url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}/modify"
                add_lbls = params.get("add_labels") or []
                rem_lbls = params.get("remove_labels") or []
                try:
                    response = await client.post(url, headers=headers, json={"addLabelIds": add_lbls, "removeLabelIds": rem_lbls})
                    latency = round((time.perf_counter() - start_time) * 1000.0, 2)
                    res_body = response.json() if response.is_success else {"error": response.text}
                    return ConnectorResponseModel(
                        success=response.is_success,
                        operation_id=op_id,
                        status_code=response.status_code,
                        data={"messageId": msg_id, "labelIds": res_body.get("labelIds", []), "body": res_body},
                        latency_ms=latency,
                    )
                except Exception as exc:
                    return ConnectorResponseModel(success=False, operation_id=op_id, status_code=500, error_message=str(exc))

            # ----------------------------------------------------
            # Operation: gmail.drafts.create
            # ----------------------------------------------------
            elif op_id in ["gmail.drafts.create", "gmail.create_draft"]:
                to_addr = str(params.get("to") or "").strip()
                subject = str(params.get("subject") or "Draft Subject").strip()
                body_text = str(params.get("body") or "").strip()
                url = "https://gmail.googleapis.com/gmail/v1/users/me/drafts"
                raw_encoded = self._build_mime_message(to_addr=to_addr, subject=subject, body=body_text, from_addr=profile_email)
                try:
                    response = await client.post(url, headers=headers, json={"message": {"raw": raw_encoded}})
                    latency = round((time.perf_counter() - start_time) * 1000.0, 2)
                    res_body = response.json() if response.is_success else {"error": response.text}
                    return ConnectorResponseModel(
                        success=response.is_success,
                        operation_id=op_id,
                        status_code=response.status_code,
                        data={"draftId": res_body.get("id"), "message": res_body.get("message"), "body": res_body},
                        latency_ms=latency,
                    )
                except Exception as exc:
                    return ConnectorResponseModel(success=False, operation_id=op_id, status_code=500, error_message=str(exc))

            # ----------------------------------------------------
            # Operation: gmail.drafts.send
            # ----------------------------------------------------
            elif op_id in ["gmail.drafts.send", "gmail.send_draft"]:
                draft_id = str(params.get("draft_id") or params.get("id") or "").strip()
                url = "https://gmail.googleapis.com/gmail/v1/users/me/drafts/send"
                try:
                    response = await client.post(url, headers=headers, json={"id": draft_id})
                    latency = round((time.perf_counter() - start_time) * 1000.0, 2)
                    res_body = response.json() if response.is_success else {"error": response.text}
                    return ConnectorResponseModel(
                        success=response.is_success,
                        operation_id=op_id,
                        status_code=response.status_code,
                        data={"messageId": res_body.get("id"), "threadId": res_body.get("threadId"), "body": res_body},
                        latency_ms=latency,
                    )
                except Exception as exc:
                    return ConnectorResponseModel(success=False, operation_id=op_id, status_code=500, error_message=str(exc))

            # ----------------------------------------------------
            # Operation: gmail.attachments.download
            # ----------------------------------------------------
            elif op_id in ["gmail.attachments.download", "gmail.download_attachment"]:
                msg_id = str(params.get("message_id") or "").strip()
                att_id = str(params.get("attachment_id") or params.get("id") or "").strip()
                filename = str(params.get("filename") or f"attachment_{att_id}.bin").strip()
                url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}/attachments/{att_id}"
                try:
                    response = await client.get(url, headers=headers)
                    latency = round((time.perf_counter() - start_time) * 1000.0, 2)
                    res_body = response.json() if response.is_success else {"error": response.text}
                    raw_b64 = res_body.get("data", "")
                    from app.services.gmail_attachment_service import gmail_attachment_service
                    save_meta = {}
                    if raw_b64 and params.get("save_to_disk", True):
                        save_meta = gmail_attachment_service.save_attachment_payload(
                            attachment_id=att_id,
                            filename=filename,
                            base64_data=raw_b64
                        )
                    return ConnectorResponseModel(
                        success=response.is_success,
                        operation_id=op_id,
                        status_code=response.status_code,
                        data={
                            "attachmentId": att_id,
                            "filename": filename,
                            "mimeType": save_meta.get("mime_type") or gmail_attachment_service.get_mime_type(filename),
                            "size": res_body.get("size", 0),
                            "savedPath": save_meta.get("saved_path"),
                            "data": raw_b64,
                            "body": res_body
                        },
                        latency_ms=latency,
                    )
                except Exception as exc:
                    return ConnectorResponseModel(success=False, operation_id=op_id, status_code=500, error_message=str(exc))

            # Fallback for unhandled operation
            latency = round((time.perf_counter() - start_time) * 1000.0, 2)
            return ConnectorResponseModel(
                success=False,
                operation_id=op_id,
                status_code=400,
                error_message=f"Unsupported Gmail operation: '{op_id}'",
                data={"error": f"Unsupported operation '{op_id}'"},
                latency_ms=latency,
            )

    execute = execute_operation
