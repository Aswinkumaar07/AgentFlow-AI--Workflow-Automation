"""
Analytics Report Exporter for AgentFlow AI (AI-36).
Generates sanitized CSV and JSON downloadable reports.
Enforces zero secret leaks across all exported fields.
"""

import csv
import io
import json
from typing import Any, Dict
from app.runtime.execution_analytics import sanitize_telemetry_secrets


class AnalyticsExporter:
    """
    Report Export Engine.
    Converts sanitized execution telemetry into CSV and JSON exports.
    """

    @staticmethod
    def export_json(data: Dict[str, Any]) -> str:
        """
        Serializes sanitized analytics payload into pretty-printed JSON.
        """
        clean_data = sanitize_telemetry_secrets(data)
        return json.dumps(clean_data, indent=2)

    @staticmethod
    def export_csv(data: Dict[str, Any]) -> str:
        """
        Generates structured CSV report for executive metrics and execution records.
        """
        clean_data = sanitize_telemetry_secrets(data)
        summary = clean_data.get("summary", {})
        health = clean_data.get("health_score", {})
        node_stats = clean_data.get("node_statistics", [])
        provider_stats = clean_data.get("provider_statistics", [])
        error_trends = clean_data.get("error_trends", [])
        recent_execs = clean_data.get("recent_executions", [])

        output = io.StringIO()
        writer = csv.writer(output)

        # 1. Executive Summary Section
        writer.writerow(["=== EXECUTIVE SUMMARY ==="])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Executions", summary.get("total_executions", 0)])
        writer.writerow(["Successful Executions", summary.get("successful_executions", 0)])
        writer.writerow(["Failed Executions", summary.get("failed_executions", 0)])
        writer.writerow(["Success Rate (%)", summary.get("success_rate", "N/A")])
        writer.writerow(["Average Duration (ms)", summary.get("average_duration_ms", "N/A")])
        writer.writerow(["P50 Duration (ms)", summary.get("p50_duration_ms", "N/A")])
        writer.writerow(["P95 Duration (ms)", summary.get("p95_duration_ms", "N/A")])
        writer.writerow(["Total Retry Attempts", summary.get("total_retry_attempts", 0)])
        writer.writerow(["Health Score Status", health.get("status", "Healthy")])
        writer.writerow(["Health Score (%)", health.get("score", 100)])
        writer.writerow([])

        # 2. Provider Performance Section
        writer.writerow(["=== PROVIDER PERFORMANCE ==="])
        writer.writerow(["Provider", "Executions", "Success Rate (%)", "Avg Duration (ms)", "P50 (ms)", "P95 (ms)", "Retries"])
        for p in provider_stats:
            writer.writerow([
                p.get("provider"),
                p.get("execution_count"),
                p.get("success_rate"),
                p.get("average_duration_ms"),
                p.get("p50_duration_ms"),
                p.get("p95_duration_ms"),
                p.get("retries"),
            ])
        writer.writerow([])

        # 3. Node Performance Section
        writer.writerow(["=== NODE PERFORMANCE ==="])
        writer.writerow(["Node ID", "Provider", "Operation", "Executions", "Success Count", "Failure Count", "Avg Duration (ms)", "P50 (ms)", "P95 (ms)"])
        for n in node_stats:
            writer.writerow([
                n.get("node_id"),
                n.get("provider"),
                n.get("operation_id"),
                n.get("execution_count"),
                n.get("success_count"),
                n.get("failure_count"),
                n.get("average_duration_ms"),
                n.get("p50_duration_ms"),
                n.get("p95_duration_ms"),
            ])
        writer.writerow([])

        # 4. Error Category Trends
        writer.writerow(["=== ERROR CATEGORY TRENDS ==="])
        writer.writerow(["Category", "Count", "Percentage (%)", "Recent Occurrence"])
        for err in error_trends:
            writer.writerow([
                err.get("category"),
                err.get("count"),
                err.get("percentage"),
                err.get("recent_occurrence", ""),
            ])
        writer.writerow([])

        # 5. Recent Executions Log
        writer.writerow(["=== RECENT EXECUTIONS LOG ==="])
        writer.writerow(["Execution ID", "Status", "Trigger Type", "Version ID", "Duration (ms)", "Nodes Executed"])
        for ex in recent_execs:
            writer.writerow([
                ex.get("execution_id"),
                ex.get("status"),
                ex.get("trigger_type"),
                ex.get("version_id"),
                ex.get("duration_ms"),
                ex.get("nodes_executed"),
            ])

        return output.getvalue()


analytics_exporter = AnalyticsExporter()
