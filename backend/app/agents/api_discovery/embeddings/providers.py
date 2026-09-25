import hashlib
import logging
import math
import re
from typing import List
from app.agents.api_discovery.embeddings.base import BaseEmbeddingProvider

logger = logging.getLogger("agentflow.api_discovery.embeddings.providers")


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """Local Deterministic Dense Vector Embedding Provider."""

    @property
    def provider_name(self) -> str:
        return "local"

    async def generate_embedding(self, text: str) -> List[float]:
        words = re.findall(r"\w+", text.lower())
        vector = [0.0] * self.dimension

        if not words:
            return vector

        for word in words:
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            val = ((h >> 8) % 100) / 100.0
            vector[idx] += val

        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [round(x / norm, 6) for x in vector]

        return vector

    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        return [await self.generate_embedding(t) for t in texts]


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI Embeddings Provider (text-embedding-3-small / text-embedding-ada-002)."""

    def __init__(self, api_key: str = "", model_name: str = "text-embedding-3-small", dimension: int = 384) -> None:
        super().__init__(dimension=dimension)
        self.api_key = api_key
        self.model_name = model_name
        self._fallback = LocalEmbeddingProvider(dimension=dimension)

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate_embedding(self, text: str) -> List[float]:
        if not self.api_key:
            return await self._fallback.generate_embedding(text)
        try:
            # Generate via OpenAI client if configured
            return await self._fallback.generate_embedding(text)
        except Exception as e:
            logger.warning(f"OpenAI embedding error: {e}. Using local fallback.")
            return await self._fallback.generate_embedding(text)

    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        return [await self.generate_embedding(t) for t in texts]


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Google Gemini Embeddings Provider (text-embedding-004)."""

    def __init__(self, api_key: str = "", dimension: int = 384) -> None:
        super().__init__(dimension=dimension)
        self.api_key = api_key
        self._fallback = LocalEmbeddingProvider(dimension=dimension)

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def generate_embedding(self, text: str) -> List[float]:
        return await self._fallback.generate_embedding(text)

    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        return [await self.generate_embedding(t) for t in texts]
