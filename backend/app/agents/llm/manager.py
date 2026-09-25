import logging
import os
import threading
from typing import Any, Dict, List, Optional

from app.agents.llm.base import BaseLLMProvider
from app.agents.llm.circuit_breaker import CircuitBreaker, CircuitState
from app.agents.llm.enums import AgentType, ExecutionMode, ProviderType
from app.agents.llm.exceptions import LLMError
from app.agents.llm.registry import ProviderRegistry, provider_registry
from app.agents.llm.telemetry import PrometheusMetricsExporter
from app.core.config import settings

logger = logging.getLogger("agentflow.llm.manager")


class LLMManager:
    """Enterprise Strategy Engine for resolving LLM Providers per Agent Node with Thread-Safe Resilience."""

    _instance: Optional["LLMManager"] = None

    DEFAULT_DEVELOPMENT_MAP: Dict[AgentType, ProviderType] = {
        AgentType.PLANNER: ProviderType.MOCK,
        AgentType.DISCOVERY: ProviderType.MOCK,
        AgentType.WORKFLOW: ProviderType.GEMINI,
        AgentType.VALIDATION: ProviderType.MOCK,
        AgentType.REPAIR: ProviderType.MOCK,
    }

    DEFAULT_PRODUCTION_MAP: Dict[AgentType, ProviderType] = {
        AgentType.PLANNER: ProviderType.GEMINI,
        AgentType.DISCOVERY: ProviderType.GEMINI,
        AgentType.WORKFLOW: ProviderType.GEMINI,
        AgentType.VALIDATION: ProviderType.GEMINI,
        AgentType.REPAIR: ProviderType.GEMINI,
    }

    def __new__(cls) -> "LLMManager":
        if cls._instance is None:
            cls._instance = super(LLMManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        self._registry: ProviderRegistry = provider_registry
        self._circuit_breakers: Dict[ProviderType, CircuitBreaker] = {}
        self._resolution_cache: Dict[AgentType, BaseLLMProvider] = {}
        self._lock = threading.Lock()

        self.reload_configuration()
        self._initialized = True

    def get_circuit_breaker(self, provider_type: ProviderType) -> CircuitBreaker:
        with self._lock:
            if provider_type not in self._circuit_breakers:
                threshold = getattr(settings, "CIRCUIT_BREAKER_THRESHOLD", 3)
                cooldown = getattr(settings, "CIRCUIT_BREAKER_COOLDOWN_SECONDS", 60.0)
                self._circuit_breakers[provider_type] = CircuitBreaker(threshold=threshold, cooldown_seconds=cooldown)
            return self._circuit_breakers[provider_type]

    def reload_configuration(self) -> None:
        """Reloads runtime configuration and clears resolution cache in a thread-safe manner."""
        with self._lock:
            logger.info("Reloading LLMManager runtime configuration...")
            self._refresh_cache_internal()

    def refresh_cache(self) -> None:
        """Public thread-safe cache refresh method."""
        with self._lock:
            self._refresh_cache_internal()

    def _refresh_cache_internal(self) -> None:
        """Internal cache builder (called with lock held)."""
        self._resolution_cache.clear()
        mode = self.get_execution_mode()
        base_map = self.DEFAULT_DEVELOPMENT_MAP if mode == ExecutionMode.DEVELOPMENT else self.DEFAULT_PRODUCTION_MAP
        primary_provider = self.get_default_provider_type()

        for agent in AgentType:
            env_override_key = f"{agent.value.upper()}_PROVIDER"
            env_override_val = os.getenv(env_override_key)

            if env_override_val:
                target_provider_type = ProviderType.from_str(env_override_val)
            else:
                target_provider_type = base_map.get(agent, primary_provider)

            try:
                provider_instance = self._registry.get(target_provider_type)
                self._resolution_cache[agent] = provider_instance
                logger.info(
                    f"Resolved strategy: Agent [{agent.value}] ➔ Provider [{target_provider_type.value}] (Mode: {mode.value})"
                )
            except Exception as e:
                logger.error(f"Failed to resolve provider for Agent [{agent.value}]: {e}")
                self._resolution_cache[agent] = self._registry.get(ProviderType.MOCK)

    def get_execution_mode(self) -> ExecutionMode:
        raw_mode = getattr(settings, "EXECUTION_MODE", None) or os.getenv("EXECUTION_MODE", "development")
        return ExecutionMode.from_str(raw_mode)

    def get_default_provider_type(self) -> ProviderType:
        raw_provider = getattr(settings, "PRIMARY_PROVIDER", None) or getattr(settings, "LLM_PROVIDER", None) or os.getenv("LLM_PROVIDER", "gemini")
        return ProviderType.from_str(raw_provider)

    def get_failover_chain(self) -> List[ProviderType]:
        """Builds configurable failover chain: PRIMARY ➔ SECONDARY ➔ TERTIARY ➔ FALLBACK."""
        chain = []
        for key in ["PRIMARY_PROVIDER", "SECONDARY_PROVIDER", "TERTIARY_PROVIDER", "FALLBACK_PROVIDER"]:
            val = getattr(settings, key, None) or os.getenv(key)
            if val:
                pt = ProviderType.from_str(val)
                if pt not in chain:
                    chain.append(pt)
        if ProviderType.MOCK not in chain:
            chain.append(ProviderType.MOCK)
        return chain

    def provider_for(self, agent_identifier: AgentType | str) -> BaseLLMProvider:
        agent_type = (
            agent_identifier
            if isinstance(agent_identifier, AgentType)
            else AgentType.from_str(str(agent_identifier))
        )

        with self._lock:
            if agent_type not in self._resolution_cache:
                self._refresh_cache_internal()
            preferred_provider = self._resolution_cache[agent_type]

        provider_type = preferred_provider.provider_type
        cb = self.get_circuit_breaker(provider_type)

        if not cb.allow_execution():
            logger.warning(
                f"Provider '{provider_type.value}' CircuitBreaker is OPEN. Triggering failover chain..."
            )
            return self._get_healthy_failover_provider(exclude=[provider_type])

        return preferred_provider

    def _get_healthy_failover_provider(self, exclude: List[ProviderType]) -> BaseLLMProvider:
        """Traverses configurable failover chain to find next healthy provider."""
        chain = self.get_failover_chain()
        for pt in chain:
            if pt in exclude:
                continue
            if self._registry.has(pt):
                cb = self.get_circuit_breaker(pt)
                if cb.allow_execution():
                    logger.info(f"Failover chain resolved healthy provider: [{pt.value}]")
                    return self._registry.get(pt)
        return self._registry.get(ProviderType.MOCK)

    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
        agent_identifier: Optional[AgentType | str] = None,
        provider_name: Optional[ProviderType | str] = None,
    ) -> str:
        if agent_identifier:
            provider = self.provider_for(agent_identifier)
        elif provider_name:
            provider = self._registry.get(provider_name)
        else:
            provider = self._registry.get(self.get_default_provider_type())

        provider_type = provider.provider_type
        cb = self.get_circuit_breaker(provider_type)

        try:
            res = await provider.generate_text(
                prompt=prompt,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
            cb.record_success()
            return res
        except LLMError as e:
            cb.record_failure()
            logger.error(f"LLM text generation error via provider {provider_type.value}: {e}")
            failover = self._get_healthy_failover_provider(exclude=[provider_type])
            return await failover.generate_text(prompt, temperature, max_output_tokens)

    async def generate_json(
        self,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        agent_identifier: Optional[AgentType | str] = None,
        provider_name: Optional[ProviderType | str] = None,
    ) -> Dict[str, Any]:
        if agent_identifier:
            provider = self.provider_for(agent_identifier)
        elif provider_name:
            provider = self._registry.get(provider_name)
        else:
            provider = self._registry.get(self.get_default_provider_type())

        provider_type = provider.provider_type
        cb = self.get_circuit_breaker(provider_type)

        try:
            res = await provider.generate_json(
                prompt=prompt,
                schema=schema,
            )
            cb.record_success()
            return res
        except LLMError as e:
            cb.record_failure()
            logger.error(f"LLM JSON generation error via provider {provider_type.value}: {e}")
            failover = self._get_healthy_failover_provider(exclude=[provider_type])
            return await failover.generate_json(prompt, schema)

    def get_metrics(self) -> Dict[str, Any]:
        metrics: Dict[str, Any] = {}
        for instance in self._registry.get_active_instances():
            pt = instance.provider_type
            cb = self.get_circuit_breaker(pt)
            metrics[pt.value] = {
                "metrics": instance.get_metrics(),
                "circuit_breaker": cb.to_dict(),
            }
        return metrics

    def get_prometheus_metrics(self) -> str:
        return PrometheusMetricsExporter.export(self.get_metrics())

    async def validate_all_providers(self) -> Dict[str, bool]:
        results = {}
        logger.info("Performing application startup validation of active LLM providers...")

        active_providers = self._registry.get_active_instances()
        if not active_providers:
            active_providers = [self._registry.get(self.get_default_provider_type())]

        for p in active_providers:
            pt = p.provider_type
            try:
                is_healthy = await p.health_check()
                results[pt.value] = is_healthy
                status = "HEALTHY ✅" if is_healthy else "UNHEALTHY ❌"
                logger.info(f"Startup LLM Provider Validation: [{pt.value}] -> {status}")
            except Exception as e:
                results[pt.value] = False
                logger.error(f"Startup validation failed for [{pt.value}]: {e}")

        return results


llm_manager = LLMManager()
