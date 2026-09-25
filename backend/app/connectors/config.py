from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConnectorConfig(BaseSettings):
    """Configuration for Enterprise Connector Framework."""

    DEFAULT_TIMEOUT_SECONDS: float = Field(default=30.0, description="Default HTTP client timeout in seconds.")
    MAX_CONNECTIONS: int = Field(default=100, description="Maximum HTTP connections in connection pool.")
    MAX_KEEPALIVE_CONNECTIONS: int = Field(default=20, description="Maximum idle keep-alive connections.")
    ENCRYPTION_SECRET_KEY: str = Field(
        default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
        description="AES-256 secret key for encrypting tenant credentials.",
    )
    DEFAULT_RETRY_ATTEMPTS: int = Field(default=3, description="Default execution retry attempts.")
    DEFAULT_RETRY_COOLDOWN_SECONDS: float = Field(default=1.0, description="Default retry backoff cooldown in seconds.")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


connector_config = ConnectorConfig()
