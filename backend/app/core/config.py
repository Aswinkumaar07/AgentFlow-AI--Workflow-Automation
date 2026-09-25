import os
from typing import List, Union, Optional
from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AgentFlow AI - Intelligent API Workflow Automation"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    EXECUTION_MODE: str = Field(default="development", description="System execution mode: 'development' or 'production'")
    LLM_PROVIDER: str = Field(default="gemini", description="Default LLM Provider: 'gemini', 'mock', 'openai', 'anthropic', 'ollama'")
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-pro"

    # OAuth 2.0 Provider Credentials
    FRONTEND_URL: str = Field(default="http://localhost:5173", description="Frontend base URL for OAuth result page redirects")
    GOOGLE_CLIENT_ID: str = Field(default="", description="Google OAuth Client ID")
    GOOGLE_CLIENT_SECRET: str = Field(default="", description="Google OAuth Client Secret")
    GOOGLE_REDIRECT_URI: str = Field(default="http://127.0.0.1:8000/api/v1/oauth/google/callback", description="Google OAuth Redirect URI")
    SLACK_CLIENT_ID: str = Field(default="", description="Slack OAuth Client ID")
    SLACK_CLIENT_SECRET: str = Field(default="", description="Slack OAuth Client Secret")
    SLACK_REDIRECT_URI: str = Field(default="http://127.0.0.1:8000/api/v1/oauth/slack/callback", description="Slack OAuth Redirect URI")
    GITHUB_CLIENT_ID: str = Field(default="", description="GitHub OAuth Client ID")
    GITHUB_CLIENT_SECRET: str = Field(default="", description="GitHub OAuth Client Secret")

    # LLM Resilience & Circuit Breaker Settings
    LLM_MAX_RETRIES: int = 3
    LLM_TIMEOUT_SECONDS: float = 30.0
    CIRCUIT_BREAKER_THRESHOLD: int = 3
    CIRCUIT_BREAKER_COOLDOWN_SECONDS: float = 60.0

    # LLM Failover Chain Configuration
    PRIMARY_PROVIDER: str = "gemini"
    SECONDARY_PROVIDER: Optional[str] = None
    TERTIARY_PROVIDER: Optional[str] = None
    FALLBACK_PROVIDER: str = "mock"

    # Security & JWT
    SECRET_KEY: str = Field(
        default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
        description="512-bit secret key for JWT signing"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "agentflow_user"
    POSTGRES_PASSWORD: str = "agentflow_password"
    POSTGRES_DB: str = "agentflow_db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None

    @computed_field
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            return url
        storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage"))
        os.makedirs(storage_dir, exist_ok=True)
        db_path = os.path.join(storage_dir, "agentflow.db").replace("\\", "/")
        return f"sqlite+aiosqlite:///{db_path}"

    # Redis Cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
    ]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    model_config = SettingsConfigDict(
        env_file=(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env"),
            ".env",
            "backend/.env",
        ),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
