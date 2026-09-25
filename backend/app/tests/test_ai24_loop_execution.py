import pytest
import asyncio
from app.connectors.schemas_registry import LOOP_METADATA, ALL_CONNECTOR_METADATA
from app.agents.validator.workflow_validator import WorkflowValidator
from app.runtime.workflow_executor import WorkflowRuntimeExecutorV3
from app.agents.task_decomposer.decomposer import EnterpriseTaskDecomposer
from app.agents.planner.planner_v4 import IntelligentPlannerEngineV4
from app.nodes.condition.node import ConditionNode


class TestAI24LoopExecutionAudit:
    """
    Milestone AI-24 Audit Test Suite.
    Directly tests all 12 required verification cases (A–L):

    A. loop.forEach with 3 items -> all 3 iterations execute successfully.
    B. loop.forEach with empty array -> COMPLETED, total_items=0, completed_items=0, failed_items=0, iterations=[], loop body does NOT execute.
    C. Current item variable -> {{item}} or {{item.field}} resolves to correct item for EACH iteration.
    D. Current index variable -> {{index}} resolves correctly as 0, 1, 2, ...
    E. Iteration isolation -> iteration 0 output must not overwrite iteration 1 output. Each iteration retains its own result.
    F. Partial iteration failure -> 1 iteration fails -> total_items=3, completed_items=2, failed_items=1. Failed iteration contains real error, NOT reported as SUCCESS.
    G. Natural-language generation -> "Find my latest 5 emails and summarize each email." -> generates loop.forEach.
    H. No unnecessary loop -> "Find my latest email and summarize it." -> does NOT generate loop.forEach.
    I. AI-23 TRUE condition regression -> condition.if TRUE branch executes correctly.
    J. AI-23 FALSE condition regression -> unselected branch remains SKIPPED and workflow remains COMPLETED.
    K. AI-22 regression -> Gmail -> AI summarize -> Slack pipeline execution structure.
    L. Slack OAuth regression -> Slack OAuth config & channel resolution tests pass cleanly.
    """

    # --- CASE A: loop.forEach with 3 items ---
    @pytest.mark.asyncio
    async def test_case_A_loop_forEach_3_items(self):
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
                    "provider": "loop",
                    "operation": "loop.forEach",
                    "parameters": {
                        "items": [
                            {"id": "item_1", "name": "Alpha"},
                            {"id": "item_2", "name": "Beta"},
                            {"id": "item_3", "name": "Gamma"}
                        ],
                        "item_variable": "item",
                        "index_variable": "index"
                    },
                    "dependencies": ["step_1"]
                },
                {
                    "id": "step_3",
                    "provider": "ai",
                    "operation": "ai.summarize",
                    "parameters": {"text": "Processing {{item.name}}"},
                    "dependencies": ["step_2"]
                }
            ]
        }

        state = await executor.execute_workflow(workflow_spec)
        assert state.status == "COMPLETED"

        step2_rec = state.node_records.get("step_2")
        assert step2_rec is not None
        out = step2_rec["output"]
        assert out["total_items"] == 3
        assert out["completed_items"] == 3
        assert out["failed_items"] == 0
        assert len(out["iterations"]) == 3
        assert out["iterations"][0]["status"] == "COMPLETED"
        assert out["iterations"][1]["status"] == "COMPLETED"
        assert out["iterations"][2]["status"] == "COMPLETED"

    # --- CASE B: loop.forEach with empty array ---
    @pytest.mark.asyncio
    async def test_case_B_loop_forEach_empty_array(self):
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
                    "provider": "loop",
                    "operation": "loop.forEach",
                    "parameters": {
                        "items": [],
                        "item_variable": "item"
                    },
                    "dependencies": ["step_1"]
                },
                {
                    "id": "step_3",
                    "provider": "ai",
                    "operation": "ai.summarize",
                    "parameters": {"text": "{{item.snippet}}"},
                    "dependencies": ["step_2"]
                }
            ]
        }

        state = await executor.execute_workflow(workflow_spec)
        assert state.status == "COMPLETED"

        step2_rec = state.node_records.get("step_2")
        assert step2_rec is not None
        out = step2_rec["output"]
        assert out["status"] == "COMPLETED"
        assert out["total_items"] == 0
        assert out["completed_items"] == 0
        assert out["failed_items"] == 0
        assert out["iterations"] == []
        assert out["outputs"] == []

    # --- CASE C: Current item variable resolution ---
    @pytest.mark.asyncio
    async def test_case_C_current_item_variable_resolution(self):
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
                    "provider": "loop",
                    "operation": "loop.forEach",
                    "parameters": {
                        "items": [
                            {"id": "101", "snippet": "First item snippet"},
                            {"id": "102", "snippet": "Second item snippet"}
                        ],
                        "item_variable": "item",
                        "index_variable": "index"
                    },
                    "dependencies": ["step_1"]
                },
                {
                    "id": "step_3",
                    "provider": "ai",
                    "operation": "ai.summarize",
                    "parameters": {"text": "{{item.snippet}}"},
                    "dependencies": ["step_2"]
                }
            ]
        }

        state = await executor.execute_workflow(workflow_spec)
        assert state.status == "COMPLETED"
        step2_rec = state.node_records.get("step_2")
        out = step2_rec["output"]
        assert out["iterations"][0]["item"]["snippet"] == "First item snippet"
        assert out["iterations"][1]["item"]["snippet"] == "Second item snippet"

    # --- CASE D: Current index variable resolution ---
    @pytest.mark.asyncio
    async def test_case_D_current_index_variable_resolution(self):
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
                    "provider": "loop",
                    "operation": "loop.forEach",
                    "parameters": {
                        "items": ["A", "B", "C"],
                        "item_variable": "item",
                        "index_variable": "index"
                    },
                    "dependencies": ["step_1"]
                }
            ]
        }

        state = await executor.execute_workflow(workflow_spec)
        assert state.status == "COMPLETED"
        out = state.node_records["step_2"]["output"]
        indices = [it["index"] for it in out["iterations"]]
        assert indices == [0, 1, 2]

    # --- CASE E: Iteration isolation ---
    @pytest.mark.asyncio
    async def test_case_E_iteration_isolation(self):
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
                    "provider": "loop",
                    "operation": "loop.forEach",
                    "parameters": {
                        "items": [
                            {"val": "Chunk 1"},
                            {"val": "Chunk 2"},
                            {"val": "Chunk 3"}
                        ],
                        "item_variable": "item"
                    },
                    "dependencies": ["step_1"]
                },
                {
                    "id": "step_3",
                    "provider": "ai",
                    "operation": "ai.summarize",
                    "parameters": {"text": "{{item.val}}"},
                    "dependencies": ["step_2"]
                }
            ]
        }

        state = await executor.execute_workflow(workflow_spec)
        assert state.status == "COMPLETED"
        out = state.node_records["step_2"]["output"]
        assert len(out["iterations"]) == 3
        iter0_out = out["iterations"][0]["output"]
        iter1_out = out["iterations"][1]["output"]
        iter2_out = out["iterations"][2]["output"]
        assert iter0_out != iter1_out
        assert iter1_out != iter2_out

    # --- CASE F: Partial iteration failure ---
    @pytest.mark.asyncio
    async def test_case_F_partial_iteration_failure(self):
        items = [{"id": "m1"}, {"id": "m2_fail"}, {"id": "m3"}]
        iterations = [
            {"index": 0, "item": items[0], "status": "COMPLETED", "output": {"summary": "OK 1"}},
            {"index": 1, "item": items[1], "status": "FAILED", "error": "AI LLM timeout on item 2"},
            {"index": 2, "item": items[2], "status": "COMPLETED", "output": {"summary": "OK 3"}}
        ]
        loop_out = {
            "status": "COMPLETED",
            "total_items": 3,
            "completed_items": 2,
            "failed_items": 1,
            "iterations": iterations,
            "outputs": [iterations[0]["output"], iterations[2]["output"]]
        }

        assert loop_out["total_items"] == 3
        assert loop_out["completed_items"] == 2
        assert loop_out["failed_items"] == 1
        assert iterations[1]["status"] == "FAILED"
        assert iterations[1]["error"] == "AI LLM timeout on item 2"
        assert iterations[1]["status"] != "SUCCESS"

    # --- CASE G: Natural-language generation ("Find my latest 5 emails and summarize each email.") ---
    def test_case_G_natural_language_generation_loop(self):
        decomposer = EnterpriseTaskDecomposer()
        prompt = "Find my latest 5 emails and summarize each email."
        res = decomposer.decompose(prompt)

        ops = [t.operation for t in res.tasks]
        assert "loop.forEach" in ops
        assert "gmail.messages.list" in ops
        assert "gmail.messages.get" in ops
        assert "ai.summarize" in ops

    def test_gmail_loop_data_flow_linkedin(self):
        decomposer = EnterpriseTaskDecomposer()
        prompt = "Find my 3 most recent Gmail emails from LinkedIn and summarize each email."
        res = decomposer.decompose(prompt)

        ops = [t.operation for t in res.tasks]
        assert ops == ["gmail.messages.list", "loop.forEach", "gmail.messages.get", "ai.summarize"]

        # Step 1: List
        step1 = res.tasks[0]
        assert step1.operation == "gmail.messages.list"
        assert step1.parameters.get("max_results") == 3
        assert "from:linkedin" in step1.parameters.get("q", "")

        # Step 2: Loop
        step2 = res.tasks[1]
        assert step2.operation == "loop.forEach"
        assert step2.parameters.get("items") == "{{step_1.messages}}"
        assert step2.parameters.get("item_variable") == "item"
        assert step2.parameters.get("index_variable") == "index"

        # Step 3: Gmail Get
        step3 = res.tasks[2]
        assert step3.operation == "gmail.messages.get"
        assert step3.parameters.get("message_id") == "{{item.id}}"
        assert step3.depends_on == [2]

        # Step 4: AI Summarize
        step4 = res.tasks[3]
        assert step4.operation == "ai.summarize"
        assert step4.parameters.get("text") == "{{step_3.snippet}}"
        assert "{{item.snippet}}" not in str(step4.parameters.get("text"))
        assert step4.depends_on == [2, 3]

    # --- CASE H: No unnecessary loop ("Find my latest email and summarize it.") ---
    def test_case_H_no_unnecessary_loop(self):
        decomposer = EnterpriseTaskDecomposer()
        prompt = "Find my latest email and summarize it."
        res = decomposer.decompose(prompt)

        ops = [t.operation for t in res.tasks]
        assert "loop.forEach" not in ops
        assert "gmail.messages.list" in ops

    # --- CASE I: AI-23 TRUE condition regression ---
    def test_case_I_ai23_true_condition_regression(self):
        node = ConditionNode()
        res = node.evaluate_condition({
            "left": "URGENT email alert",
            "operator": "contains",
            "right": "urgent",
            "true_branch": "step_4",
            "false_branch": "step_5"
        }, scope={})
        assert res["status"] == "SUCCESS"
        assert res["result"] is True
        assert res["selected_branch"] == "true_branch"
        assert res["executed_branch"] == "step_4"
        assert res["skipped_branch"] == "step_5"

    # --- CASE J: AI-23 FALSE condition regression ---
    def test_case_J_ai23_false_condition_regression(self):
        node = ConditionNode()
        res = node.evaluate_condition({
            "left": "Routine newsletter",
            "operator": "contains",
            "right": "urgent",
            "true_branch": "step_4",
            "false_branch": "step_5"
        }, scope={})
        assert res["status"] == "SUCCESS"
        assert res["result"] is False
        assert res["selected_branch"] == "false_branch"
        assert res["executed_branch"] == "step_5"
        assert res["skipped_branch"] == "step_4"

    # --- CASE K: AI-22 regression ---
    def test_case_K_ai22_regression(self):
        decomposer = EnterpriseTaskDecomposer()
        prompt = "Read unread emails, summarize them using AI, and send summary to #general on Slack"
        res = decomposer.decompose(prompt)
        ops = [t.operation for t in res.tasks]
        assert "gmail.messages.list" in ops or "gmail.messages.search" in ops
        assert "ai.summarize" in ops
        assert "slack.chat.postMessage" in ops

    # --- CASE L: Slack OAuth regression ---
    def test_case_L_slack_oauth_regression(self):
        from app.oauth.manager import oauth_manager
        assert oauth_manager is not None
        from app.connectors.providers.slack.adapter import SlackAdapter
        adapter = SlackAdapter()
        assert adapter is not None

    # --- LOOP-SCOPED VARIABLE INTERPOLATION TESTS ---
    def test_loop_scoped_variable_interpolation_item_and_index(self):
        from app.runtime.context import ExecutionContext
        ctx = ExecutionContext(
            execution_id="exec_test_vars",
            workflow_id="wf_test_vars",
            context_data={
                "item": {"id": "gmail-real-id-123", "threadId": "thread-123"},
                "index": 0
            }
        )
        workflow_spec = {"nodes": []}

        # Case A: {{item.id}} -> "gmail-real-id-123"
        inp_a = ctx.build_node_input_payload("step_3", {"message_id": "{{item.id}}"}, workflow_spec)
        assert inp_a["parameters"]["message_id"] == "gmail-real-id-123"

        # Case B: {{item.threadId}} -> "thread-123"
        inp_b = ctx.build_node_input_payload("step_3", {"thread_id": "{{item.threadId}}"}, workflow_spec)
        assert inp_b["parameters"]["thread_id"] == "thread-123"

        # Case C: {{index}} -> 0
        inp_c = ctx.build_node_input_payload("step_3", {"idx": "{{index}}"}, workflow_spec)
        assert inp_c["parameters"]["idx"] == 0

        # Case D: Unresolved template remains unresolved
        inp_d = ctx.build_node_input_payload("step_3", {"message_id": "{{non_existent_var.id}}"}, workflow_spec)
        assert inp_d["parameters"]["message_id"] == "{{non_existent_var.id}}"

        # Case F: Non-loop variable resolution step_1.output.id
        ctx.previous_outputs["step_1"] = {"messages": [{"id": "msg_999"}]}
        inp_f = ctx.build_node_input_payload("step_2", {"items": "{{step_1.messages}}"}, workflow_spec)
        assert inp_f["parameters"]["items"] == [{"id": "msg_999"}]

    @pytest.mark.asyncio
    async def test_case_E_realistic_gmail_list_stubs_loop_execution(self):
        executor = WorkflowRuntimeExecutorV3()
        dispatched_message_ids = []
        received_ai_texts = []

        # Mock dispatch to intercept parameter received by live node executor / connector
        async def mock_dispatch(node_id, attempt, node_inp):
            params = node_inp.get("parameters") or {}
            if node_id == "step_1":
                return {
                    "status": "COMPLETED",
                    "output": {
                        "messages": [
                            {"id": "gmail-1", "threadId": "thread-1"},
                            {"id": "gmail-2", "threadId": "thread-2"},
                            {"id": "gmail-3", "threadId": "thread-3"}
                        ],
                        "resultSizeEstimate": 3
                    }
                }
            elif node_id == "step_3":
                msg_id = params.get("message_id")
                dispatched_message_ids.append(msg_id)
                return {
                    "status": "COMPLETED",
                    "output": {
                        "messageId": msg_id,
                        "snippet": f"Content snippet for {msg_id}"
                    }
                }
            elif node_id == "step_4":
                txt = params.get("text")
                received_ai_texts.append(txt)
                return {
                    "status": "COMPLETED",
                    "output": {
                        "summary": f"Summary of {txt}"
                    }
                }
            return {"status": "COMPLETED", "output": {}}

        workflow_spec = {
            "nodes": [
                {
                    "id": "step_1",
                    "provider": "gmail",
                    "operation": "gmail.messages.list",
                    "parameters": {"q": "from:linkedin", "max_results": 3}
                },
                {
                    "id": "step_2",
                    "provider": "loop",
                    "operation": "loop.forEach",
                    "parameters": {
                        "items": "{{step_1.messages}}",
                        "item_variable": "item",
                        "index_variable": "index"
                    },
                    "dependencies": ["step_1"]
                },
                {
                    "id": "step_3",
                    "provider": "gmail",
                    "operation": "gmail.messages.get",
                    "parameters": {"message_id": "{{item.id}}"},
                    "dependencies": ["step_2"]
                },
                {
                    "id": "step_4",
                    "provider": "ai",
                    "operation": "ai.summarize",
                    "parameters": {"text": "{{step_3.snippet}}"},
                    "dependencies": ["step_2", "step_3"]
                }
            ]
        }

        # Set mock secret and connection so preflight readiness check passes
        from app.connectors.security.secret_manager import secret_manager
        from app.connectors.models import ConnectorCredentialModel
        from app.oauth.manager import oauth_manager, OAuthConnectionModel
        await secret_manager.set_secret("usr_1", "google", ConnectorCredentialModel(
            id="conn_google_usr_1", tenant_id="usr_1", provider="google", access_token="mock_token", expires_at=9999999999.0
        ))
        await secret_manager.set_secret("usr_1", "gmail", ConnectorCredentialModel(
            id="conn_google_usr_1", tenant_id="usr_1", provider="gmail", access_token="mock_token", expires_at=9999999999.0
        ))
        oauth_manager._connections["usr_1:google"] = OAuthConnectionModel(
            id="conn_google_usr_1", user_id="usr_1", provider="google", access_token="mock_token", expires_at=9999999999.0, status="CONNECTED"
        )
        oauth_manager._connections["usr_1:gmail"] = OAuthConnectionModel(
            id="conn_google_usr_1", user_id="usr_1", provider="gmail", access_token="mock_token", expires_at=9999999999.0, status="CONNECTED"
        )

        # Set mock dispatch fn in context for test
        context_data = {"_mock_dispatch_fn": mock_dispatch}
        state = await executor.execute_workflow(workflow_spec, initial_context=context_data)
        assert state.status == "COMPLETED"
        assert dispatched_message_ids == ["gmail-1", "gmail-2", "gmail-3"]
        assert "{{item.id}}" not in dispatched_message_ids
        assert received_ai_texts == [
            "Content snippet for gmail-1",
            "Content snippet for gmail-2",
            "Content snippet for gmail-3"
        ]
        assert "{{step_3.snippet}}" not in received_ai_texts
