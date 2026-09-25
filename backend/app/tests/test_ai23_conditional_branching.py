import pytest
import asyncio
from app.nodes.condition.node import ConditionNode
from app.agents.validator.workflow_validator import WorkflowValidator
from app.runtime.workflow_executor import WorkflowRuntimeExecutorV3
from app.agents.task_decomposer.decomposer import EnterpriseTaskDecomposer


class TestAI23ConditionalBranching:
    """
    Test suite for AI-23 — Conditional Workflow Branching (IF/ELSE).
    Covers evaluation, branch execution, branch skipping, DAG validation, and task decomposition.
    """

    # --- Unit Tests: ConditionNode Evaluation ---

    def test_condition_equals_true(self):
        node = ConditionNode()
        res = node.evaluate_condition({
            "left": "urgent",
            "operator": "equals",
            "right": "urgent",
            "true_branch": "step_4",
            "false_branch": "step_5"
        }, scope={})
        assert res["status"] == "SUCCESS"
        assert res["result"] is True
        assert res["selected_branch"] == "true_branch"
        assert res["executed_branch"] == "step_4"
        assert res["skipped_branch"] == "step_5"

    def test_condition_equals_false(self):
        node = ConditionNode()
        res = node.evaluate_condition({
            "left": "normal",
            "operator": "equals",
            "right": "urgent",
            "true_branch": "step_4",
            "false_branch": "step_5"
        }, scope={})
        assert res["status"] == "SUCCESS"
        assert res["result"] is False
        assert res["selected_branch"] == "false_branch"
        assert res["executed_branch"] == "step_5"
        assert res["skipped_branch"] == "step_4"

    def test_condition_contains_true(self):
        node = ConditionNode()
        res = node.evaluate_condition({
            "left": "This is an URGENT email regarding system status.",
            "operator": "contains",
            "right": "urgent"
        }, scope={})
        assert res["status"] == "SUCCESS"
        assert res["result"] is True

    def test_condition_contains_false(self):
        node = ConditionNode()
        res = node.evaluate_condition({
            "left": "This is a routine monthly update.",
            "operator": "contains",
            "right": "urgent"
        }, scope={})
        assert res["status"] == "SUCCESS"
        assert res["result"] is False

    def test_condition_exists(self):
        node = ConditionNode()
        res_exists = node.evaluate_condition({
            "left": "valid content",
            "operator": "exists"
        }, scope={})
        assert res_exists["result"] is True

        res_not_exists = node.evaluate_condition({
            "left": None,
            "operator": "exists"
        }, scope={})
        assert res_not_exists["result"] is False

        res_not_exists_op = node.evaluate_condition({
            "left": "",
            "operator": "not_exists"
        }, scope={})
        assert res_not_exists_op["result"] is True

    # --- Integration Tests: DAG Executor Branching & Skipping ---

    def test_dag_executor_true_branch_executes_false_branch_skipped(self):
        executor = WorkflowRuntimeExecutorV3()
        workflow_spec = {
            "nodes": [
                {
                    "id": "step_1",
                    "provider": "schedule",
                    "operation": "schedule.trigger",
                    "parameters": {"cron": "0 8 * * *"}
                },
                {
                    "id": "step_2",
                    "provider": "condition",
                    "operation": "condition.if",
                    "parameters": {
                        "left": "urgent notification",
                        "operator": "contains",
                        "right": "urgent",
                        "true_branch": "step_3",
                        "false_branch": "step_4"
                    }
                },
                {
                    "id": "step_3",
                    "provider": "ai",
                    "operation": "ai.summarize",
                    "parameters": {"text": "urgent content"}
                },
                {
                    "id": "step_4",
                    "provider": "ai",
                    "operation": "ai.summarize",
                    "parameters": {"text": "fallback text"}
                }
            ],
            "edges": [
                {"id": "e1-2", "source": "step_1", "target": "step_2"},
                {"id": "e2-3", "source": "step_2", "target": "step_3"},
                {"id": "e2-4", "source": "step_2", "target": "step_4"},
            ]
        }

        res = asyncio.run(executor.execute_workflow(workflow_spec, {}))
        assert res.status in ["COMPLETED", "SUCCESS"]
        records = res.node_records

        step_2_rec = records.get("step_2")
        step_2_out = step_2_rec.get("output") if isinstance(step_2_rec, dict) else step_2_rec.output
        step_2_body = step_2_out.get("body") if isinstance(step_2_out, dict) and "body" in step_2_out else step_2_out
        assert step_2_body.get("result") is True

        step_3_rec = records.get("step_3")
        step_3_status = step_3_rec.get("status") if isinstance(step_3_rec, dict) else step_3_rec.status
        assert step_3_status in ["SUCCESS", "COMPLETED"]

        step_4_rec = records.get("step_4")
        step_4_status = step_4_rec.get("status") if isinstance(step_4_rec, dict) else step_4_rec.status
        assert step_4_status == "SKIPPED"

    def test_dag_executor_false_branch_executes_true_branch_skipped(self):
        executor = WorkflowRuntimeExecutorV3()
        workflow_spec = {
            "nodes": [
                {
                    "id": "step_1",
                    "provider": "schedule",
                    "operation": "schedule.trigger",
                    "parameters": {"cron": "0 8 * * *"}
                },
                {
                    "id": "step_2",
                    "provider": "condition",
                    "operation": "condition.if",
                    "parameters": {
                        "left": "routine update",
                        "operator": "contains",
                        "right": "urgent",
                        "true_branch": "step_3",
                        "false_branch": "step_4"
                    }
                },
                {
                    "id": "step_3",
                    "provider": "ai",
                    "operation": "ai.summarize",
                    "parameters": {"text": "routine content"}
                },
                {
                    "id": "step_4",
                    "provider": "ai",
                    "operation": "ai.summarize",
                    "parameters": {"text": "routine fallback"}
                }
            ],
            "edges": [
                {"id": "e1-2", "source": "step_1", "target": "step_2"},
                {"id": "e2-3", "source": "step_2", "target": "step_3"},
                {"id": "e2-4", "source": "step_2", "target": "step_4"},
            ]
        }

        res = asyncio.run(executor.execute_workflow(workflow_spec, {}))
        assert res.status in ["COMPLETED", "SUCCESS"]
        records = res.node_records

        step_2_rec = records.get("step_2")
        step_2_out = step_2_rec.get("output") if isinstance(step_2_rec, dict) else step_2_rec.output
        step_2_body = step_2_out.get("body") if isinstance(step_2_out, dict) and "body" in step_2_out else step_2_out
        assert step_2_body.get("result") is False

        step_3_rec = records.get("step_3")
        step_3_status = step_3_rec.get("status") if isinstance(step_3_rec, dict) else step_3_rec.status
        assert step_3_status == "SKIPPED"

        step_4_rec = records.get("step_4")
        step_4_status = step_4_rec.get("status") if isinstance(step_4_rec, dict) else step_4_rec.status
        assert step_4_status in ["SUCCESS", "COMPLETED"]

    def test_dag_executor_skips_transitive_downstream_dependents(self):
        executor = WorkflowRuntimeExecutorV3()
        workflow_spec = {
            "nodes": [
                {"id": "step_1", "provider": "schedule", "operation": "schedule.trigger", "parameters": {}},
                {
                    "id": "step_2",
                    "provider": "condition",
                    "operation": "condition.if",
                    "parameters": {
                        "left": "urgent text",
                        "operator": "contains",
                        "right": "urgent",
                        "true_branch": "step_3",
                        "false_branch": "step_4"
                    }
                },
                {"id": "step_3", "provider": "ai", "operation": "ai.summarize", "parameters": {"text": "urgent"}},
                {"id": "step_4", "provider": "ai", "operation": "ai.summarize", "parameters": {"text": "fallback"}},
                {"id": "step_5", "provider": "ai", "operation": "ai.summarize", "parameters": {"text": "step 3 done"}},
                {"id": "step_6", "provider": "ai", "operation": "ai.summarize", "parameters": {"text": "step 4 done"}},
            ],
            "edges": [
                {"id": "e1-2", "source": "step_1", "target": "step_2"},
                {"id": "e2-3", "source": "step_2", "target": "step_3"},
                {"id": "e2-4", "source": "step_2", "target": "step_4"},
                {"id": "e3-5", "source": "step_3", "target": "step_5"},
                {"id": "e4-6", "source": "step_4", "target": "step_6"},
            ]
        }

        res = asyncio.run(executor.execute_workflow(workflow_spec, {}))
        records = res.node_records

        step_3_rec = records.get("step_3")
        step_3_status = step_3_rec.get("status") if isinstance(step_3_rec, dict) else step_3_rec.status
        assert step_3_status in ["SUCCESS", "COMPLETED"]

        step_5_rec = records.get("step_5")
        step_5_status = step_5_rec.get("status") if isinstance(step_5_rec, dict) else step_5_rec.status
        assert step_5_status in ["SUCCESS", "COMPLETED"]

        step_4_rec = records.get("step_4")
        step_4_status = step_4_rec.get("status") if isinstance(step_4_rec, dict) else step_4_rec.status
        assert step_4_status == "SKIPPED"

        step_6_rec = records.get("step_6")
        step_6_status = step_6_rec.get("status") if isinstance(step_6_rec, dict) else step_6_rec.status
        assert step_6_status == "SKIPPED"

    # --- Validation Tests ---

    def test_validator_rejects_invalid_operator(self):
        validator = WorkflowValidator()
        spec = {
            "nodes": [
                {
                    "id": "step_1",
                    "provider": "condition",
                    "operation": "condition.if",
                    "parameters": {"operator": "invalid_op_xyz", "true_branch": "step_2"}
                },
                {"id": "step_2", "provider": "ai", "operation": "ai.summarize", "parameters": {}}
            ],
            "edges": [{"id": "e1-2", "source": "step_1", "target": "step_2"}]
        }
        res = validator.validate_workflow(spec)
        assert res.is_valid is False
        assert any("Invalid condition operator" in err or "Unsupported" in err for err in res.errors)

    def test_validator_rejects_invalid_branch_target(self):
        validator = WorkflowValidator()
        spec = {
            "nodes": [
                {
                    "id": "step_1",
                    "provider": "condition",
                    "operation": "condition.if",
                    "parameters": {"operator": "equals", "true_branch": "step_nonexistent"}
                }
            ],
            "edges": []
        }
        res = validator.validate_workflow(spec)
        assert res.is_valid is False
        assert any("non-existent" in err for err in res.errors)

    def test_validator_cycle_detection_with_condition_node(self):
        validator = WorkflowValidator()
        spec = {
            "nodes": [
                {"id": "step_1", "provider": "condition", "operation": "condition.if", "parameters": {"operator": "equals", "true_branch": "step_2"}},
                {"id": "step_2", "provider": "ai", "operation": "ai.summarize", "parameters": {}}
            ],
            "edges": [
                {"id": "e1-2", "source": "step_1", "target": "step_2"},
                {"id": "e2-1", "source": "step_2", "target": "step_1"},
            ]
        }
        res = validator.validate_workflow(spec)
        assert res.is_valid is False
        assert any("Cycle" in err or "cycle" in err for err in res.errors)

    # --- Task Decomposition Tests ---

    def test_task_decomposer_conditional_prompt(self):
        decomposer = EnterpriseTaskDecomposer()
        prompt = "Check whether email contains urgent, if so summarize and send to #all-agentflow-ai"
        res = decomposer.decompose(prompt)
        assert len(res.tasks) >= 4
        condition_task = next((t for t in res.tasks if t.operation == "condition.if" or t.provider == "condition"), None)
        assert condition_task is not None
        assert condition_task.parameters.get("operator") == "contains"
        assert condition_task.parameters.get("right") == "urgent"

        slack_task = next((t for t in res.tasks if t.provider == "slack"), None)
        assert slack_task is not None
        assert slack_task.parameters.get("channel") == "#all-agentflow-ai"

    def test_task_decomposer_otherwise_do_nothing_prompt(self):
        decomposer = EnterpriseTaskDecomposer()
        prompt = "Check whether my latest email contains the word urgent. If it does, summarize the email using AI and send the summary to #all-agentflow-ai on Slack. Otherwise, do nothing."
        res = decomposer.decompose(prompt)

        # 1. "otherwise do nothing" -> no false action node
        condition_task = next((t for t in res.tasks if t.operation == "condition.if" or t.provider == "condition"), None)
        assert condition_task is not None
        assert condition_task.parameters.get("false_branch") is None
        assert not any("Fallback Email" in t.name or "gmail.messages.send" in t.operation for t in res.tasks)

        # 2. "if it does..." -> TRUE branch still generated
        assert any(t.operation == "ai.summarize" for t in res.tasks)

        # 3. Slack remains #all-agentflow-ai
        slack_task = next((t for t in res.tasks if t.provider == "slack"), None)
        assert slack_task is not None
        assert slack_task.parameters.get("channel") == "#all-agentflow-ai"

        # 4. Condition operator is actually "contains"
        assert condition_task.parameters.get("operator") == "contains"
        assert condition_task.parameters.get("right") == "urgent"
        assert condition_task.parameters.get("left") == "{{step_2.snippet}}"

    # --- Regression Tests for Requirement 5 (A, B, C) ---

    def test_regression_false_condition_unselected_skipped_overall_completed(self):
        """Test A: FALSE condition -> selected branch executes, unselected branch skipped -> overall COMPLETED."""
        from app.api.v1.runtime import execute_full_workflow_dag
        workflow_spec = {
            "workflow_id": "wf_test_false_cond",
            "nodes": [
                {"id": "step_1", "step_id": "step_1", "provider": "schedule", "operation_id": "schedule.trigger", "parameters": {}},
                {
                    "id": "step_2",
                    "step_id": "step_2",
                    "provider": "condition",
                    "operation_id": "condition.if",
                    "parameters": {
                        "left": "normal text",
                        "operator": "contains",
                        "right": "urgent",
                        "true_branch": "step_3",
                        "false_branch": "step_4"
                    }
                },
                {"id": "step_3", "step_id": "step_3", "provider": "ai", "operation_id": "ai.summarize", "parameters": {"text": "true branch text"}},
                {"id": "step_4", "step_id": "step_4", "provider": "ai", "operation_id": "ai.summarize", "parameters": {"text": "false branch text"}},
            ],
            "edges": [
                {"id": "e1-2", "source": "step_1", "target": "step_2"},
                {"id": "e2-3", "source": "step_2", "target": "step_3"},
                {"id": "e2-4", "source": "step_2", "target": "step_4"},
            ]
        }
        res = asyncio.run(execute_full_workflow_dag({"workflow": workflow_spec}))
        assert res["success"] is True
        assert res["status"] == "COMPLETED"
        assert res["nodes_executed"] == 3
        assert res["skipped_nodes"] == 1
        assert res["total_nodes"] == 4

        # Verify step_3 is SKIPPED and step_4 is SUCCESS
        step_3_res = next(r for r in res["node_results"] if r["node_id"] == "step_3")
        assert step_3_res["status"] == "SKIPPED"

        step_4_res = next(r for r in res["node_results"] if r["node_id"] == "step_4")
        assert step_4_res["status"] == "SUCCESS"

    def test_regression_true_condition_unselected_skipped_overall_completed(self):
        """Test B: TRUE condition -> selected branch executes, unselected branch skipped -> overall COMPLETED."""
        from app.api.v1.runtime import execute_full_workflow_dag
        workflow_spec = {
            "workflow_id": "wf_test_true_cond",
            "nodes": [
                {"id": "step_1", "step_id": "step_1", "provider": "schedule", "operation_id": "schedule.trigger", "parameters": {}},
                {
                    "id": "step_2",
                    "step_id": "step_2",
                    "provider": "condition",
                    "operation_id": "condition.if",
                    "parameters": {
                        "left": "urgent email body",
                        "operator": "contains",
                        "right": "urgent",
                        "true_branch": "step_3",
                        "false_branch": "step_4"
                    }
                },
                {"id": "step_3", "step_id": "step_3", "provider": "ai", "operation_id": "ai.summarize", "parameters": {"text": "true branch text"}},
                {"id": "step_4", "step_id": "step_4", "provider": "ai", "operation_id": "ai.summarize", "parameters": {"text": "false branch text"}},
            ],
            "edges": [
                {"id": "e1-2", "source": "step_1", "target": "step_2"},
                {"id": "e2-3", "source": "step_2", "target": "step_3"},
                {"id": "e2-4", "source": "step_2", "target": "step_4"},
            ]
        }
        res = asyncio.run(execute_full_workflow_dag({"workflow": workflow_spec}))
        assert res["success"] is True
        assert res["status"] == "COMPLETED"
        assert res["nodes_executed"] == 3
        assert res["skipped_nodes"] == 1
        assert res["total_nodes"] == 4

        # Verify step_3 is SUCCESS and step_4 is SKIPPED
        step_3_res = next(r for r in res["node_results"] if r["node_id"] == "step_3")
        assert step_3_res["status"] == "SUCCESS"

        step_4_res = next(r for r in res["node_results"] if r["node_id"] == "step_4")
        assert step_4_res["status"] == "SKIPPED"

    def test_regression_genuine_node_failure_overall_failed(self):
        """Test C: Genuine node failure -> overall FAILED."""
        from unittest.mock import patch
        from app.api.v1.runtime import execute_full_workflow_dag
        from app.runtime.workflow_executor import workflow_runtime_executor_v3

        orig_dispatch = workflow_runtime_executor_v3.scheduler.dispatch_ready_nodes

        async def mock_dispatch(nodes):
            res = await orig_dispatch(nodes)
            for r in res:
                if r.get("node_id") == "step_2" or r.get("id") == "step_2":
                    r["status"] = "FAILED"
                    r["output"] = {"error": "Connection timeout 500"}
            return res

        with patch.object(workflow_runtime_executor_v3.scheduler, "dispatch_ready_nodes", side_effect=mock_dispatch):
            workflow_spec = {
                "workflow_id": "wf_test_failing_node",
                "nodes": [
                    {"id": "step_1", "step_id": "step_1", "provider": "schedule", "operation_id": "schedule.trigger", "parameters": {}},
                    {"id": "step_2", "step_id": "step_2", "provider": "failing_provider", "operation_id": "failing.node.op", "parameters": {}},
                ],
                "edges": [
                    {"id": "e1-2", "source": "step_1", "target": "step_2"},
                ]
            }
            res = asyncio.run(execute_full_workflow_dag({"workflow": workflow_spec}))

        assert res["success"] is False
        assert res["status"] == "FAILED"
        assert len(res["errors"]) > 0
        assert "Connection timeout 500" in res["errors"][0]

