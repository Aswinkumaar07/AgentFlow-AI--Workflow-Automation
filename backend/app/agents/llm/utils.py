import json
import time
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar, ParamSpec

P = ParamSpec("P")
T = TypeVar("T")


def estimate_tokens(text: str) -> int:
    """
    Estimate the approximate number of LLM tokens.

    Rule of thumb:
    ~4 characters ≈ 1 token

    Args:
        text: Input text.

    Returns:
        Estimated token count.
    """
    if not text:
        return 0

    return max(1, len(text) // 4)


def truncate_prompt(text: str, max_tokens: int) -> str:
    """
    Truncate a prompt so it approximately fits within a token limit.

    Args:
        text: Prompt text.
        max_tokens: Maximum allowed tokens.

    Returns:
        Truncated prompt.
    """
    if not text:
        return ""

    if max_tokens <= 0:
        raise ValueError("max_tokens must be greater than zero.")

    estimated = estimate_tokens(text)

    if estimated <= max_tokens:
        return text

    max_chars = max_tokens * 4

    return text[:max_chars].rstrip() + "..."


def safe_json_dumps(obj: Any) -> str:
    """
    Safely serialize any object to formatted JSON.

    Args:
        obj: Python object.

    Returns:
        Pretty JSON string.
    """
    try:
        return json.dumps(
            obj,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    except Exception:
        return json.dumps(
            {"raw": str(obj)},
            indent=2,
            ensure_ascii=False,
        )


def mask_api_key(api_key: str) -> str:
    """
    Mask sensitive API keys before logging.

    Example:
        AIzaSy123456789ABCDE

    becomes

        AIza************BCDE

    Args:
        api_key: Original API key.

    Returns:
        Masked API key.
    """
    if not api_key:
        return "****"

    key = api_key.strip()

    if len(key) <= 8:
        return "*" * len(key)

    return (
        key[:4]
        + "*" * (len(key) - 8)
        + key[-4:]
    )


def measure_execution_time(
    func: Callable[P, Awaitable[T]],
) -> Callable[P, Awaitable[T]]:
    """
    Async decorator that measures execution time.

    Unlike the previous implementation,
    this decorator DOES NOT mutate the returned object.

    The execution time is attached to the wrapped function
    as ``last_execution_time_ms``.

    Args:
        func: Async function.

    Returns:
        Wrapped async function.
    """

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start = time.perf_counter()

        result = await func(*args, **kwargs)

        elapsed = (time.perf_counter() - start) * 1000

        wrapper.last_execution_time_ms = round(elapsed, 2)

        return result

    wrapper.last_execution_time_ms = 0.0

    return wrapper