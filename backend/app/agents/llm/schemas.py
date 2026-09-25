from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class LLMTextRequest(BaseModel):
    """Schema representing a text generation request to an LLM provider."""

    prompt: str = Field(..., description="Prompt text sent to the LLM model.")
    temperature: float = Field(default=0.2, ge=0.0, le=1.0, description="Sampling temperature.")
    max_output_tokens: int = Field(default=4096, ge=1, description="Maximum tokens to generate.")
    system_instruction: Optional[str] = Field(default=None, description="Optional system instruction context.")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class LLMJsonRequest(BaseModel):
    """Schema representing a structured JSON generation request to an LLM provider."""

    prompt: str = Field(..., description="Prompt text requesting structured JSON output.")
    schema_definition: Optional[Dict[str, Any]] = Field(default=None, description="Optional JSON Schema object.")
    temperature: float = Field(default=0.1, ge=0.0, le=1.0, description="Sampling temperature.")
    max_output_tokens: int = Field(default=4096, ge=1, description="Maximum tokens to generate.")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class LLMUsage(BaseModel):
    """Schema representing token usage metadata returned by the provider."""

    prompt_tokens: int = Field(default=0, ge=0, description="Tokens consumed by prompt input.")
    completion_tokens: int = Field(default=0, ge=0, description="Tokens generated in response.")
    total_tokens: int = Field(default=0, ge=0, description="Total tokens consumed.")


class LLMResponse(BaseModel):
    """Unified container schema for LLM provider execution output."""

    content: Any = Field(..., description="Generated text string or parsed JSON dictionary.")
    model: str = Field(..., description="Name of the LLM model used for generation.")
    provider: str = Field(..., description="Name of the LLM provider service.")
    usage: Optional[LLMUsage] = Field(default=None, description="Token usage statistics.")
    raw_response: Optional[Dict[str, Any]] = Field(default=None, description="Raw metadata from provider payload.")

    model_config = ConfigDict(arbitrary_types_allowed=True)
