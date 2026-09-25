from typing import Any, Dict


class DiscoveryPrometheusExporter:
    """Prometheus TSDB Exporter for API Discovery Platform Telemetry Metrics."""

    @staticmethod
    def export_metrics(discovery_metrics: Dict[str, Any]) -> str:
        lines = [
            "# HELP api_discovery_requests_total Total number of API discovery queries executed.",
            "# TYPE api_discovery_requests_total counter",
            f'api_discovery_requests_total {discovery_metrics.get("total_queries", 0)}',
            "",
            "# HELP api_discovery_latency_average_ms Average API discovery query latency in milliseconds.",
            "# TYPE api_discovery_latency_average_ms gauge",
            f'api_discovery_latency_average_ms {discovery_metrics.get("avg_latency_ms", 0.0)}',
            "",
            "# HELP api_discovery_cache_hit_ratio Discovery query cache hit ratio.",
            "# TYPE api_discovery_cache_hit_ratio gauge",
            f'api_discovery_cache_hit_ratio {discovery_metrics.get("cache_hit_ratio", 1.0)}',
            "",
            "# HELP api_discovery_indexed_endpoints_total Total number of indexed API endpoints.",
            "# TYPE api_discovery_indexed_endpoints_total gauge",
            f'api_discovery_indexed_endpoints_total {discovery_metrics.get("indexed_endpoints", 0)}',
        ]
        return "\n".join(lines) + "\n"
