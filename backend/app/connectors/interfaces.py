from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from app.connectors.models import (
    ConnectorCredentialModel,
    ConnectorMetadataModel,
    ConnectorRequestModel,
    ConnectorResponseModel,
)


class BaseProviderAdapter(ABC):
    """Abstract Interface for concrete SaaS Provider Adapters (Gmail, Drive, Slack, GitHub, etc.)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns string name of provider."""
        raise NotImplementedError

    @abstractmethod
    def get_metadata(self) -> ConnectorMetadataModel:
        """Returns metadata detailing supported operations and auth types."""
        raise NotImplementedError

    @abstractmethod
    async def execute_operation(
        self, request: ConnectorRequestModel, credentials: Optional[ConnectorCredentialModel] = None
    ) -> ConnectorResponseModel:
        """Executes a specific operation against the provider API."""
        raise NotImplementedError


class BaseAuthHandler(ABC):
    """Abstract Interface for Authentication Handlers (OAuth2, PKCE, API Key, JWT)."""

    @abstractmethod
    async def apply_auth(self, headers: Dict[str, str], credentials: ConnectorCredentialModel) -> Dict[str, str]:
        """Applies authentication headers/tokens to request."""
        raise NotImplementedError

    @abstractmethod
    async def refresh_tokens(self, credentials: ConnectorCredentialModel) -> ConnectorCredentialModel:
        """Refreshes expired tokens if supported."""
        raise NotImplementedError


class BaseSecretManager(ABC):
    """Abstract Interface for Secret Management (HashiCorp Vault, AWS Secrets Manager, Encrypted Store)."""

    @abstractmethod
    async def get_secret(self, tenant_id: str, provider: str) -> Optional[ConnectorCredentialModel]:
        """Retrieves and decrypts tenant credentials."""
        raise NotImplementedError

    @abstractmethod
    async def set_secret(self, tenant_id: str, provider: str, credentials: ConnectorCredentialModel) -> bool:
        """Encrypts and stores tenant credentials."""
        raise NotImplementedError


class BaseConnectionPool(ABC):
    """Abstract Interface for HTTP/2 Persistent Connection Pooling."""

    @abstractmethod
    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """Dispatches HTTP request over persistent pooled client."""
        raise NotImplementedError


class BaseConnectorExecutor(ABC):
    """Abstract Interface for Execution Engine (retries, timeouts, rate limiting, rollback)."""

    @abstractmethod
    async def execute(
        self, adapter: BaseProviderAdapter, request: ConnectorRequestModel, credentials: Optional[ConnectorCredentialModel] = None
    ) -> ConnectorResponseModel:
        """Executes operation through resilience pipeline."""
        raise NotImplementedError
