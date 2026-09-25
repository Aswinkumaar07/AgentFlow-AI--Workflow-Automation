import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.agents.llm.base import BaseLLMProvider
from app.agents.llm.enums import ProviderType
from app.agents.llm.exceptions import (
    LLMAuthenticationError,
    LLMJSONParseError,
    LLMProviderError,
    LLMRateLimitError,
    LLMValidationError,
)
from app.agents.llm.response_parser import ResponseParser
from app.core.config import settings

logger = logging.getLogger("agentflow.llm.gemini")


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM Provider implementation using official google-genai SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        super().__init__()
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY", "")
        self.model_name = (
            model_name or getattr(settings, "GEMINI_MODEL", None) or os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
        )

        self._client = None
        self._initialize_client()

    @property
    def provider_type(self) -> ProviderType:
        """Returns ProviderType.GEMINI enum identity."""
        return ProviderType.GEMINI

    def _initialize_client(self) -> None:
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. GeminiProvider operating with fallback mock responses.")
            return

        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            logger.info(f"GeminiProvider initialized successfully with model: {self.model_name}")
        except ImportError:
            logger.warning("google-genai SDK is not installed. GeminiProvider running in fallback mode.")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")

    async def health_check(self) -> bool:
        if not self.api_key or not self._client:
            return False
        try:
            res = await self.generate_text("ping", temperature=0.0, max_output_tokens=5)
            return bool(res)
        except Exception as e:
            logger.warning(f"GeminiProvider health check failed: {e}")
            return False

    def _generate_content_sync(self, prompt: str, temperature: float, max_output_tokens: int) -> str:
        if not self._client:
            return f"[Gemini Mock Response] Processed prompt: {prompt[:100]}"

        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                },
            )
            if response and hasattr(response, "text") and response.text:
                return response.text
            return str(response)
        except Exception as e:
            err_str = str(e).lower()
            if "api_key" in err_str or "unauthorized" in err_str or "401" in err_str:
                raise LLMAuthenticationError(f"Gemini authentication failed: {e}", provider="Gemini", original_error=e) from e
            if "quota" in err_str or "rate limit" in err_str or "429" in err_str:
                raise LLMRateLimitError(f"Gemini rate limit exceeded: {e}", provider="Gemini", original_error=e) from e
            raise LLMProviderError(f"Gemini generation error: {e}", provider="Gemini", original_error=e) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(LLMProviderError),
        reraise=True,
    )
    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> str:
        if not prompt or not prompt.strip():
            raise LLMValidationError("Prompt string cannot be empty.", provider="Gemini")

        start = time.perf_counter()
        try:
            res = await asyncio.to_thread(
                self._generate_content_sync,
                prompt,
                temperature,
                max_output_tokens,
            )
            duration_ms = (time.perf_counter() - start) * 1000.0
            self.record_execution_metrics(prompt, res, duration_ms, success=True)
            return res
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000.0
            self.record_execution_metrics(prompt, "", duration_ms, success=False)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(LLMProviderError),
        reraise=True,
    )
    async def generate_json(
        self,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        json_prompt = f"{prompt}\n\nIMPORTANT: Respond ONLY with valid raw JSON object. Do NOT use markdown fences like ```json or ```."
        raw_text = await self.generate_text(json_prompt, temperature=0.1)

        try:
            return ResponseParser.extract_json(raw_text)
        except LLMJSONParseError:
            cleaned = ResponseParser.clean_markdown(raw_text)
            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict):
                    return parsed
                return {"result": parsed}
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from Gemini response: {raw_text[:200]}")
                raise LLMJSONParseError(
                    message=f"Gemini response could not be parsed as valid JSON: {e}",
                    provider="Gemini",
                    original_error=e,
                ) from e
