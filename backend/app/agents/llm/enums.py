from enum import Enum


class ExecutionMode(str, Enum):
    """System Execution Modes."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"

    @classmethod
    def from_str(cls, value: str) -> "ExecutionMode":
        """Normalizes string input to ExecutionMode enum."""
        if not value:
            return cls.DEVELOPMENT
        cleaned = value.lower().strip()
        if cleaned in ["dev", "mock", "development"]:
            return cls.DEVELOPMENT
        return cls.PRODUCTION


class ProviderType(str, Enum):
    """Supported LLM Provider Types."""

    GEMINI = "gemini"
    MOCK = "mock"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"

    @classmethod
    def from_str(cls, value: str) -> "ProviderType":
        """Normalizes string input to ProviderType enum."""
        cleaned = (value or "gemini").lower().strip()
        for member in cls:
            if member.value == cleaned:
                return member
        return cls.GEMINI


class AgentType(str, Enum):
    """Multi-Agent System Node Types."""

    PLANNER = "planner"
    DISCOVERY = "discovery"
    WORKFLOW = "workflow"
    VALIDATION = "validation"
    REPAIR = "repair"

    @classmethod
    def from_str(cls, value: str) -> "AgentType":
        """Normalizes string input to AgentType enum."""
        cleaned = (value or "planner").lower().strip()
        if "workflow" in cleaned:
            return cls.WORKFLOW
        if "discover" in cleaned:
            return cls.DISCOVERY
        if "validat" in cleaned:
            return cls.VALIDATION
        if "repair" in cleaned or "heal" in cleaned:
            return cls.REPAIR
        return cls.PLANNER
