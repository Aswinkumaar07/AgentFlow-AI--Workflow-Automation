from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EngineConfig(BaseSettings):
    """Configuration for Enterprise Workflow Execution Engine."""

    WORKFLOW_STATE_STORE: str = Field(default="memory", description="State store backend: 'memory', 'redis', 'postgres'")
    WORKFLOW_QUEUE_BROKER: str = Field(default="memory", description="Queue broker backend: 'memory', 'redis'")
    MAX_CONCURRENT_WORKFLOWS: int = Field(default=1000, description="Maximum concurrent workflow executions.")
    CHECKPOINT_INTERVAL_SECONDS: float = Field(default=1.0, description="State checkpoint interval in seconds.")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


engine_config = EngineConfig()
