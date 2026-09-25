from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseRAGService(ABC):
    """
    Abstract Interface for Retrieval-Augmented Generation (RAG).
    
    TODO: Plug in Qdrant / Pinecone / pgvector retrieval for API documentation & context.
    """

    @abstractmethod
    async def retrieve_context(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant API documentation chunks for prompt augmentation.
        """
        pass
