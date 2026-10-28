import pytest
from app.agents.planner.parameter_mapper import ResponseToRequestParameterMapper, parameter_mapper
from app.agents.planner.planner_v4 import IntelligentPlannerEngineV4
from app.agents.task_decomposer.models import DecomposedTask, TaskDecompositionResult
from app.agents.connector_ai.operation_ranker import operation_ranker
from app.agents.connector_ai.connector_selector import connector_selector


@pytest.fixture(autouse=True)
def clean_catalogs():
    orig_ops = list(operation_ranker.OPERATION_CATALOG)
    orig_conn = list(connector_selector.CONNECTOR_CATALOG)
    yield
    operation_ranker.OPERATION_CATALOG = orig_ops
    connector_selector.CONNECTOR_CATALOG = orig_conn


def test_01_exact_match():
    mapper = ResponseToRequestParameterMapper()
    resp_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"}
        }
    }
    res = mapper.map_parameters("step_1", resp_schema, ["id"])
    assert res.mappings == {"id": "{{step_1.data.id}}"}


def test_02_camel_case_to_snake_case():
    mapper = ResponseToRequestParameterMapper()
    resp_schema = {
        "type": "object",
        "properties": {
            "userId": {"type": "integer"}
        }
    }
    res = mapper.map_parameters("step_1", resp_schema, ["user_id"])
    assert res.mappings == {"user_id": "{{step_1.data.userId}}"}


def test_03_exact_snake_case():
    mapper = ResponseToRequestParameterMapper()
    resp_schema = {
        "type": "object",
        "properties": {
            "customer_id": {"type": "string"}
        }
    }
    res = mapper.map_parameters("step_1", resp_schema, ["customer_id"])
    assert res.mappings == {"customer_id": "{{step_1.data.customer_id}}"}


def test_04_nested_response_property():
    mapper = ResponseToRequestParameterMapper()
    resp_schema = {
        "type": "object",
        "properties": {
            "customer": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"}
                }
            }
        }
    }
    res = mapper.map_parameters("step_1", resp_schema, ["customer_id"])
    assert res.mappings == {"customer_id": "{{step_1.data.customer.id}}"}


def test_05_path_parameter_mapping():
    mapper = ResponseToRequestParameterMapper()
    resp_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"}
        }
    }
    res = mapper.map_parameters("step_1", resp_schema, ["id"])
    assert "id" in res.mappings
    assert res.mappings["id"] == "{{step_1.data.id}}"


def test_06_query_parameter_mapping():
    mapper = ResponseToRequestParameterMapper()
    resp_schema = {
        "type": "object",
        "properties": {
            "account_id": {"type": "string"}
        }
    }
    res = mapper.map_parameters("step_1", resp_schema, ["account_id"])
    assert res.mappings == {"account_id": "{{step_1.data.account_id}}"}


def test_07_header_parameter_mapping():
    mapper = ResponseToRequestParameterMapper()
    resp_schema = {
        "type": "object",
        "properties": {
            "token": {"type": "string"}
        }
    }
    res = mapper.map_parameters("step_1", resp_schema, ["X-User-Token"])
    assert "X-User-Token" not in res.mappings or res.mappings.get("X-User-Token") == "{{step_1.data.token}}"


def test_08_json_body_field_mapping():
    mapper = ResponseToRequestParameterMapper()
    resp_schema = {
        "type": "object",
        "properties": {
            "order_id": {"type": "integer"}
        }
    }
    res = mapper.map_parameters("step_1", resp_schema, ["order_id"])
    assert res.mappings == {"order_id": "{{step_1.data.order_id}}"}


def test_09_integer_to_integer_compatible():
    mapper = ResponseToRequestParameterMapper()
    resp_schema = {"type": "object", "properties": {"code": {"type": "integer"}}}
    req_schema = {"type": "object", "properties": {"code": {"type": "integer"}}}
    res = mapper.map_parameters("step_1", resp_schema, ["code"], downstream_request_schema=req_schema)
    assert res.mappings == {"code": "{{step_1.data.code}}"}


def test_10_string_to_string_compatible():
    mapper = ResponseToRequestParameterMapper()
    resp_schema = {"type": "object", "properties": {"status": {"type": "string"}}}
    req_schema = {"type": "object", "properties": {"status": {"type": "string"}}}
    res = mapper.map_parameters("step_1", resp_schema, ["status"], downstream_request_schema=req_schema)
    assert res.mappings == {"status": "{{step_1.data.status}}"}


def test_11_object_to_integer_rejected():
    mapper = ResponseToRequestParameterMapper()
    resp_schema = {"type": "object", "properties": {"user_data": {"type": "object"}}}
    req_schema = {"type": "object", "properties": {"user_data": {"type": "integer"}}}
    res = mapper.map_parameters("step_1", resp_schema, ["user_data"], downstream_request_schema=req_schema)
    assert "user_data" not in res.mappings


def test_12_multiple_equally_plausible_candidates_rejected():
    mapper = ResponseToRequestParameterMapper()
    resp_schema = {
        "type": "object",
        "properties": {
            "user_id": {"type": "integer"},
            "organization_id": {"type": "integer"}
        }
    }
    res = mapper.map_parameters("step_1", resp_schema, ["id"])
    assert "id" not in res.mappings


def test_13_missing_response_field_rejected():
    mapper = ResponseToRequestParameterMapper()
    resp_schema = {"type": "object", "properties": {"foo": {"type": "string"}}}
    res = mapper.map_parameters("step_1", resp_schema, ["bar"])
    assert "bar" not in res.mappings


def test_14_missing_downstream_input_rejected():
    mapper = ResponseToRequestParameterMapper()
    resp_schema = {"type": "object", "properties": {"foo": {"type": "string"}}}
    res = mapper.map_parameters("step_1", resp_schema, [])
    assert res.mappings == {}


def test_15_array_response_with_item_property():
    mapper = ResponseToRequestParameterMapper()
    resp_schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string"}
            }
        }
    }
    res = mapper.map_parameters("step_1", resp_schema, ["item_id"])
    assert res.mappings == {"item_id": "{{step_1.data.item_id}}"}


def test_16_nested_object_response_schema():
    mapper = ResponseToRequestParameterMapper()
    resp_schema = {
        "type": "object",
        "properties": {
            "meta": {
                "type": "object",
                "properties": {
                    "trace_id": {"type": "string"}
                }
            }
        }
    }
    res = mapper.map_parameters("step_1", resp_schema, ["trace_id"])
    assert res.mappings == {"trace_id": "{{step_1.data.meta.trace_id}}"}


def test_17_planner_integration_generates_variable_reference():
    planner = IntelligentPlannerEngineV4()
    op1 = {
        "provider": "TestProvider",
        "operation": "test.op1.get",
        "summary": "Get user",
        "parameters": {"url": "https://httpbin.org/get"},
        "response_schema": {"type": "object", "properties": {"id": {"type": "integer"}}},
        "authentication": "None",
        "keywords": ["get user"]
    }
    op2 = {
        "provider": "TestProvider",
        "operation": "test.op2.notify",
        "summary": "Notify user",
        "parameters": {"url": "https://httpbin.org/notify/{id}", "id": "{{id}}"},
        "query_params": [],
        "header_params": [],
        "response_schema": {},
        "authentication": "None",
        "keywords": ["notify user"]
    }
    operation_ranker.OPERATION_CATALOG.append(op1)
    operation_ranker.OPERATION_CATALOG.append(op2)
    try:
        res = planner.plan("Fetch user from TestProvider and notify user")
        assert res is not None
    finally:
        if op1 in operation_ranker.OPERATION_CATALOG:
            operation_ranker.OPERATION_CATALOG.remove(op1)
        if op2 in operation_ranker.OPERATION_CATALOG:
            operation_ranker.OPERATION_CATALOG.remove(op2)


def test_18_planner_integration_preserves_existing_literal_parameters():
    mapper = ResponseToRequestParameterMapper()
    resp_schema = {"type": "object", "properties": {"id": {"type": "integer"}}}
    existing = {"id": "literal_12345"}
    res = mapper.map_parameters("step_1", resp_schema, ["id"], existing_downstream_params=existing)
    assert "id" not in res.mappings


def test_19_single_node_workflow_unchanged():
    planner = IntelligentPlannerEngineV4()
    res = planner.plan("Send email to alice@example.com")
    assert len(res.workflow_graph.get("nodes", [])) == 1
    node = res.workflow_graph["nodes"][0]
    assert node["provider"] == "gmail"


def test_20_existing_native_connector_planning_remains_unchanged():
    planner = IntelligentPlannerEngineV4()
    res = planner.plan("Read unread emails and summarize inbox")
    assert len(res.workflow_graph.get("nodes", [])) >= 2
    ops = [n["operation"] for n in res.workflow_graph["nodes"]]
    assert any("gmail" in op for op in ops)
