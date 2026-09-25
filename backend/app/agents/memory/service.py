from typing import Dict, Any, Optional, List
from app.agents.memory.interface import BaseMemoryService
from app.agents.tools import memory_tool

class MemoryAgent(BaseMemoryService):
    """
    Memory Agent Node for storing and retrieving past successful workflows.
    """
    async def store_state(self, session_id: str, state: Dict[str, Any]) -> bool:
        return True

    async def get_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        return None

    async def find_similar_workflows(self, prompt: str) -> List[Dict[str, Any]]:
        return await memory_tool.search_previous_workflows(prompt)

memory_agent = MemoryAgent()
