import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("agentflow.access")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        user_id = "anonymous"

        # Attempt to read user_id from request state if set by auth dependency
        if hasattr(request.state, "user") and request.state.user:
            user_id = str(getattr(request.state.user, "id", "unknown"))

        response = await call_next(request)

        process_time = (time.time() - start_time) * 1000  # milliseconds
        formatted_process_time = f"{process_time:.2f}ms"

        logger.info(
            f"Method={request.method} Path={request.url.path} Status={response.status_code} "
            f"Duration={formatted_process_time} IP={client_ip} UserID={user_id}"
        )

        response.headers["X-Process-Time"] = formatted_process_time
        return response
