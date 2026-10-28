import pytest
from unittest.mock import MagicMock, patch
from app.agents.planner.planner_v4 import IntelligentPlannerEngineV4
from app.agents.task_decomposer.models import DecomposedTask, TaskDecompositionResult
from app.agents.connector_ai.operation_ranker import operation_ranker
from app.agents.api_discovery.dynamic_discovery import dynamic_api_discovery_engine


def test_01_planner_v4_passes_task_instructions_to_operation_ranker():
    planner = IntelligentPlannerEngineV4()
    prompt = "Get store order by ID and then get pet details using https://petstore3.swagger.io/api/v3/openapi.json"

    # Mock bridge result
    mock_bridge_res = MagicMock()
    mock_bridge_res.attempted = True
    mock_bridge_res.success = True
    mock_bridge_res.provider = "Petstore"
    mock_bridge_res.discovered_ops_count = 2
    mock_bridge_res.url = "https://petstore3.swagger.io/api/v3/openapi.json"
    mock_bridge_res.discovered_ops = []
    mock_bridge_res.error_message = None

    # Mock decomposer result with 2 tasks
    mock_decomp_res = TaskDecompositionResult(
        prompt=prompt,
        intent="dynamic_api",
        tasks=[
            DecomposedTask(
                step=1,
                name="Get store order by ID",
                provider="generic",
                operation="execute.action",
                parameters={"instruction": "Get store order by ID"},
                depends_on=[],
            ),
            DecomposedTask(
                step=2,
                name="get pet details",
                provider="generic",
                operation="execute.action",
                parameters={"instruction": "get pet details"},
                depends_on=[1],
            ),
        ]
    )

    with patch("app.agents.planner.ai37_planner_bridge.ai37_planner_bridge.discover_if_eligible", return_value=mock_bridge_res), \
         patch("app.agents.task_decomposer.enterprise_task_decomposer.decompose", return_value=mock_decomp_res), \
         patch("app.agents.planner.planner_v4.operation_ranker.rank_operations") as mock_rank_ops:

        mock_rank_ops.return_value = [MagicMock(operation="getOrderById", parameters={})]

        planner.plan(prompt)

        assert mock_rank_ops.call_count == 2
        calls = mock_rank_ops.call_args_list

        # Call 1 should receive task 1 instruction
        assert calls[0].args[0] == "Get store order by ID"
        assert calls[0].kwargs.get("target_provider") == "Petstore"

        # Call 2 should receive task 2 instruction
        assert calls[1].args[0] == "get pet details"
        assert calls[1].kwargs.get("target_provider") == "Petstore"


def test_02_task_instruction_fallback_precedence():
    planner = IntelligentPlannerEngineV4()
    prompt = "Global prompt string"

    mock_bridge_res = MagicMock(
        attempted=True,
        success=True,
        provider="Petstore",
        discovered_ops_count=3,
        url="https://petstore3.swagger.io/api/v3/openapi.json",
        discovered_ops=[],
        error_message=None
    )

    # Task 1: has instruction in parameters
    # Task 2: has no instruction in parameters, but has name
    # Task 3: has no instruction and empty name
    mock_decomp_res = TaskDecompositionResult(
        prompt=prompt,
        intent="dynamic_api",
        tasks=[
            DecomposedTask(
                step=1,
                name="Task Name 1",
                provider="generic",
                operation="execute.action",
                parameters={"instruction": "Instruction 1"},
                depends_on=[],
            ),
            DecomposedTask(
                step=2,
                name="Task Name 2",
                provider="generic",
                operation="execute.action",
                parameters={},
                depends_on=[1],
            ),
            DecomposedTask(
                step=3,
                name="",
                provider="generic",
                operation="execute.action",
                parameters={},
                depends_on=[2],
            ),
        ]
    )

    with patch("app.agents.planner.ai37_planner_bridge.ai37_planner_bridge.discover_if_eligible", return_value=mock_bridge_res), \
         patch("app.agents.task_decomposer.enterprise_task_decomposer.decompose", return_value=mock_decomp_res), \
         patch("app.agents.planner.planner_v4.operation_ranker.rank_operations") as mock_rank_ops:

        mock_rank_ops.return_value = [MagicMock(operation="dummyOp", parameters={})]

        planner.plan(prompt)

        assert mock_rank_ops.call_count == 3
        calls = mock_rank_ops.call_args_list

        # Task 1 uses parameters["instruction"]
        assert calls[0].args[0] == "Instruction 1"
        # Task 2 falls back to task.name
        assert calls[1].args[0] == "Task Name 2"
        # Task 3 falls back to global prompt
        assert calls[2].args[0] == prompt


def test_03_offline_semantic_operation_selection_with_petstore_catalog():
    from app.agents.connector_ai.connector_selector import connector_selector

    orig_ops = list(operation_ranker.OPERATION_CATALOG)
    orig_conn = list(connector_selector.CONNECTOR_CATALOG)

    petstore_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Petstore", "version": "1.0"},
        "paths": {
            "/store/order/{orderId}": {
                "get": {
                    "summary": "Find purchase order by ID",
                    "description": "Get store order by ID",
                    "operationId": "getOrderById",
                    "responses": {"200": {"description": "successful operation"}}
                }
            },
            "/pet/{petId}": {
                "get": {
                    "summary": "Find pet by ID",
                    "description": "get pet details",
                    "operationId": "getPetById",
                    "responses": {"200": {"description": "successful operation"}}
                }
            },
            "/pet/findByStatus": {
                "get": {
                    "summary": "Finds Pets by status",
                    "description": "Finds Pets by status",
                    "operationId": "findPetsByStatus",
                    "responses": {"200": {"description": "successful operation"}}
                }
            }
        }
    }

    try:
        res = dynamic_api_discovery_engine.discover_and_register_api(petstore_spec)
        assert res.success is True

        # 1. Query with "Get store order by ID" -> expects getOrderById
        ops_1 = operation_ranker.rank_operations("Get store order by ID", target_provider="Petstore", top_k=1)
        assert len(ops_1) == 1
        assert ops_1[0].operation == "getOrderById"

        # 2. Query with "get pet by id" -> expects getPetById under Phase 28 raw score tie-breaking
        ops_2 = operation_ranker.rank_operations("get pet by id", target_provider="Petstore", top_k=1)
        assert len(ops_2) == 1
        assert ops_2[0].operation == "getPetById"
    finally:
        operation_ranker.OPERATION_CATALOG.clear()
        operation_ranker.OPERATION_CATALOG.extend(orig_ops)
        connector_selector.CONNECTOR_CATALOG.clear()
        connector_selector.CONNECTOR_CATALOG.extend(orig_conn)

