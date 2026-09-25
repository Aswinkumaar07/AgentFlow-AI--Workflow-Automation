from typing import Dict, List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class APIDiscoveryConfig(BaseSettings):
    """Configuration for Enterprise API Discovery Platform."""

    # Vector Store & Embedding Settings
    VECTORSTORE_PROVIDER: str = Field(default="memory", description="Vector store backend: 'memory', 'faiss', 'qdrant', 'pgvector', 'chroma', 'pinecone'")
    EMBEDDING_PROVIDER: str = Field(default="local", description="Embedding provider: 'local', 'openai', 'gemini', 'bge', 'sentence_transformers', 'voyage'")
    EMBEDDING_DIMENSION: int = Field(default=384, description="Vector embedding dimension size.")

    # Cache Settings
    CACHE_BACKEND: str = Field(default="memory", description="Cache backend: 'memory', 'redis'")
    CACHE_TTL_SECONDS: int = Field(default=3600, description="Cache TTL in seconds.")
    CACHE_BACKGROUND_WARMUP: bool = Field(default=True, description="Enable background cache warmup.")

    # Hybrid Search & Ranking Weights
    WEIGHT_VECTOR_SIMILARITY: float = 0.40
    WEIGHT_BM25: float = 0.25
    WEIGHT_POPULARITY: float = 0.15
    WEIGHT_HEALTH_SCORE: float = 0.10
    WEIGHT_LATENCY: float = 0.05
    WEIGHT_COST: float = 0.05

    # Catalog & Indexing Settings
    CATALOG_DIR: str = Field(default="backend/app/agents/api_discovery/catalog", description="Directory path for YAML provider catalogs.")
    AUTO_INDEX_ON_STARTUP: bool = Field(default=True, description="Automatically index catalog YAML files on startup.")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


discovery_config = APIDiscoveryConfig()
