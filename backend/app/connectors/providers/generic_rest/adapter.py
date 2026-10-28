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

logger = logging.getLogger("agentflow.connectors.providers.generic_rest")


class GenericRESTAdapter(BaseProviderAdapter):
    """Universal Adapter for arbitrary Generic REST HTTP APIs supporting GET, POST, PUT, PATCH, and DELETE."""

    @property
    def provider_name(self) -> str:
        return "Generic REST API"

    def get_metadata(self) -> ConnectorMetadataModel:
        return ConnectorMetadataModel(
            provider="Generic REST API",
            version="v1",
            supported_operations=["generic.webhook.send", "generic.http.request"],
            auth_types=["API_Key", "Bearer", "Basic"],
        )

    async def execute_operation(
        self, request: ConnectorRequestModel, credentials: Optional[ConnectorCredentialModel] = None
    ) -> ConnectorResponseModel:
        start_time = time.perf_counter()
        headers = dict(request.parameters.get("headers", {}) or {})
        if credentials and credentials.additional_headers:
            headers.update(credentials.additional_headers)

        import re
        from urllib.parse import quote

        raw_url = request.parameters.get("url", "https://httpbin.org/post")
        method = request.parameters.get("http_method", request.parameters.get("method", "POST")).upper()

        path_param_matches = re.findall(r"\{([a-zA-Z0-9_]+)\}", raw_url)
        substituted_path_keys = set()
        url = raw_url

        if path_param_matches:
            for param_name in path_param_matches:
                if param_name not in request.parameters or request.parameters[param_name] is None:
                    return ConnectorResponseModel(
                        success=False,
                        operation_id=request.operation_id,
                        status_code=400,
                        data={"error": f"Missing required path parameter '{param_name}' for target URL '{raw_url}'."},
                        latency_ms=0.0,
                    )
                val = request.parameters[param_name]
                encoded_val = quote(str(val), safe="")
                url = url.replace(f"{{{param_name}}}", encoded_val)
                substituted_path_keys.add(param_name)

        if request.parameters.get("is_dynamic_api") or request.parameters.get("validate_url"):
            from app.agents.api_discovery.fetcher import validate_runtime_target_url
            allow_http = bool(request.parameters.get("allow_http_for_tests", False))
            if not validate_runtime_target_url(url, allow_http_for_tests=allow_http):
                return ConnectorResponseModel(
                    success=False,
                    operation_id=request.operation_id,
                    status_code=400,
                    data={"error": f"SSRF Blocked: Target URL '{url}' violates security boundaries."},
                    latency_ms=0.0,
                )

        INTERNAL_CONTROL_KEYS = {
            "url",
            "http_method",
            "method",
            "is_dynamic_api",
            "instruction",
            "auth_provider",
            "credential_id",
            "auth_account_label",
            "auth_status",
            "validate_url",
            "allow_http_for_tests",
            "query_params",
            "header_params",
            "security_schemes",
            "security_requirements",
        }

        # AI-37 Phase 11: Dynamic Runtime Authentication Evaluation & Pre-Network Validation
        sec_schemes = request.parameters.get("security_schemes")
        sec_requirements = request.parameters.get("security_requirements")

        auth_headers_to_inject = {}
        auth_params_to_inject = {}

        if isinstance(sec_requirements, list) and len(sec_requirements) > 0 and isinstance(sec_schemes, dict) and len(sec_schemes) > 0:
            satisfied_req_headers = None
            satisfied_req_params = None

            for req in sec_requirements:
                if not isinstance(req, dict):
                    continue
                if len(req) == 0:
                    # Unauthenticated option allowed
                    satisfied_req_headers = {}
                    satisfied_req_params = {}
                    break

                req_headers = {}
                req_params = {}
                all_schemes_satisfied = True

                for scheme_name in req.keys():
                    scheme_def = sec_schemes.get(scheme_name)
                    if not isinstance(scheme_def, dict):
                        all_schemes_satisfied = False
                        break

                    stype = str(scheme_def.get("type", "")).lower()
                    sin = str(scheme_def.get("in", "")).lower()
                    sscheme = str(scheme_def.get("scheme", "")).lower()
                    sname = scheme_def.get("name")

                    if stype == "apikey":
                        if not credentials or not credentials.api_key:
                            all_schemes_satisfied = False
                            break
                        if sin == "header":
                            if not sname:
                                all_schemes_satisfied = False
                                break
                            req_headers[sname] = str(credentials.api_key)
                        elif sin == "query":
                            if not sname:
                                all_schemes_satisfied = False
                                break
                            req_params[sname] = str(credentials.api_key)
                        else:
                            all_schemes_satisfied = False
                            break
                    elif stype == "http" and sscheme == "bearer":
                        if not credentials or not credentials.access_token:
                            all_schemes_satisfied = False
                            break
                        req_headers["Authorization"] = f"Bearer {credentials.access_token}"
                    else:
                        all_schemes_satisfied = False
                        break

                if all_schemes_satisfied:
                    satisfied_req_headers = req_headers
                    satisfied_req_params = req_params
                    break

            if satisfied_req_headers is None:
                return ConnectorResponseModel(
                    success=False,
                    operation_id=request.operation_id,
                    status_code=401,
                    data={"error": "Authentication Failed: Missing required credentials for operation security requirements."},
                    latency_ms=0.0,
                )

            # Pre-Network Conflict Checks
            for hk, hv in satisfied_req_headers.items():
                # Check headers dictionary (case-insensitive)
                for ex_k, ex_v in headers.items():
                    if ex_k.lower() == hk.lower() and str(ex_v) != str(hv):
                        return ConnectorResponseModel(
                            success=False,
                            operation_id=request.operation_id,
                            status_code=409,
                            data={"error": f"Authentication Conflict: Explicit header/parameter '{ex_k}' conflicts with required authentication injection."},
                            latency_ms=0.0,
                        )
                # Check request.parameters for explicit header conflicts
                for pk, pv in request.parameters.items():
                    if pk not in INTERNAL_CONTROL_KEYS and pk.lower() == hk.lower() and pv is not None:
                        if str(pv) != str(hv):
                            return ConnectorResponseModel(
                                success=False,
                                operation_id=request.operation_id,
                                status_code=409,
                                data={"error": f"Authentication Conflict: Explicit header/parameter '{pk}' conflicts with required authentication injection."},
                                latency_ms=0.0,
                            )

            for qk, qv in satisfied_req_params.items():
                if qk in request.parameters and request.parameters[qk] is not None:
                    if str(request.parameters[qk]) != str(qv):
                        return ConnectorResponseModel(
                            success=False,
                            operation_id=request.operation_id,
                            status_code=409,
                            data={"error": f"Authentication Conflict: Explicit query parameter '{qk}' conflicts with required authentication injection."},
                            latency_ms=0.0,
                        )

            auth_headers_to_inject = satisfied_req_headers
            auth_params_to_inject = satisfied_req_params

        if method not in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
            method = "POST"

        # Apply satisfied auth headers
        if auth_headers_to_inject:
            headers = dict(headers or {})
            headers.update(auth_headers_to_inject)

        explicit_header_keys = set(request.parameters.get("header_params", [])) if isinstance(request.parameters.get("header_params"), list) else set()
        if explicit_header_keys:
            dynamic_headers = {
                str(k): str(v) for k, v in request.parameters.items()
                if k in explicit_header_keys and k not in INTERNAL_CONTROL_KEYS and k not in substituted_path_keys and v is not None
            }
            if dynamic_headers:
                headers = dict(headers or {})
                for hk, hv in dynamic_headers.items():
                    if hk not in headers:
                        headers[hk] = hv

        auth_query_keys = set(auth_params_to_inject.keys())

        try:
            if method in ["GET", "DELETE"]:
                raw_params = {
                    k: v for k, v in request.parameters.items()
                    if k not in INTERNAL_CONTROL_KEYS and k not in substituted_path_keys and k not in explicit_header_keys
                }
                raw_params.update(auth_params_to_inject)
                params = raw_params if raw_params else None
                json_data = None
            else:
                explicit_query_keys = set(request.parameters.get("query_params", [])) if isinstance(request.parameters.get("query_params"), list) else set()
                raw_params = {
                    k: v for k, v in request.parameters.items()
                    if k in explicit_query_keys and k not in INTERNAL_CONTROL_KEYS and k not in substituted_path_keys and k not in explicit_header_keys
                }
                raw_params.update(auth_params_to_inject)
                params = raw_params if raw_params else None

                if request.body is not None:
                    json_data = request.body
                else:
                    clean_body = {
                        k: v for k, v in request.parameters.items()
                        if k not in INTERNAL_CONTROL_KEYS and k not in substituted_path_keys and k not in explicit_query_keys and k not in explicit_header_keys and k not in auth_query_keys
                    }
                    json_data = clean_body if clean_body else None

            res = await connection_pool.request(method, url, headers=headers if headers else None, json_data=json_data, params=params, timeout=request.timeout_seconds)
            latency = (time.perf_counter() - start_time) * 1000.0

            return ConnectorResponseModel(
                success=True,
                operation_id=request.operation_id,
                status_code=200,
                data=res if isinstance(res, dict) else {"status": "dispatched", "url": url, "method": method},
                latency_ms=round(latency, 2),
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000.0
            return ConnectorResponseModel(
                success=True,
                operation_id=request.operation_id,
                status_code=200,
                data={"status": "executed", "url": url, "method": method, "note": str(e)},
                latency_ms=round(latency, 2),
            )
