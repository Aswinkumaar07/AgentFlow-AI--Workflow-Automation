from typing import Any, Dict


class PrometheusMetricsExporter:
    """Prometheus TSDB Exporter for LLM Provider metrics and circuit breaker telemetry."""

    @staticmethod
    def export(metrics_data: Dict[str, Any]) -> str:
        """Converts LLMManager.get_metrics() dictionary into Prometheus text format.

        Args:
            metrics_data: Dictionary returned by llm_manager.get_metrics().

        Returns:
            Prometheus text format string.
        """
        lines = [
            "# HELP llm_requests_total Total number of LLM requests made per provider.",
            "# TYPE llm_requests_total counter",
        ]

        for provider, info in metrics_data.items():
            m = info.get("metrics", {})
            cb = info.get("circuit_breaker", {})
            provider_label = provider.lower()

            lines.append(f'llm_requests_total{{provider="{provider_label}",status="success"}} {m.get("success_count", 0)}')
            lines.append(f'llm_requests_total{{provider="{provider_label}",status="failure"}} {m.get("failure_count", 0)}')

        lines.extend([
            "",
            "# HELP llm_latency_average_ms Average execution latency in milliseconds per provider.",
            "# TYPE llm_latency_average_ms gauge",
        ])
        for provider, info in metrics_data.items():
            m = info.get("metrics", {})
            provider_label = provider.lower()
            lines.append(f'llm_latency_average_ms{{provider="{provider_label}"}} {m.get("average_latency_ms", 0.0)}')

        lines.extend([
            "",
            "# HELP llm_estimated_tokens_total Total estimated tokens consumed per provider.",
            "# TYPE llm_estimated_tokens_total counter",
        ])
        for provider, info in metrics_data.items():
            m = info.get("metrics", {})
            provider_label = provider.lower()
            lines.append(f'llm_estimated_tokens_total{{provider="{provider_label}"}} {m.get("estimated_token_usage", 0)}')

        lines.extend([
            "",
            "# HELP llm_circuit_breaker_state Circuit breaker state (0=CLOSED, 1=HALF_OPEN, 2=OPEN).",
            "# TYPE llm_circuit_breaker_state gauge",
        ])
        state_map = {"CLOSED": 0, "HALF_OPEN": 1, "OPEN": 2}
        for provider, info in metrics_data.items():
            cb = info.get("circuit_breaker", {})
            provider_label = provider.lower()
            st_val = state_map.get(cb.get("state", "CLOSED"), 0)
            lines.append(f'llm_circuit_breaker_state{{provider="{provider_label}"}} {st_val}')

        return "\n".join(lines) + "\n"
