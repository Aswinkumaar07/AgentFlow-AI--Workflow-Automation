"""
Sprint AI-10: AgentFlow Final Architecture Pipeline

Full end-to-end orchestrator:

  User Prompt
    ↓
  [Layer 1] EnterpriseIntentClassifier   → IntentResult (JSON)
    ↓
  [Layer 2] EnterpriseTaskDecomposer     → TaskDecompositionResult (JSON)
    ↓
  [Layer 3] IntelligentPlannerV4         → PlanningResultV4 (JSON)
    ↓
  [Layer 4] WorkflowValidator            → ValidationResult (JSON)
    ↓
  [GATE]    can_execute?
     ↓ YES                               ↓ NO
  PipelineResult (success)           PipelineResult (blocked, errors)

Provider-agnostic: zero hardcoded Gmail send fallback.
Structured JSON at every inter-layer boundary.
"""
import json
import logging
import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("agentflow.pipeline")


# ─── Inter-layer data models ────────────────────────────────────────────────

class LayerResult(BaseModel):
    """Structured JSON envelope passed between pipeline layers."""
    layer: str
    status: str = "ok"          # ok | error | skipped
    duration_ms: float = 0.0
    data: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)


class PipelineResult(BaseModel):
    """
    Final structured result returned by AgentFlowPipeline.
    Every field is serialisable to JSON for frontend/API consumption.
    """
    # Core pipeline fields
    prompt: str
    intent: str = ""
    can_execute: bool = False
    confidence: float = 0.0

    # Layer outputs
    task_count: int = 0
    node_count: int = 0
    edge_count: int = 0
    selected_providers: List[str] = Field(default_factory=list)
    selected_operations: List[str] = Field(default_factory=list)
    trigger_type: str = "Manual"

    # Validation
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)

    # Full workflow graph for execution
    workflow_graph: Dict[str, Any] = Field(default_factory=dict)

    # Planning result with full reasoning trace
    planning_result: Optional[Dict[str, Any]] = None

    # Per-layer structured results
    layers: List[LayerResult] = Field(default_factory=list)

    # Pipeline metadata
    total_duration_ms: float = 0.0
    pipeline_version: str = "AI-10"

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    def is_blocked(self) -> bool:
        return not self.can_execute

    @property
    def status(self) -> str:
        return "success" if self.can_execute else "blocked"

    def to_frontend_response(self) -> Dict[str, Any]:
        """
        Sprint AI-11: Frontend contract API response dictionary.
        Format consumed by React frontend:
        {
            "success": true,
            "workflow": { "trigger": {}, "nodes": [], "edges": [] },
            "intent": { "name": "...", "confidence": 0.98 },
            "validation": { "is_valid": true, "errors": [], "warnings": [] },
            "can_execute": true
        }
        """
        return {
            "success": self.can_execute,
            "error_code": None if self.can_execute else "INTENT_UNRESOLVED",
            "message": "Workflow generated successfully" if self.can_execute else "Unable to determine the requested operation.",
            "workflow": {
                "trigger": self.workflow_graph.get("trigger", {}),
                "nodes": self.workflow_graph.get("nodes", []),
                "edges": self.workflow_graph.get("edges", []),
            },
            "intent": {
                "name": self.intent,
                "confidence": self.confidence,
            },
            "validation": {
                "is_valid": self.can_execute,
                "errors": self.validation_errors,
                "warnings": self.validation_warnings,
            },
            "can_execute": self.can_execute,
        }


# ─── Pipeline orchestrator ───────────────────────────────────────────────────

class AgentFlowPipeline:
    """
    Sprint AI-10: Central AgentFlow orchestrator.

    Wires all AI layers into a single callable pipeline.
    Enforces the validation gate before allowing execution.
    Emits structured JSON at every layer boundary.
    """

    def run(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> PipelineResult:
        """
        Execute the full AgentFlow pipeline for a user prompt.

        Returns a PipelineResult with:
        - can_execute: True if validation passes
        - workflow_graph: fully executable DAG
        - layers: per-layer timing + structured JSON output
        - validation_errors / warnings
        """
        pipeline_start = time.perf_counter()
        layers: List[LayerResult] = []
        logger.info(f"[AI-10][PIPELINE] Starting pipeline for prompt: '{prompt}'")

        # ── Layer 1: Intent Classification ──────────────────────────────────
        l1_result = self._run_intent_classification(prompt)
        layers.append(l1_result)
        intent = l1_result.data.get("intent", "UNKNOWN")
        intent_confidence = l1_result.data.get("confidence", 0.0)

        # ── Layer 2: Task Decomposition ──────────────────────────────────────
        l2_result = self._run_task_decomposition(prompt, intent)
        layers.append(l2_result)
        tasks = l2_result.data.get("tasks", [])

        # ── Layer 3: Planning (DAG Generation) ──────────────────────────────
        l3_result = self._run_planning(prompt, context)
        layers.append(l3_result)
        plan_data = l3_result.data
        workflow_graph = plan_data.get("workflow_graph", {})
        workflow_graph["intent"] = intent

        # ── Layer 4: Validation Gate ─────────────────────────────────────────
        l4_result = self._run_validation(workflow_graph)
        layers.append(l4_result)
        can_execute = l4_result.data.get("is_valid", False)
        val_errors = l4_result.data.get("errors", [])
        val_warnings = l4_result.data.get("warnings", [])

        # ── Final Result Assembly ────────────────────────────────────────────
        total_ms = (time.perf_counter() - pipeline_start) * 1000

        workflow_graph = plan_data.get("workflow_graph", {})
        nodes = workflow_graph.get("nodes", [])
        edges = workflow_graph.get("edges", [])

        result = PipelineResult(
            prompt=prompt,
            intent=intent,
            can_execute=can_execute,
            confidence=plan_data.get("confidence", intent_confidence),
            task_count=len(tasks),
            node_count=len(nodes),
            edge_count=len(edges),
            selected_providers=plan_data.get("selected_connectors", []),
            selected_operations=plan_data.get("selected_operations", []),
            trigger_type=workflow_graph.get("trigger", {}).get("type", "Manual"),
            validation_errors=val_errors,
            validation_warnings=val_warnings,
            workflow_graph=workflow_graph,
            planning_result=plan_data,
            layers=layers,
            total_duration_ms=round(total_ms, 2),
        )

        # Structured JSON summary log
        summary = {
            "pipeline": "AgentFlow-AI-10",
            "prompt": prompt,
            "intent": intent,
            "task_count": result.task_count,
            "node_count": result.node_count,
            "edge_count": result.edge_count,
            "providers": result.selected_providers,
            "can_execute": can_execute,
            "status": result.status,
            "total_duration_ms": result.total_duration_ms,
            "validation_errors": val_errors,
        }
        logger.info(f"[AI-10][PIPELINE][JSON] {json.dumps(summary)}")

        if can_execute:
            logger.info(f"[AI-10][GATE] ✅ Execution ALLOWED — {result.node_count} nodes ready")
        else:
            logger.warning(f"[AI-10][GATE] 🚫 Execution BLOCKED — {len(val_errors)} error(s): {val_errors}")

        return result

    # ── Private layer runners ────────────────────────────────────────────────

    def _run_intent_classification(self, prompt: str) -> LayerResult:
        t0 = time.perf_counter()
        try:
            from app.agents.intent_classifier import enterprise_intent_classifier
            res = enterprise_intent_classifier.classify(prompt)
            data = {
                "intent": res.intent.value,
                "confidence": res.confidence,
                "reasoning": res.reasoning,
                "entities": res.entities,
            }
            logger.info(
                f"[AI-10][L1][JSON] {json.dumps({'layer': 'IntentClassifier', **data})}"
            )
            return LayerResult(
                layer="IntentClassifier",
                status="ok",
                duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                data=data,
            )
        except Exception as exc:
            logger.error(f"[AI-10][L1] IntentClassifier error: {exc}")
            return LayerResult(
                layer="IntentClassifier", status="error",
                duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                data={"intent": "UNKNOWN", "confidence": 0.0},
                errors=[str(exc)],
            )

    def _run_task_decomposition(self, prompt: str, intent: str) -> LayerResult:
        t0 = time.perf_counter()
        try:
            from app.agents.task_decomposer import enterprise_task_decomposer
            res = enterprise_task_decomposer.decompose(prompt, intent=intent)
            tasks_data = [
                {"step": t.step, "name": t.name, "provider": t.provider, "operation": t.operation}
                for t in res.tasks
            ]
            data = {
                "task_count": len(res.tasks),
                "tasks": tasks_data,
                "reasoning": res.reasoning,
            }
            logger.info(
                f"[AI-10][L2][JSON] {json.dumps({'layer': 'TaskDecomposer', **data})}"
            )
            return LayerResult(
                layer="TaskDecomposer",
                status="ok",
                duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                data=data,
            )
        except Exception as exc:
            logger.error(f"[AI-10][L2] TaskDecomposer error: {exc}")
            return LayerResult(
                layer="TaskDecomposer", status="error",
                duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                data={"task_count": 0, "tasks": []},
                errors=[str(exc)],
            )

    def _run_planning(self, prompt: str, context: Optional[Dict[str, Any]]) -> LayerResult:
        t0 = time.perf_counter()
        try:
            from app.agents.planner.planner_v4 import intelligent_planner_v4
            plan = intelligent_planner_v4.plan(prompt, context=context)
            data = {
                "intent": plan.intent,
                "selected_connectors": plan.selected_connectors,
                "selected_operations": plan.selected_operations,
                "workflow_graph": plan.workflow_graph,
                "confidence": plan.confidence,
                "can_execute": plan.can_execute,
                "validation_errors": plan.validation_errors,
                "validation_warnings": plan.validation_warnings,
                "reasoning_trace": plan.reasoning_trace,
                "pipeline_summary": plan.pipeline_summary,
            }
            logger.info(
                f"[AI-10][L3][JSON] {json.dumps({'layer': 'PlannerV4', 'intent': plan.intent, 'node_count': len(plan.workflow_graph.get('nodes', [])), 'can_execute': plan.can_execute})}"
            )
            return LayerResult(
                layer="PlannerV4",
                status="ok",
                duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                data=data,
            )
        except Exception as exc:
            logger.error(f"[AI-10][L3] PlannerV4 error: {exc}")
            return LayerResult(
                layer="PlannerV4", status="error",
                duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                data={"workflow_graph": {}, "confidence": 0.0, "can_execute": False},
                errors=[str(exc)],
            )

    def _run_validation(self, workflow_graph: Dict[str, Any]) -> LayerResult:
        t0 = time.perf_counter()
        try:
            from app.agents.validator import workflow_validator
            res = workflow_validator.validate_workflow(workflow_graph)
            data = {
                "is_valid": res.is_valid,
                "errors": res.errors,
                "warnings": res.warnings,
                "suggestions": res.suggestions,
                "confidence": res.confidence,
            }
            logger.info(
                f"[AI-10][L4][JSON] {json.dumps({'layer': 'WorkflowValidator', 'is_valid': res.is_valid, 'errors': res.errors})}"
            )
            return LayerResult(
                layer="WorkflowValidator",
                status="ok",
                duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                data=data,
            )
        except Exception as exc:
            logger.error(f"[AI-10][L4] WorkflowValidator error: {exc}")
            return LayerResult(
                layer="WorkflowValidator", status="error",
                duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                data={"is_valid": False, "errors": [str(exc)], "warnings": []},
                errors=[str(exc)],
            )


# Singleton instance
agentflow_pipeline = AgentFlowPipeline()
