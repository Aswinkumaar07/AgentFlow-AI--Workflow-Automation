class APIDiscoveryError(Exception):
    """Base exception class for API Discovery Platform."""

    def __init__(self, message: str, provider: str = "DiscoveryEngine", original_error: Exception | None = None):
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.original_error = original_error

    def __str__(self) -> str:
        return f"[{self.provider}] {self.message}"


class CatalogParseError(APIDiscoveryError):
    """Raised when parsing OpenAPI, Swagger, Postman, or YAML catalogs fails."""
    pass


class EmbeddingGenerationError(APIDiscoveryError):
    """Raised when generating vector embeddings fails."""
    pass


class VectorStoreError(APIDiscoveryError):
    """Raised when querying or storing vectors in vector database fails."""
    pass


class CapabilityGraphError(APIDiscoveryError):
    """Raised when building or searching capability graph fails."""
    pass
