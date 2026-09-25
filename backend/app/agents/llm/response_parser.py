import json
from typing import Any, Dict, Optional

from app.agents.llm.exceptions import LLMJSONParseError


class ResponseParser:
    """Enterprise parser for cleaning, extracting, and validating LLM responses."""

    @staticmethod
    def clean_markdown(text: str) -> str:
        """Removes markdown code fences (```json and ```) and surrounding whitespace from text.

        Args:
            text: Raw string output from LLM model.

        Returns:
            Cleaned text string.
        """
        if not text:
            return ""

        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        return cleaned.strip()

    @staticmethod
    def extract_json(text: str) -> Dict[str, Any]:
        """Extracts and parses the first complete JSON object from text.

        Locates the first '{' and last '}' characters, extracts the substring,
        and parses it as a Python dictionary.

        Args:
            text: Input string containing a JSON payload.

        Returns:
            Parsed JSON object as a dictionary.

        Raises:
            LLMJSONParseError: If no JSON braces are found or JSON parsing fails.
        """
        cleaned = ResponseParser.clean_markdown(text)

        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")

        if first_brace == -1 or last_brace == -1 or last_brace <= first_brace:
            raise LLMJSONParseError(
                message=f"No valid JSON object structure found in response: {text[:100]}...",
                provider="ResponseParser",
            )

        json_str = cleaned[first_brace : last_brace + 1]

        try:
            parsed = json.loads(json_str)
            if not isinstance(parsed, dict):
                raise LLMJSONParseError(
                    message=f"Extracted JSON is not a valid dictionary object: {type(parsed).__name__}",
                    provider="ResponseParser",
                )
            return parsed
        except json.JSONDecodeError as e:
            raise LLMJSONParseError(
                message=f"Failed to parse extracted JSON string: {str(e)}",
                provider="ResponseParser",
                original_error=e,
            ) from e

    @staticmethod
    def extract_text(text: str) -> str:
        """Extracts and returns cleaned raw text from LLM response.

        Args:
            text: Raw text response string.

        Returns:
            Cleaned text string.
        """
        return ResponseParser.clean_markdown(text)

    @staticmethod
    def validate_json(obj: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> bool:
        """Validates a JSON dictionary object against an optional schema.

        Placeholder implementation for future jsonschema integration.

        Args:
            obj: Parsed JSON dictionary object.
            schema: Optional JSON Schema dictionary.

        Returns:
            Boolean True if object is valid.
        """
        return True
