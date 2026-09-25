import logging
import time
from typing import Optional
from app.connectors.cache.connection_pool import connection_pool
from app.connectors.interfaces import BaseProviderAdapter
from app.connectors.models import (
    ConnectorCredentialModel,
    ConnectorMetadataModel,
    ConnectorRequestModel,
    ConnectorResponseModel,
)

logger = logging.getLogger("agentflow.connectors.providers.slack")


class SlackAdapter(BaseProviderAdapter):
    """Production Provider Adapter for Slack Web API (Sprint AI-22 Real Execution Fix)."""

    @property
    def provider_name(self) -> str:
        return "Slack"

    def get_metadata(self) -> ConnectorMetadataModel:
        return ConnectorMetadataModel(
            provider="Slack",
            version="v1",
            supported_operations=["slack.chat.postMessage", "slack.conversations.list"],
            auth_types=["Bearer", "OAuth2"],
        )

    async def _resolve_channel_id(self, channel_input: str, headers: dict, timeout: float) -> str:
        """
        Resolves channel names like '#all-agentflow-ai' or 'all-agentflow-ai' to real Slack Channel IDs (e.g. 'C08...').
        If input is already a Channel ID format (starts with 'C', 'D', 'G' and 8+ chars), returns it directly.
        Includes auth.test diagnostic verification and cursor pagination.
        Raises ValueError if channel resolution fails or channel is not found.
        """
        ch = str(channel_input or "").strip()
        clean_name = ch.lstrip("#").strip().lower()

        if not clean_name:
            raise ValueError("Slack channel input is empty.")

        if len(ch) >= 8 and ch[0] in ["C", "D", "G"] and " " not in ch:
            return ch

        # 1. Diagnostic auth.test (Safe logging only, NO tokens)
        try:
            auth_res = await connection_pool.request(
                "POST",
                "https://slack.com/api/auth.test",
                headers=headers,
                timeout=timeout
            )
            if isinstance(auth_res, dict):
                logger.info(
                    f"[SLACK_AUTH_TEST] ok={auth_res.get('ok')} "
                    f"team_id={auth_res.get('team_id')} team={auth_res.get('team')} "
                    f"user_id={auth_res.get('user_id')} user={auth_res.get('user')} "
                    f"bot_id={auth_res.get('bot_id')} error={auth_res.get('error')}"
                )
        except Exception as auth_exc:
            logger.warning(f"[SLACK_AUTH_TEST_FAILED] Error calling auth.test: {auth_exc}")

        # 2. Paginated conversations.list (types=public_channel, limit=200)
        url = "https://slack.com/api/conversations.list"
        cursor = ""
        page_num = 1
        found_id = None

        while True:
            params = {"types": "public_channel", "limit": 200}
            if cursor:
                params["cursor"] = cursor

            try:
                res = await connection_pool.request(
                    "GET",
                    url,
                    headers=headers,
                    params=params,
                    timeout=timeout
                )
                if isinstance(res, dict):
                    if not res.get("ok"):
                        slack_err = res.get("error") or "unknown_error"
                        logger.error(f"[SLACK_CHANNEL_RESOLVE_FAILED] Page {page_num} conversations.list error: {slack_err}")
                        raise ValueError(f"Slack channel resolution failed: {slack_err}")

                    channels = res.get("channels", [])
                    logger.info(f"[SLACK_CHANNELS_PAGE] Page {page_num} returned {len(channels)} public channels.")

                    for item in channels:
                        c_id = item.get("id")
                        c_name = item.get("name", "")
                        c_memb = item.get("is_member", False)
                        c_arch = item.get("is_archived", False)

                        if c_name.lower() == clean_name:
                            found_id = c_id
                            logger.info(
                                f"[SLACK_CHANNEL_MATCH_FOUND] target='{clean_name}' -> "
                                f"id={c_id} name=#{c_name} is_member={c_memb} is_archived={c_arch}"
                            )
                            break

                    if found_id:
                        break

                    next_cursor = res.get("response_metadata", {}).get("next_cursor", "").strip()
                    if not next_cursor:
                        break
                    cursor = next_cursor
                    page_num += 1
                else:
                    raise ValueError("Slack channel resolution failed: Unexpected API response format.")
            except ValueError:
                raise
            except Exception as exc:
                logger.error(f"[SLACK_CHANNEL_RESOLVE_EXCEPTION] Exception during channel resolution: {exc}")
                raise ValueError(f"Slack channel resolution failed: {exc}")

        if found_id:
            return found_id
        else:
            logger.warning(f"[SLACK_CHANNEL_NOT_FOUND] Target channel '{clean_name}' not found across pages.")
            raise ValueError(f"Slack channel not found: {clean_name}")

    async def execute_operation(
        self, request: ConnectorRequestModel, credentials: Optional[ConnectorCredentialModel] = None
    ) -> ConnectorResponseModel:
        from app.oauth.manager import oauth_manager

        start_time = time.perf_counter()
        headers = {"Content-Type": "application/json; charset=utf-8"}
        token = ""

        if credentials and credentials.access_token:
            token = credentials.access_token

        if not token:
            conns = await oauth_manager.get_user_connections(request.tenant_id or "usr_1")
            s_conn = next((c for c in conns if "slack" in c.provider.lower()), None)
            if s_conn and s_conn.access_token:
                token = s_conn.access_token

        if not token:
            from app.connectors.security.secret_manager import secret_manager
            sec = await secret_manager.get_secret(request.tenant_id or "usr_1", "Slack")
            if not sec:
                sec = await secret_manager.get_secret("usr_1", "Slack")
            if sec and sec.access_token:
                token = sec.access_token

        if not token:
            import os
            if os.environ.get("SLACK_BOT_TOKEN"):
                token = os.environ.get("SLACK_BOT_TOKEN")

        if not token:
            logger.warning(f"[SLACK_EXECUTE_OPERATION] Tenant [{request.tenant_id}] has no connected Slack OAuth account. Missing credential.")
            latency = (time.perf_counter() - start_time) * 1000.0
            return ConnectorResponseModel(
                success=False,
                operation_id=request.operation_id,
                status_code=401,
                data={"ok": False, "error": "not_authed"},
                error_message=f"Slack authentication failed: Tenant [{request.tenant_id}] is not connected (Missing access token).",
                latency_ms=round(latency, 2),
            )


        headers["Authorization"] = f"Bearer {token}"
        params = dict(request.body or request.parameters or {})

        op_id_clean = request.operation_id.lower()
        logger.info(f"[SLACK_EXECUTE_OPERATION] Executing '{request.operation_id}' for tenant '{request.tenant_id}'")

        # Channel resolution for chat.postMessage
        if op_id_clean in ["slack.chat.postmessage", "slack.chat.postMessage", "default"]:
            raw_ch = params.get("channel") or "#general"
            try:
                resolved_ch = await self._resolve_channel_id(raw_ch, headers, request.timeout_seconds)
                params["channel"] = resolved_ch
            except ValueError as ve:
                latency = (time.perf_counter() - start_time) * 1000.0
                err_msg = str(ve)
                return ConnectorResponseModel(
                    success=False,
                    operation_id=request.operation_id,
                    status_code=400,
                    error_message=err_msg,
                    data={"ok": False, "error": "channel_not_found" if "not found" in err_msg.lower() else "resolution_failed"},
                    latency_ms=round(latency, 2),
                )

        url = "https://slack.com/api/chat.postMessage"
        if op_id_clean == "slack.conversations.list":
            url = "https://slack.com/api/conversations.list"

        try:
            res = await connection_pool.request(
                "POST" if op_id_clean != "slack.conversations.list" else "GET",
                url,
                headers=headers,
                json_data=params if op_id_clean != "slack.conversations.list" else None,
                params=params if op_id_clean == "slack.conversations.list" else None,
                timeout=request.timeout_seconds
            )
            latency = (time.perf_counter() - start_time) * 1000.0

            if isinstance(res, dict):
                is_ok = bool(res.get("ok"))
                logger.info(
                    f"[SLACK_POST_MESSAGE_RESULT] ok={is_ok} channel={res.get('channel')} "
                    f"ts={res.get('ts')} error={res.get('error')}"
                )
                if is_ok:
                    return ConnectorResponseModel(
                        success=True,
                        operation_id=request.operation_id,
                        status_code=200,
                        data=res,
                        latency_ms=round(latency, 2),
                    )
                else:
                    err_msg = res.get("error") or "Slack API operation failed."
                    is_auth_err = res.get("error") in ["not_authed", "invalid_auth"]
                    return ConnectorResponseModel(
                        success=False,
                        operation_id=request.operation_id,
                        status_code=401 if is_auth_err else 400,
                        error_message=f"Slack API error: {err_msg}",
                        data=res,
                        latency_ms=round(latency, 2),
                    )
            else:
                return ConnectorResponseModel(
                    success=False,
                    operation_id=request.operation_id,
                    status_code=500,
                    error_message="Unexpected non-JSON response from Slack API.",
                    data={"ok": False, "raw": str(res)},
                    latency_ms=round(latency, 2),
                )
        except Exception as exc:
            latency = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"[SLACK_API_EXCEPTION] Operation '{request.operation_id}' failed: {exc}")
            return ConnectorResponseModel(
                success=False,
                operation_id=request.operation_id,
                status_code=500,
                error_message=f"Slack request failed: {str(exc)}",
                data={"ok": False, "error": str(exc)},
                latency_ms=round(latency, 2),
            )
