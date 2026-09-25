from typing import Any, Dict, Optional


class LLMError(Exception):
    """Base exception class for all LLM layer errors.

    Attributes:
        message: Human-readable error explanation.
        provider: Name of the LLM provider service (e.g. 'Gemini', 'OpenAI').
        status_code: HTTP-style error status code.
        original_error: Optional underlying exception object that triggered this error.
    """

    def __init__(
        self,
        message: str = "An error occurred in the LLM provider layer.",
        provider: str = "Unknown",
        status_code: int = 500,
        original_error: Optional[Exception] = None,
    ) -> None:
        """Initializes the base LLM exception.

        Args:
            message: Explanation of the error condition.
            provider: Target provider name.
            status_code: Associated status code.
            original_error: Original exception if chained.
        """
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.status_code = status_code
        self.original_error = original_error

    def __str__(self) -> str:
        """Returns string representation of the exception."""
        return f"[{self.provider}] [{self.status_code}] {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Serializes exception details to a standard dictionary format.

        Returns:
            Dictionary containing error, provider, status_code, and message.
        """
        return {
            "error": self.__class__.__name__,
            "provider": self.provider,
            "status_code": self.status_code,
            "message": self.message,
        }


class LLMProviderError(LLMError):
    """Exception raised when an upstream LLM provider returns an unhandled error."""

    def __init__(
        self,
        message: str = "Upstream LLM provider returned an unexpected error.",
        provider: str = "Unknown",
        status_code: int = 500,
        original_error: Optional[Exception] = None,
    ) -> None:
        super().__init__(
            message=message,
            provider=provider,
            status_code=status_code,
            original_error=original_error,
        )


class LLMAuthenticationError(LLMError):
    """Exception raised when authentication with an LLM provider fails (e.g. invalid API key)."""

    def __init__(
        self,
        message: str = "Authentication failed with the LLM provider.",
        provider: str = "Unknown",
        status_code: int = 401,
        original_error: Optional[Exception] = None,
    ) -> None:
        super().__init__(
            message=message,
            provider=provider,
            status_code=status_code,
            original_error=original_error,
        )


class LLMRateLimitError(LLMError):
    """Exception raised when an LLM provider rate limit or quota is exceeded."""

    def __init__(
        self,
        message: str = "LLM provider rate limit exceeded.",
        provider: str = "Unknown",
        status_code: int = 429,
        original_error: Optional[Exception] = None,
    ) -> None:
        super().__init__(
            message=message,
            provider=provider,
            status_code=status_code,
            original_error=original_error,
        )


class LLMTimeoutError(LLMError):
    """Exception raised when a request to an LLM provider times out."""

    def __init__(
        self,
        message: str = "Request to LLM provider timed out.",
        provider: str = "Unknown",
        status_code: int = 408,
        original_error: Optional[Exception] = None,
    ) -> None:
        super().__init__(
            message=message,
            provider=provider,
            status_code=status_code,
            original_error=original_error,
        )


class LLMConnectionError(LLMError):
    """Exception raised when network connection to an LLM provider fails."""

    def __init__(
        self,
        message: str = "Failed to establish connection with LLM provider.",
        provider: str = "Unknown",
        status_code: int = 503,
        original_error: Optional[Exception] = None,
    ) -> None:
        super().__init__(
            message=message,
            provider=provider,
            status_code=status_code,
            original_error=original_error,
        )


class LLMJSONParseError(LLMError):
    """Exception raised when an LLM response fails to parse as valid JSON."""

    def __init__(
        self,
        message: str = "Failed to parse structured JSON from LLM response.",
        provider: str = "Unknown",
        status_code: int = 500,
        original_error: Optional[Exception] = None,
    ) -> None:
        super().__init__(
            message=message,
            provider=provider,
            status_code=status_code,
            original_error=original_error,
        )


class LLMValidationError(LLMError):
    """Exception raised when LLM input parameters or schema constraints fail validation."""

    def __init__(
        self,
        message: str = "LLM payload or schema validation failed.",
        provider: str = "Unknown",
        status_code: int = 422,
        original_error: Optional[Exception] = None,
    ) -> None:
        super().__init__(
            message=message,
            provider=provider,
            status_code=status_code,
            original_error=original_error,
        )


class LLMConfigurationError(LLMError):
    """Exception raised when LLM provider configuration or credentials are missing/invalid."""

    def __init__(
        self,
        message: str = "LLM provider configuration error.",
        provider: str = "Unknown",
        status_code: int = 500,
        original_error: Optional[Exception] = None,
    ) -> None:
        super().__init__(
            message=message,
            provider=provider,
            status_code=status_code,
            original_error=original_error,
        )


class LLMUnavailableError(LLMError):
    """Exception raised when the LLM provider service is temporarily unavailable or in maintenance."""

    def __init__(
        self,
        message: str = "LLM provider service is currently unavailable.",
        provider: str = "Unknown",
        status_code: int = 503,
        original_error: Optional[Exception] = None,
    ) -> None:
        super().__init__(
            message=message,
            provider=provider,
            status_code=status_code,
            original_error=original_error,
        )
