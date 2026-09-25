from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseMemoryService(ABC):
    """
    Abstract Interface for Short-term and Long-term Agent Memory.
    
    TODO: Plug in Redis / Vector DB memory storage for agent conversation & state history.
    """

    @abstractmethod
    async def store_state(self, session_id: str, state: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    async def get_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        pass
