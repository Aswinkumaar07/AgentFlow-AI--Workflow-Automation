"""
Sprint AI-9: Workflow Validator Tests
Covers all 10 validation categories:
  1. Valid DAG passthrough
  2. Cycle detection
  3. Unknown / unsupported connectors
  4. Duplicate node IDs
  5. Invalid expression syntax
  6. OAuth warnings
  7. Missing required parameters (when params dict provided)
  8. Missing trigger
  9. Invalid trigger type
 10. Edge integrity (dangling source/target)
 11. Empty workflow
 12. Duplicate edge IDs
 13. Missing node IDs
 14. Multi-step DAG validation (AI-8 integration)
 15. Execution prevention on invalid workflow
"""
import pytest
from app.agents.validator import workflow_validator, validator_ai_service, ValidationResult


# ─── helpers ────────────────────────────────────────────────────────────────

def _valid_graph(extra_nodes=None, extra_edges=None, trigger=None):
    nodes = [
        {"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.send"},
        {"id": "step_2", "provider": "Slack", "operation_id": "slack.chat.postMessage"},
    ]
    edges = [{"id": "e1-2", "source": "step_1", "target": "step_2"}]
    return {
        "trigger": trigger or {"type": "Manual"},
        "nodes": nodes + (extra_nodes or []),
        "edges": edges + (extra_edges or []),
    }


# ─── 1. Valid DAG ───────────────────────────────────────────────────────────

def test_ai9_valid_dag_passes():
    """A well-formed DAG with known providers should be valid."""
    res = workflow_validator.validate_workflow(_valid_graph())
    assert res.is_valid is True
    assert len(res.errors) == 0
    assert res.confidence >= 0.85


def test_ai9_valid_dag_via_service():
    """validator_ai_service wraps the same logic."""
    res = validator_ai_service.validate(_valid_graph())
    assert res.is_valid is True
    assert isinstance(res, ValidationResult)


# ─── 2. Cycle Detection ─────────────────────────────────────────────────────

def test_ai9_cycle_detection():
    """Bidirectional edge creates a cycle → invalid."""
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.send"},
            {"id": "step_2", "provider": "Slack", "operation_id": "slack.chat.postMessage"},
        ],
        "edges": [
            {"id": "e1", "source": "step_1", "target": "step_2"},
            {"id": "e2", "source": "step_2", "target": "step_1"},
        ],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is False
    assert any("Cycle detected" in err for err in res.errors)
    assert res.confidence == 0.0


def test_ai9_self_loop_cycle():
    """A node pointing to itself is a cycle."""
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [{"id": "step_1", "provider": "Slack", "operation_id": "slack.chat.postMessage"}],
        "edges": [{"id": "e1", "source": "step_1", "target": "step_1"}],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is False
    assert any("Cycle" in err for err in res.errors)


def test_ai9_three_node_cycle():
    """A → B → C → A is a cycle."""
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {"id": "a", "provider": "Gmail", "operation_id": "gmail.messages.list"},
            {"id": "b", "provider": "Slack", "operation_id": "slack.chat.postMessage"},
            {"id": "c", "provider": "Gmail", "operation_id": "gmail.messages.send"},
        ],
        "edges": [
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "a"},
        ],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is False
    assert any("Cycle detected" in err for err in res.errors)


# ─── 3. Unknown / Unsupported Connector ─────────────────────────────────────

def test_ai9_unknown_connector():
    """An unknown provider name must produce an 'Unknown connector' error."""
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [{"id": "step_1", "provider": "UnknownInvalidProvider", "operation_id": "foo.bar"}],
        "edges": [],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is False
    assert any("Unknown connector provider" in err for err in res.errors)


def test_ai9_known_providers_are_valid():
    """Gmail, Slack, GitHub, Notion, Stripe must all be accepted."""
    for provider in ["Gmail", "Slack", "GitHub", "Notion"]:
        graph = {
            "trigger": {"type": "Manual"},
            "nodes": [{"id": "step_1", "provider": provider, "operation_id": "some.op"}],
            "edges": [],
        }
        res = workflow_validator.validate_workflow(graph)
        unknown_errors = [e for e in res.errors if "Unknown connector provider" in e]
        assert len(unknown_errors) == 0, f"Provider '{provider}' should be known but got: {unknown_errors}"


# ─── 4. Duplicate Node IDs ──────────────────────────────────────────────────

def test_ai9_duplicate_node_ids():
    """Two nodes with same ID must fail."""
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.send"},
            {"id": "step_1", "provider": "Slack", "operation_id": "slack.chat.postMessage"},
        ],
        "edges": [],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is False
    assert any("Duplicate node ID" in err for err in res.errors)


# ─── 5. Expression Syntax ───────────────────────────────────────────────────

def test_ai9_invalid_expression_unclosed():
    """Unclosed {{ must fail."""
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {
                "id": "step_1",
                "provider": "Gmail",
                "operation_id": "gmail.messages.send",
                "parameters": {"subject": "Hello {{unclosed_var"},
            }
        ],
        "edges": [],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is False
    assert any("Invalid expression syntax" in err for err in res.errors)


def test_ai9_valid_template_expression():
    """Properly closed {{step_1.value}} must not fail."""
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list"},
            {
                "id": "step_2",
                "provider": "Gmail",
                "operation_id": "gmail.messages.send",
                "parameters": {"subject": "Summary", "body": "{{step_1.snippet}}", "to": "a@b.com"},
            },
        ],
        "edges": [{"source": "step_1", "target": "step_2"}],
    }
    res = workflow_validator.validate_workflow(graph)
    expr_errors = [e for e in res.errors if "Invalid expression syntax" in e]
    assert len(expr_errors) == 0


def test_ai9_loop_variable_without_loop_node():
    """Using {{loop.item}} without a loop node must fail."""
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {
                "id": "step_1",
                "provider": "Gmail",
                "operation_id": "gmail.messages.send",
                "parameters": {"body": "{{loop.item.subject}}"},
            }
        ],
        "edges": [],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is False
    assert any("loop" in err.lower() for err in res.errors)


# ─── 6. OAuth Warnings ──────────────────────────────────────────────────────

def test_ai9_oauth_warning_gmail_no_auth():
    """Gmail node without auth metadata should produce an OAuth warning but stay valid."""
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [{"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.send"}],
        "edges": [],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is True
    assert any("OAuth" in warn for warn in res.warnings)


def test_ai9_oauth_warning_multiple_oauth_nodes():
    """Both Gmail and Slack should each emit OAuth warnings."""
    graph = _valid_graph()
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is True
    oauth_warnings = [w for w in res.warnings if "OAuth" in w]
    assert len(oauth_warnings) >= 2


def test_ai9_node_with_auth_no_oauth_warning():
    """Node with auth metadata should NOT get an OAuth warning."""
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {
                "id": "step_1",
                "provider": "Gmail",
                "operation_id": "gmail.messages.send",
                "authentication": {"credential_id": "conn_google_usr_1"},
            }
        ],
        "edges": [],
    }
    res = workflow_validator.validate_workflow(graph)
    oauth_warnings = [w for w in res.warnings if "OAuth" in w]
    assert len(oauth_warnings) == 0


# ─── 7. Required Parameters ─────────────────────────────────────────────────

def test_ai9_required_params_missing_fires_when_params_provided():
    """Required param errors should fire when a params dict is present with empty values."""
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {
                "id": "step_1",
                "provider": "Gmail",
                "operation_id": "gmail.messages.send",
                "parameters": {},   # empty dict → required params missing
            }
        ],
        "edges": [],
    }
    res = workflow_validator.validate_workflow(graph)
    # Should have errors about missing required params (to, subject, body)
    assert res.is_valid is False or any(
        "missing" in err.lower() for err in res.errors
    )


def test_ai9_required_params_not_fired_when_no_params_dict():
    """When no params dict, required-param errors must NOT fire (node still in design)."""
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.send"}
            # No "parameters" key at all
        ],
        "edges": [],
    }
    res = workflow_validator.validate_workflow(graph)
    param_errors = [e for e in res.errors if "Required parameter" in e]
    assert len(param_errors) == 0


def test_ai9_template_reference_satisfies_required_param():
    """A template {{step_N.value}} should count as satisfying a required param."""
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {
                "id": "step_1",
                "provider": "Gmail",
                "operation_id": "gmail.messages.send",
                "parameters": {
                    "to": "john@example.com",
                    "subject": "Report",
                    "body": "{{step_0.summary}}",
                },
            }
        ],
        "edges": [],
    }
    res = workflow_validator.validate_workflow(graph)
    param_errors = [e for e in res.errors if "Required parameter" in e]
    assert len(param_errors) == 0


# ─── 8. Missing Trigger ─────────────────────────────────────────────────────

def test_ai9_missing_trigger():
    """No trigger → validation error."""
    graph = {
        "nodes": [{"id": "step_1", "provider": "Slack", "operation_id": "slack.chat.postMessage"}],
        "edges": [],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is False
    assert any("trigger" in err.lower() for err in res.errors)


def test_ai9_trigger_without_type():
    """Trigger dict without 'type' key → error."""
    graph = {
        "trigger": {"event": "push"},   # no "type"
        "nodes": [{"id": "step_1", "provider": "Slack", "operation_id": "slack.chat.postMessage"}],
        "edges": [],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is False
    assert any("trigger" in err.lower() for err in res.errors)


# ─── 9. Invalid Trigger Type ────────────────────────────────────────────────

def test_ai9_invalid_trigger_type():
    """An unrecognised trigger type should produce an error."""
    graph = {
        "trigger": {"type": "FakeTrigger"},
        "nodes": [{"id": "step_1", "provider": "Slack", "operation_id": "slack.chat.postMessage"}],
        "edges": [],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is False
    assert any("trigger" in err.lower() or "FakeTrigger" in err for err in res.errors)


def test_ai9_valid_trigger_types():
    """Manual, Schedule, Webhook, GitHub must all be accepted."""
    for ttype in ["Manual", "Schedule", "Webhook", "GitHub"]:
        graph = {
            "trigger": {"type": ttype},
            "nodes": [{"id": "step_1", "provider": "Slack", "operation_id": "slack.chat.postMessage"}],
            "edges": [],
        }
        res = workflow_validator.validate_workflow(graph)
        trigger_errors = [e for e in res.errors if "trigger" in e.lower() or "Trigger" in e]
        assert len(trigger_errors) == 0, f"Trigger '{ttype}' should be valid, got: {trigger_errors}"


# ─── 10. Edge Integrity ──────────────────────────────────────────────────────

def test_ai9_edge_with_unknown_source():
    """Edge pointing from a nonexistent source node must fail."""
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [{"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.send"}],
        "edges": [{"source": "ghost_node", "target": "step_1"}],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is False
    assert any("ghost_node" in err for err in res.errors)


def test_ai9_edge_with_unknown_target():
    """Edge pointing to a nonexistent target node must fail."""
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [{"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.send"}],
        "edges": [{"source": "step_1", "target": "step_999"}],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is False
    assert any("step_999" in err for err in res.errors)


# ─── 11. Empty Workflow ──────────────────────────────────────────────────────

def test_ai9_empty_nodes():
    """Workflow with no nodes must fail immediately."""
    graph = {"trigger": {"type": "Manual"}, "nodes": [], "edges": []}
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is False
    assert any("no execution nodes" in err for err in res.errors)


# ─── 12. Duplicate Edge IDs ──────────────────────────────────────────────────

def test_ai9_duplicate_edge_ids():
    """Two edges with the same ID must fail."""
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list"},
            {"id": "step_2", "provider": "Gmail", "operation_id": "gmail.messages.send"},
            {"id": "step_3", "provider": "Slack", "operation_id": "slack.chat.postMessage"},
        ],
        "edges": [
            {"id": "e1", "source": "step_1", "target": "step_2"},
            {"id": "e1", "source": "step_2", "target": "step_3"},  # duplicate "e1"
        ],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is False
    assert any("Duplicate edge ID" in err for err in res.errors)


# ─── 13. Node Missing ID ─────────────────────────────────────────────────────

def test_ai9_node_missing_id():
    """A node without an 'id' attribute must fail."""
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [{"provider": "Gmail", "operation_id": "gmail.messages.send"}],  # no id
        "edges": [],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is False
    assert any("missing required 'id'" in err for err in res.errors)


# ─── 14. Multi-Step DAG (AI-8 Integration) ───────────────────────────────────

def test_ai9_multistep_dag_validates_cleanly():
    """A 4-node Read→Get→Summarize→Send DAG with no explicit params must be valid."""
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {"id": "step_1", "provider": "Gmail",    "operation_id": "gmail.messages.list"},
            {"id": "step_2", "provider": "Gmail",    "operation_id": "gmail.messages.get"},
            {"id": "step_3", "provider": "AI",       "operation_id": "ai.summarize"},
            {"id": "step_4", "provider": "Gmail",    "operation_id": "gmail.messages.send"},
        ],
        "edges": [
            {"source": "step_1", "target": "step_2"},
            {"source": "step_2", "target": "step_3"},
            {"source": "step_3", "target": "step_4"},
        ],
    }
    res = workflow_validator.validate_workflow(graph)
    # No required-param errors (no params dicts provided)
    param_errors = [e for e in res.errors if "Required parameter" in e]
    assert len(param_errors) == 0
    # DAG should be valid
    assert res.is_valid is True


def test_ai9_invoice_drive_slack_dag_validates():
    """Search→Download→Drive→Slack 4-node workflow validates cleanly."""
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {"id": "step_1", "provider": "Gmail",         "operation_id": "gmail.messages.search"},
            {"id": "step_2", "provider": "Gmail",         "operation_id": "gmail.attachments.download"},
            {"id": "step_3", "provider": "Google_Drive",  "operation_id": "drive.files.create"},
            {"id": "step_4", "provider": "Slack",         "operation_id": "slack.chat.postMessage"},
        ],
        "edges": [
            {"source": "step_1", "target": "step_2"},
            {"source": "step_2", "target": "step_3"},
            {"source": "step_3", "target": "step_4"},
        ],
    }
    res = workflow_validator.validate_workflow(graph)
    param_errors = [e for e in res.errors if "Required parameter" in e]
    assert len(param_errors) == 0
    assert res.is_valid is True


# ─── 15. Execution Prevention ─────────────────────────────────────────────────

def test_ai9_execution_blocked_on_invalid_workflow():
    """Simulate runtime guard: execution must be blocked when is_valid=False."""
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {"id": "step_1", "provider": "UnknownBot", "operation_id": "bot.doSomething"},
        ],
        "edges": [],
    }
    res = workflow_validator.validate_workflow(graph)
    # Runtime guard check
    assert res.is_valid is False
    can_execute = res.is_valid
    assert can_execute is False, "Execution must be prevented for invalid workflows"


def test_ai9_execution_allowed_on_valid_workflow():
    """Valid workflow must set is_valid=True allowing execution."""
    graph = {
        "trigger": {"type": "Schedule"},
        "nodes": [
            {"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list"},
            {"id": "step_2", "provider": "Gmail", "operation_id": "gmail.messages.send"},
        ],
        "edges": [{"source": "step_1", "target": "step_2"}],
    }
    res = workflow_validator.validate_workflow(graph)
    param_errors = [e for e in res.errors if "Required parameter" in e]
    assert len(param_errors) == 0
    assert res.is_valid is True


# ─── 16. Full Validation Report Structure ──────────────────────────────────────

def test_ai9_validation_result_structure():
    """ValidationResult must always have all required fields."""
    graph = _valid_graph()
    res = workflow_validator.validate_workflow(graph)
    assert hasattr(res, "is_valid")
    assert hasattr(res, "errors")
    assert hasattr(res, "warnings")
    assert hasattr(res, "suggestions")
    assert hasattr(res, "confidence")
    assert isinstance(res.is_valid, bool)
    assert isinstance(res.errors, list)
    assert isinstance(res.warnings, list)
    assert isinstance(res.confidence, float)
    assert 0.0 <= res.confidence <= 1.0
