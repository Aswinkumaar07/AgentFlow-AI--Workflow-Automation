class ConnectorError(Exception):
    """Base exception class for Enterprise Connector Framework."""

    def __init__(
        self,
        message: str,
        provider: str = "GenericConnector",
        status_code: int = 500,
        original_error: Exception | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.status_code = status_code
        self.original_error = original_error

    def __str__(self) -> str:
        return f"[{self.provider} error {self.status_code}] {self.message}"


class ConnectorTimeoutError(ConnectorError):
    """Raised when connector operation times out."""

    def __init__(self, message: str, provider: str = "GenericConnector", original_error: Exception | None = None):
        super().__init__(message, provider=provider, status_code=504, original_error=original_error)


class ConnectorRateLimitError(ConnectorError):
    """Raised when provider returns HTTP 429 Rate Limit / Quota Exceeded."""

    def __init__(self, message: str, provider: str = "GenericConnector", original_error: Exception | None = None):
        super().__init__(message, provider=provider, status_code=429, original_error=original_error)


class ConnectorAuthenticationError(ConnectorError):
    """Raised when authentication credentials or OAuth tokens fail."""

    def __init__(self, message: str, provider: str = "GenericConnector", original_error: Exception | None = None):
        super().__init__(message, provider=provider, status_code=401, original_error=original_error)


class ConnectorAuthorizationError(ConnectorError):
    """Raised when insufficient OAuth scopes or permissions are present."""

    def __init__(self, message: str, provider: str = "GenericConnector", original_error: Exception | None = None):
        super().__init__(message, provider=provider, status_code=403, original_error=original_error)


class ConnectorValidationError(ConnectorError):
    """Raised when request payload or parameters fail schema validation."""

    def __init__(self, message: str, provider: str = "GenericConnector", original_error: Exception | None = None):
        super().__init__(message, provider=provider, status_code=400, original_error=original_error)


class ConnectorUnavailableError(ConnectorError):
    """Raised when provider API returns 502/503/504 Service Unavailable."""

    def __init__(self, message: str, provider: str = "GenericConnector", original_error: Exception | None = None):
        super().__init__(message, provider=provider, status_code=503, original_error=original_error)


class ConnectorExecutionError(ConnectorError):
    """Raised when connector execution fails at runtime."""

    def __init__(self, message: str, provider: str = "GenericConnector", status_code: int = 500, original_error: Exception | None = None):
        super().__init__(message, provider=provider, status_code=status_code, original_error=original_error)


class ConnectorRollbackError(ConnectorError):
    """Raised when compensation/rollback workflow fails."""

    def __init__(self, message: str, provider: str = "GenericConnector", original_error: Exception | None = None):
        super().__init__(message, provider=provider, status_code=500, original_error=original_error)
