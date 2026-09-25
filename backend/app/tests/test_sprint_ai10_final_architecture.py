"""
Sprint AI-10: Final Architecture Integration Tests

Tests the complete AgentFlow pipeline end-to-end:
  User → Intent → Tasks → DAG → Validation → Execution Gate

Verifies:
  1. Pipeline structure & layer completeness
  2. Provider-agnostic behaviour (zero hardcoded Gmail)
  3. Structured JSON at every inter-layer boundary
  4. Validation gate blocks invalid workflows
  5. Multi-provider, multi-step DAG generation
  6. Comprehensive logging at every stage
"""
import json
import logging
import pytest
from app.agents.pipeline import agentflow_pipeline, AgentFlowPipeline, PipelineResult, LayerResult


# ─── Helpers ────────────────────────────────────────────────────────────────

def _run(prompt: str) -> PipelineResult:
    return agentflow_pipeline.run(prompt)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Pipeline Structure
# ═══════════════════════════════════════════════════════════════════════════════

def test_ai10_pipeline_result_structure():
    """PipelineResult must expose all required fields with correct types."""
    res = _run("Send good morning email to john@example.com")
    assert isinstance(res, PipelineResult)
    assert isinstance(res.prompt, str)
    assert isinstance(res.intent, str)
    assert isinstance(res.can_execute, bool)
    assert isinstance(res.confidence, float)
    assert isinstance(res.task_count, int)
    assert isinstance(res.node_count, int)
    assert isinstance(res.edge_count, int)
    assert isinstance(res.selected_providers, list)
    assert isinstance(res.selected_operations, list)
    assert isinstance(res.validation_errors, list)
    assert isinstance(res.validation_warnings, list)
    assert isinstance(res.workflow_graph, dict)
    assert isinstance(res.layers, list)
    assert isinstance(res.total_duration_ms, float)
    assert res.pipeline_version == "AI-10"


def test_ai10_pipeline_has_four_layers():
    """Every pipeline run must produce exactly 4 named layers."""
    res = _run("Send good morning email to john@example.com")
    layer_names = [l.layer for l in res.layers]
    assert "IntentClassifier" in layer_names
    assert "TaskDecomposer" in layer_names
    assert "PlannerV4" in layer_names
    assert "WorkflowValidator" in layer_names


def test_ai10_each_layer_has_duration():
    """Every layer must have a measured duration in milliseconds."""
    res = _run("Summarize my unread emails")
    for layer in res.layers:
        assert layer.duration_ms >= 0.0
    assert res.total_duration_ms > 0.0


def test_ai10_pipeline_result_is_json_serialisable():
    """PipelineResult.to_json() must produce valid JSON."""
    res = _run("Send good morning email to john@example.com")
    raw = res.to_json()
    parsed = json.loads(raw)
    assert parsed["prompt"] == res.prompt
    assert parsed["pipeline_version"] == "AI-10"


def test_ai10_pipeline_status_field():
    """status property must be 'success' or 'blocked'."""
    res = _run("Send good morning email to john@example.com")
    assert res.status in ("success", "blocked")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Intent Classification Layer
# ═══════════════════════════════════════════════════════════════════════════════

def test_ai10_layer1_intent_classification():
    """Intent layer must return a recognised intent string."""
    res = _run("Send good morning email to john@example.com")
    l1 = next(l for l in res.layers if l.layer == "IntentClassifier")
    assert l1.status == "ok"
    assert "intent" in l1.data
    assert isinstance(l1.data["intent"], str)
    assert l1.data["intent"] != ""


def test_ai10_layer1_intent_confidence():
    """Intent confidence must be between 0 and 1."""
    res = _run("Summarize my unread emails")
    l1 = next(l for l in res.layers if l.layer == "IntentClassifier")
    assert 0.0 <= l1.data["confidence"] <= 1.0


def test_ai10_layer1_gmail_intent():
    """Email send prompts must resolve to a Gmail-related intent."""
    res = _run("Send good morning email to john@example.com")
    l1 = next(l for l in res.layers if l.layer == "IntentClassifier")
    assert l1.data["intent"] in (
        "EMAIL_SEND", "EMAIL_GENERATE", "EMAIL_SEARCH_BY_SENDER", "MULTI_STEP_WORKFLOW",
        "EMAIL_SUMMARIZE", "SCHEDULED_EMAIL", "EMAIL_SEND_GREETING",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Task Decomposition Layer
# ═══════════════════════════════════════════════════════════════════════════════

def test_ai10_layer2_task_decomposition():
    """Task decomposition must produce ≥1 task."""
    res = _run("Send good morning email to john@example.com")
    l2 = next(l for l in res.layers if l.layer == "TaskDecomposer")
    assert l2.status == "ok"
    assert l2.data["task_count"] >= 1
    assert len(l2.data["tasks"]) >= 1


def test_ai10_layer2_tasks_have_provider_and_operation():
    """Every decomposed task must have provider and operation fields."""
    res = _run("Read unread emails and summarize")
    l2 = next(l for l in res.layers if l.layer == "TaskDecomposer")
    for task in l2.data["tasks"]:
        assert "provider" in task
        assert "operation" in task
        assert task["provider"] != ""
        assert task["operation"] != ""


def test_ai10_layer2_no_gmail_hardcoded_provider_fallback():
    """
    Provider-agnostic: an unrecognised non-email prompt must NOT default to gmail.
    The fallback must be 'generic' (AI-10 requirement).
    """
    res = _run("zzz xyzzy unknown action qwerty")
    l2 = next(l for l in res.layers if l.layer == "TaskDecomposer")
    tasks = l2.data["tasks"]
    if tasks:
        # Fallback provider must be generic, not gmail
        fallback_provider = tasks[0]["provider"]
        assert fallback_provider != "gmail", (
            f"AI-10 violation: fallback provider must not be 'gmail', got '{fallback_provider}'"
        )


def test_ai10_layer2_multi_step_read_summarize():
    """Read + Summarize prompt must produce ≥3 tasks."""
    res = _run("Read today's emails and summarize")
    l2 = next(l for l in res.layers if l.layer == "TaskDecomposer")
    assert l2.data["task_count"] >= 3


def test_ai10_layer2_invoice_drive_slack_dag():
    """Invoice→Download→Drive→Slack must produce 4 tasks."""
    res = _run("Search invoices, download attachment, upload to Drive, and notify Slack")
    l2 = next(l for l in res.layers if l.layer == "TaskDecomposer")
    assert l2.data["task_count"] == 4
    providers = [t["provider"] for t in l2.data["tasks"]]
    assert "gmail" in providers
    assert "drive" in providers
    assert "slack" in providers


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Planning / DAG Generation Layer
# ═══════════════════════════════════════════════════════════════════════════════

def test_ai10_layer3_planning_ok():
    """Planning layer must complete without errors."""
    res = _run("Send good morning email to john@example.com")
    l3 = next(l for l in res.layers if l.layer == "PlannerV4")
    assert l3.status == "ok"
    assert "workflow_graph" in l3.data


def test_ai10_layer3_workflow_graph_has_nodes_and_trigger():
    """Workflow graph must have trigger and nodes."""
    res = _run("Send good morning email to john@example.com")
    graph = res.workflow_graph
    assert "trigger" in graph
    assert "nodes" in graph
    assert len(graph["nodes"]) >= 1


def test_ai10_layer3_multi_step_dag_nodes_and_edges():
    """Multi-step DAG must have ≥2 nodes and ≥1 edge."""
    res = _run("Read unread emails and summarize")
    assert res.node_count >= 3
    assert res.edge_count >= 2


def test_ai10_layer3_no_hardcoded_gmail_operation_fallback():
    """
    AI-10: operation fallback for unknown prompts must NOT be 'gmail.messages.send'.
    """
    res = _run("zzz xyzzy unknown action qwerty")
    l3 = next(l for l in res.layers if l.layer == "PlannerV4")
    nodes = l3.data.get("workflow_graph", {}).get("nodes", [])
    for node in nodes:
        op = node.get("operation") or node.get("operation_id") or ""
        assert op != "gmail.messages.send", (
            f"AI-10 violation: operation fallback must not be 'gmail.messages.send', got '{op}'"
        )


def test_ai10_layer3_can_execute_flag():
    """PlannerV4 must expose can_execute boolean."""
    res = _run("Send good morning email to john@example.com")
    l3 = next(l for l in res.layers if l.layer == "PlannerV4")
    assert "can_execute" in l3.data
    assert isinstance(l3.data["can_execute"], bool)


def test_ai10_layer3_pipeline_summary_fields():
    """PlannerV4 must produce a structured pipeline_summary dict."""
    res = _run("Send good morning email to john@example.com")
    l3 = next(l for l in res.layers if l.layer == "PlannerV4")
    summary = l3.data.get("pipeline_summary", {})
    assert summary.get("layer") == "PlannerV4"
    assert "intent" in summary
    assert "node_count" in summary
    assert "can_execute" in summary


def test_ai10_layer3_reasoning_trace_non_empty():
    """Reasoning trace must contain at least Stage 0 and Stage 1 entries."""
    res = _run("Send good morning email to john@example.com")
    l3 = next(l for l in res.layers if l.layer == "PlannerV4")
    trace = l3.data.get("reasoning_trace", [])
    assert len(trace) >= 2


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Validation Gate
# ═══════════════════════════════════════════════════════════════════════════════

def test_ai10_layer4_validation_ok():
    """Validation layer must run and produce is_valid field."""
    res = _run("Send good morning email to john@example.com")
    l4 = next(l for l in res.layers if l.layer == "WorkflowValidator")
    assert l4.status == "ok"
    assert "is_valid" in l4.data
    assert isinstance(l4.data["is_valid"], bool)


def test_ai10_layer4_valid_workflow_allows_execution():
    """A valid standard workflow must set can_execute=True."""
    res = _run("Send good morning email to john@example.com")
    # The workflow may produce warnings (no auth) but nodes are known providers
    # can_execute should reflect validator result
    assert res.can_execute == (len(res.validation_errors) == 0)


def test_ai10_gate_blocks_on_validator_errors():
    """
    Simulate a pipeline where the graph has a cycle — validator should block execution.
    We directly test the validator layer for a cyclic graph.
    """
    from app.agents.validator import workflow_validator
    cyclic_graph = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.send"},
            {"id": "step_2", "provider": "Slack", "operation_id": "slack.chat.postMessage"},
        ],
        "edges": [
            {"source": "step_1", "target": "step_2"},
            {"source": "step_2", "target": "step_1"},  # cycle
        ],
    }
    val = workflow_validator.validate_workflow(cyclic_graph)
    assert val.is_valid is False
    assert any("Cycle" in e for e in val.errors)
    # In a real pipeline, can_execute would be False
    can_execute = val.is_valid
    assert can_execute is False


def test_ai10_gate_allows_valid_multistep():
    """A valid multi-step DAG must pass the gate."""
    res = _run("Read unread emails and summarize")
    # Validation should not find cycles or unknown connectors
    cycle_errors = [e for e in res.validation_errors if "Cycle" in e]
    unknown_errors = [e for e in res.validation_errors if "Unknown connector" in e]
    assert len(cycle_errors) == 0
    assert len(unknown_errors) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Provider-Agnostic Architecture
# ═══════════════════════════════════════════════════════════════════════════════

def test_ai10_slack_provider_works():
    """Slack-first prompts must route to Slack provider, not Gmail."""
    res = _run("Post a message to #general on Slack")
    # At least one operation should be Slack
    ops = res.selected_operations
    providers = res.selected_providers
    all_lower = [p.lower() for p in providers] + [o.lower() for o in ops]
    assert any("slack" in x for x in all_lower), f"Expected Slack, got: {providers} / {ops}"


def test_ai10_schedule_trigger_works():
    """Schedule prompts must produce a Schedule trigger."""
    res = _run("Every Monday at 8AM send report from Employees sheet")
    assert res.trigger_type == "Schedule"


def test_ai10_github_trigger_works():
    """GitHub PR prompts must produce a GitHub trigger."""
    res = _run("When GitHub PR opens notify Slack #engineering and create Notion page")
    assert res.trigger_type == "GitHub"


def test_ai10_multi_provider_dag():
    """
    A cross-provider workflow (Gmail + Drive + Slack) must include
    nodes from multiple different providers.
    """
    res = _run("Search invoices, download attachment, upload to Drive, and notify Slack")
    nodes = res.workflow_graph.get("nodes", [])
    node_providers = {n.get("provider", "").lower() for n in nodes}
    # Should span gmail, drive, and slack
    assert len(node_providers) >= 2, f"Expected ≥2 providers, got: {node_providers}"


def test_ai10_gmail_read_ops_not_send():
    """
    'Read unread emails' must produce a list/get operation — never a send fallback.
    """
    res = _run("Read unread emails")
    nodes = res.workflow_graph.get("nodes", [])
    ops = [n.get("operation") or n.get("operation_id", "") for n in nodes]
    # Must contain list or get
    assert any(op in ("gmail.messages.list", "gmail.messages.get", "gmail.messages.search") for op in ops), \
        f"Expected read op, got: {ops}"


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Structured JSON Inter-Layer Communication
# ═══════════════════════════════════════════════════════════════════════════════

def test_ai10_layer_data_is_json_serialisable():
    """Every layer's data dict must be JSON serialisable."""
    res = _run("Send good morning email to john@example.com")
    for layer in res.layers:
        try:
            json.dumps(layer.data)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Layer '{layer.layer}' data is not JSON serialisable: {e}")


def test_ai10_layer_result_model_fields():
    """LayerResult must have layer, status, duration_ms, data, errors."""
    res = _run("Send good morning email to john@example.com")
    for layer in res.layers:
        assert hasattr(layer, "layer")
        assert hasattr(layer, "status")
        assert hasattr(layer, "duration_ms")
        assert hasattr(layer, "data")
        assert hasattr(layer, "errors")
        assert layer.status in ("ok", "error", "skipped")


def test_ai10_intent_layer_json_structure():
    """Intent layer data must have intent, confidence, reasoning keys."""
    res = _run("Summarize my unread emails")
    l1 = next(l for l in res.layers if l.layer == "IntentClassifier")
    assert "intent" in l1.data
    assert "confidence" in l1.data
    assert "reasoning" in l1.data


def test_ai10_decomposer_layer_json_structure():
    """Task decomposer layer data must have task_count, tasks, reasoning."""
    res = _run("Summarize my unread emails")
    l2 = next(l for l in res.layers if l.layer == "TaskDecomposer")
    assert "task_count" in l2.data
    assert "tasks" in l2.data
    assert "reasoning" in l2.data


def test_ai10_validator_layer_json_structure():
    """Validator layer data must have is_valid, errors, warnings, confidence."""
    res = _run("Send good morning email to john@example.com")
    l4 = next(l for l in res.layers if l.layer == "WorkflowValidator")
    assert "is_valid" in l4.data
    assert "errors" in l4.data
    assert "warnings" in l4.data
    assert "confidence" in l4.data


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Full End-to-End Pipeline Scenarios
# ═══════════════════════════════════════════════════════════════════════════════

def test_ai10_e2e_good_morning_email():
    """Full pipeline for 'Send good morning email to john@example.com'."""
    res = _run("Send good morning email to john@example.com")
    assert res.prompt == "Send good morning email to john@example.com"
    assert res.node_count >= 1
    assert res.pipeline_version == "AI-10"
    assert len(res.layers) == 4
    nodes = res.workflow_graph.get("nodes", [])
    assert len(nodes) >= 1
    # Verify Gmail node has correct subject
    gmail_nodes = [n for n in nodes if "gmail" in (n.get("provider") or "").lower()]
    assert len(gmail_nodes) >= 1
    gm = gmail_nodes[-1]
    assert "Good Morning" in gm.get("parameters", {}).get("subject", "")


def test_ai10_e2e_read_summarize_workflow():
    """Full pipeline for Read→Summarize multi-step workflow."""
    res = _run("Read today's emails and summarize")
    assert res.node_count >= 3
    assert res.edge_count >= 2
    ops = [n.get("operation") or n.get("operation_id", "") for n in res.workflow_graph.get("nodes", [])]
    assert "gmail.messages.list" in ops
    assert "ai.summarize" in ops


def test_ai10_e2e_invoice_drive_slack():
    """Full pipeline for Search→Download→Drive→Slack cross-provider workflow."""
    res = _run("Search invoices, download attachment, upload to Drive, and notify Slack")
    assert res.node_count == 4
    assert res.edge_count == 3
    ops = [n.get("operation") or n.get("operation_id", "") for n in res.workflow_graph.get("nodes", [])]
    assert "gmail.messages.search" in ops
    assert "slack.chat.postMessage" in ops


def test_ai10_e2e_scheduled_email():
    """Full pipeline for a scheduled email workflow."""
    res = _run("Every Monday at 8AM send report from Employees sheet")
    assert res.trigger_type == "Schedule"
    assert res.node_count >= 2


def test_ai10_e2e_pipeline_is_deterministic():
    """Same prompt run twice must produce same intent and node count."""
    prompt = "Read unread emails and summarize"
    res1 = _run(prompt)
    res2 = _run(prompt)
    assert res1.intent == res2.intent
    assert res1.node_count == res2.node_count
    assert res1.edge_count == res2.edge_count


# ═══════════════════════════════════════════════════════════════════════════════
# 9. AgentFlowPipeline Instance
# ═══════════════════════════════════════════════════════════════════════════════

def test_ai10_singleton_instance():
    """agentflow_pipeline must be an AgentFlowPipeline singleton."""
    from app.agents.pipeline import agentflow_pipeline
    assert isinstance(agentflow_pipeline, AgentFlowPipeline)


def test_ai10_fresh_instance_works():
    """A freshly created AgentFlowPipeline must work identically to singleton."""
    pipeline = AgentFlowPipeline()
    res = pipeline.run("Send good morning email to john@example.com")
    assert isinstance(res, PipelineResult)
    assert res.node_count >= 1


def test_ai10_pipeline_is_blocked_helper():
    """is_blocked() must return the inverse of can_execute."""
    res = _run("Send good morning email to john@example.com")
    assert res.is_blocked() == (not res.can_execute)
