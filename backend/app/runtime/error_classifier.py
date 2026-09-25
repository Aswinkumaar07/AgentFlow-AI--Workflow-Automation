import re
from typing import Any, Dict, Optional

RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
NON_RETRYABLE_STATUS_CODES = {400, 401, 403, 404, 422}

RETRYABLE_KEYWORDS = [
    "timeout",
    "timed out",
    "connection error",
    "connection refused",
    "connection reset",
    "temporary failure",
    "service unavailable",
    "bad gateway",
    "gateway timeout",
    "too many requests",
    "rate limit",
    "socket error",
    "network error",
    "500",
    "502",
    "503",
    "504",
    "429",
    "408",
]

NON_RETRYABLE_KEYWORDS = [
    "unauthorized",
    "forbidden",
    "authentication failed",
    "invalid credentials",
    "invalid api key",
    "invalid token",
    "bad request",
    "validation error",
    "missing required parameter",
    "invalid parameter",
    "invalid workflow configuration",
    "not found",
    "400",
    "401",
    "403",
    "404",
]


def classify_error(error: Any) -> Dict[str, Any]:
    """
    Classifies a node execution error as retryable or non-retryable.
    Returns metadata dict: { 'retryable': bool, 'error_type': str, 'status_code': int|None, 'message': str }
    """
    status_code: Optional[int] = None
    msg = ""

    if isinstance(error, dict):
        status_code = error.get("status_code") or error.get("code") or error.get("status")
        msg = str(error.get("error") or error.get("message") or error.get("details") or error)
    elif isinstance(error, Exception):
        msg = str(error)
        if hasattr(error, "status_code"):
            status_code = getattr(error, "status_code")
        elif hasattr(error, "code"):
            status_code = getattr(error, "code")
    else:
        msg = str(error)

    # Attempt to extract numeric status code from message string if not explicitly set
    if status_code is None and msg:
        code_match = re.search(r"\b(4\d\d|5\d\d)\b", msg)
        if code_match:
            try:
                status_code = int(code_match.group(1))
            except ValueError:
                pass

    msg_lower = msg.lower()

    # Rule 1: Numeric status code classification
    if status_code is not None:
        if status_code in RETRYABLE_STATUS_CODES:
            return {
                "retryable": True,
                "error_type": f"HTTP_{status_code}",
                "status_code": status_code,
                "message": msg,
            }
        if status_code in NON_RETRYABLE_STATUS_CODES:
            return {
                "retryable": False,
                "error_type": f"HTTP_{status_code}",
                "status_code": status_code,
                "message": msg,
            }

    # Rule 2: Keyword classification
    for kw in NON_RETRYABLE_KEYWORDS:
        if kw in msg_lower:
            return {
                "retryable": False,
                "error_type": "NON_RETRYABLE_ERROR",
                "status_code": status_code,
                "message": msg,
            }

    for kw in RETRYABLE_KEYWORDS:
        if kw in msg_lower:
            return {
                "retryable": True,
                "error_type": "TEMPORARY_NETWORK_OR_SERVER_ERROR",
                "status_code": status_code,
                "message": msg,
            }

    # Default fallback: If message contains explicit error indication, treat generic failures as non-retryable by default
    # unless configured explicitly.
    return {
        "retryable": False,
        "error_type": "GENERIC_ERROR",
        "status_code": status_code,
        "message": msg,
    }
