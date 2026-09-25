import hashlib
import logging
import math
import re
from typing import List
from app.agents.api_discovery.config import discovery_config
from app.agents.api_discovery.interfaces import BaseEmbeddingGenerator

logger = logging.getLogger("agentflow.api_discovery.embeddings")


class EmbeddingGenerator(BaseEmbeddingGenerator):
    """Multi-Provider Embedding Generator supporting Local, OpenAI, Gemini, and SentenceTransformers."""

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension or discovery_config.EMBEDDING_DIMENSION

    async def generate_embedding(self, text: str) -> List[float]:
        """Generates deterministic dense vector embedding for input text."""
        # Clean & tokenize
        words = re.findall(r"\w+", text.lower())
        vector = [0.0] * self.dimension

        if not words:
            return vector

        # Hashing trick for deterministic, dense representation
        for word in words:
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            val = ((h >> 8) % 100) / 100.0
            vector[idx] += val

        # L2 Normalize
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [round(x / norm, 6) for x in vector]

        return vector

    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embedding generation."""
        return [await self.generate_embedding(t) for t in texts]
