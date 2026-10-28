import asyncio
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from pydantic import BaseModel, Field

from app.agents.api_discovery.service import api_discovery_agent
from app.agents.api_discovery.dynamic_discovery import DynamicDiscoveryResult

logger = logging.getLogger("agentflow.agents.planner.ai37_bridge")

OPENAPI_SWAGGER_INDICATORS = [
    "/openapi",
    "/openapi.json",
    "/openapi.yaml",
    "/openapi.yml",
    "/swagger",
    "/swagger.json",
    "/swagger.yaml",
    "/api-docs",
    "openapi specification",
    "swagger specification",
    "api spec",
    "openapi spec",
    "swagger spec",
]


class AI37BridgeResult(BaseModel):
    attempted: bool = False
    success: bool = False
    url: Optional[str] = None
    provider: Optional[str] = None
    namespace: Optional[str] = None
    discovered_ops_count: int = 0
    discovered_ops: List[Dict[str, Any]] = Field(default_factory=list)
    error_message: Optional[str] = None
    error_category: Optional[str] = None


def extract_qualifying_spec_url(prompt: str) -> Optional[str]:
    """
    Extracts an explicit, valid HTTPS OpenAPI/Swagger spec URL from the prompt.
    Must meet BOTH criteria:
    1. Valid HTTPS URL (starts with https://)
    2. Strong OpenAPI/Swagger spec indicator in URL path or prompt text.
    """
    if not prompt or not prompt.strip():
        return None

    p_lower = prompt.lower()

    # Match https:// URLs
    raw_urls = re.findall(r"https://[^\s><\"'`\]\)]+", prompt)
    if not raw_urls:
        return None

    for raw_url in raw_urls:
        # Strip trailing punctuation
        clean_url = raw_url.rstrip(".,;:?!")
        try:
            parsed = urlparse(clean_url)
        except Exception:
            continue

        if parsed.scheme != "https":
            continue

        hostname = (parsed.hostname or "").lower()
        if (
            hostname in ["localhost", "127.0.0.1", "0.0.0.0", "::1"]
            or hostname.startswith("192.168.")
            or hostname.startswith("10.")
            or hostname.startswith("172.16.")
        ):
            continue

        url_lower = clean_url.lower()

        # 1. URL Path Indicator Check
        has_url_indicator = any(
            ind in url_lower
            for ind in [
                "/openapi",
                "/openapi.json",
                "/openapi.yaml",
                "/openapi.yml",
                "/swagger",
                "/swagger.json",
                "/swagger.yaml",
                "/api-docs",
            ]
        )

        # 2. Prompt Text Indicator Check
        has_prompt_indicator = any(
            ind in p_lower
            for ind in [
                "openapi specification",
                "swagger specification",
                "api spec",
                "openapi spec",
                "swagger spec",
            ]
        )

        if has_url_indicator or has_prompt_indicator:
            return clean_url

    return None


class AI37PlannerBridge:
    """
    Bridge connecting AI-37 Dynamic API Discovery to Planner V4.
    Evaluates prompts for explicit OpenAPI/Swagger URLs and performs remote specification discovery.
    """

    def discover_if_eligible(self, prompt: str) -> AI37BridgeResult:
        """
        Determines whether the prompt qualifies for AI-37 dynamic spec discovery.
        If eligible, retrieves and registers the API spec asynchronously.
        """
        spec_url = extract_qualifying_spec_url(prompt)
        if not spec_url:
            return AI37BridgeResult(attempted=False, success=False)

        logger.info(
            f"[AI-37][BRIDGE] Qualifying OpenAPI/Swagger spec URL detected: '{spec_url}'"
        )

        try:
            # Synchronously execute async discovery call safely
            discovery_res: DynamicDiscoveryResult = self._run_async(
                api_discovery_agent.discover_and_register_from_url(spec_url)
            )
        except Exception as e:
            logger.error(
                f"[AI-37][BRIDGE] Exception during remote spec discovery for '{spec_url}': {e}"
            )
            return AI37BridgeResult(
                attempted=True,
                success=False,
                url=spec_url,
                error_message=str(e),
                error_category="UNHANDLED_EXCEPTION",
            )

        if not discovery_res.success:
            logger.warning(
                f"[AI-37][BRIDGE] Remote spec discovery failed for '{spec_url}': {discovery_res.message}"
            )
            return AI37BridgeResult(
                attempted=True,
                success=False,
                url=spec_url,
                error_message=discovery_res.message,
                error_category="DISCOVERY_FAILED",
            )

        ops = (
            discovery_res.connector_spec.operations
            if discovery_res.connector_spec
            else []
        )
        provider = discovery_res.provider or "Discovered API"

        logger.info(
            f"[AI-37][BRIDGE] Successfully discovered provider '{provider}' with {len(ops)} operation(s) from '{spec_url}'"
        )

        return AI37BridgeResult(
            attempted=True,
            success=True,
            url=spec_url,
            provider=provider,
            namespace=provider.lower().replace(" ", "_"),
            discovered_ops_count=len(ops),
            discovered_ops=ops,
        )

    def _run_async(self, coro: Any) -> Any:
        """Runs an async coroutine synchronously, handling existing event loops safely."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(lambda: asyncio.run(coro))
                return future.result()
        else:
            return asyncio.run(coro)


ai37_planner_bridge = AI37PlannerBridge()
