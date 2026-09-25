from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingProvider(ABC):
    """Abstract Base Class for all Vector Embedding Providers."""

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns name identifier of the embedding provider."""
        raise NotImplementedError

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generates a float vector for a given text input."""
        raise NotImplementedError

    @abstractmethod
    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates float vectors for a batch of text inputs."""
        raise NotImplementedError
