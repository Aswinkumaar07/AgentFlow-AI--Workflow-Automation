from fastapi import HTTPException, status
from typing import Any, Optional

class AgentFlowException(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        message: str = "Bad Request",
        error_code: str = "BAD_REQUEST",
        details: Optional[Any] = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.error_code = error_code
        self.details = details

class NotFoundException(AgentFlowException):
    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="NOT_FOUND_404",
            details=details,
        )

class UnauthorizedException(AgentFlowException):
    def __init__(self, message: str = "Unauthorized", details: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_code="AUTH_401",
            details=details,
        )

class ForbiddenException(AgentFlowException):
    def __init__(self, message: str = "Forbidden", details: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_code="AUTH_403",
            details=details,
        )

class ConflictException(AgentFlowException):
    def __init__(self, message: str = "Resource conflict", details: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            error_code="CONFLICT_409",
            details=details,
        )

class ValidationException(AgentFlowException):
    def __init__(self, message: str = "Validation error", details: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_code="VALIDATION_422",
            details=details,
        )
