import pytest
from app.agents.connector_ai.operation_ranker import operation_ranker, OperationRanker

@pytest.fixture
def clean_catalog():
    original = list(operation_ranker.OPERATION_CATALOG)
    yield
    operation_ranker.OPERATION_CATALOG = original

def test_dynamic_operation_request_schema_propagates(clean_catalog):
    custom_op = {
        "provider": "Custom Schema API",
        "operation": "custom.user.create",
        "summary": "Create custom user",
        "parameters": {
            "url": "https://api.custom.com/users",
            "http_method": "POST",
            "method": "POST",
            "is_dynamic_api": True,
            "name": "{{name}}",
            "email": "{{email}}"
        },
        "request_schema": {
            "type": "object",
            "required": ["name", "email"],
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "age": {"type": "integer"}
            }
        },
        "optional_params": ["age"],
        "authentication": "APIKey",
        "keywords": ["create user", "custom user", "user"]
    }
    operation_ranker.OPERATION_CATALOG.append(custom_op)
    results = operation_ranker.rank_operations("Create custom user", target_provider="Custom Schema API", top_k=1)
    assert len(results) == 1
    res = results[0]
    assert res.operation == "custom.user.create"
    assert res.request_schema == custom_op["request_schema"]
    assert res.optional_params == ["age"]

def test_request_schema_preserved_exact_attributes(clean_catalog):
    custom_op = {
        "provider": "Exact Schema API",
        "operation": "exact.item.create",
        "parameters": {"url": "https://api.exact.com/items", "http_method": "POST"},
        "request_schema": {
            "type": "object",
            "required": ["itemId"],
            "properties": {
                "itemId": {"type": "string"},
                "price": {"type": "number"}
            }
        },
        "optional_params": ["price"],
        "authentication": "APIKey",
        "keywords": ["exact item"]
    }
    operation_ranker.OPERATION_CATALOG.append(custom_op)
    results = operation_ranker.rank_operations("Create exact item", target_provider="Exact Schema API", top_k=1)
    res = results[0]
    schema = res.request_schema
    assert schema["type"] == "object"
    assert schema["required"] == ["itemId"]
    assert schema["properties"]["itemId"]["type"] == "string"
    assert schema["properties"]["price"]["type"] == "number"

def test_optional_params_propagates_correctly(clean_catalog):
    custom_op = {
        "provider": "Opt Params API",
        "operation": "opt.item.create",
        "parameters": {},
        "request_schema": {},
        "optional_params": ["opt1", "opt2"],
        "authentication": "APIKey",
        "keywords": ["opt item"]
    }
    operation_ranker.OPERATION_CATALOG.append(custom_op)
    results = operation_ranker.rank_operations("Create opt item", target_provider="Opt Params API", top_k=1)
    assert results[0].optional_params == ["opt1", "opt2"]

def test_missing_request_schema_defaults_to_dict():
    results = operation_ranker.rank_operations("send email", target_provider="Gmail", top_k=1)
    assert len(results) == 1
    res = results[0]
    assert res.provider == "Gmail"
    assert res.request_schema == {}

def test_missing_optional_params_defaults_to_list():
    results = operation_ranker.rank_operations("send email", target_provider="Gmail", top_k=1)
    assert len(results) == 1
    res = results[0]
    assert res.optional_params == []

def test_existing_provider_operation_parameters_unchanged():
    results = operation_ranker.rank_operations("slack message", target_provider="Slack", top_k=1)
    assert len(results) == 1
    res = results[0]
    assert res.provider == "Slack"
    assert res.operation == "slack.chat.postMessage"
    assert "channel" in res.parameters

def test_ranking_score_and_confidence_unchanged(clean_catalog):
    results = operation_ranker.rank_operations("send email", target_provider="Gmail", top_k=1)
    res_before = results[0]

    # Add dummy request_schema metadata to Gmail catalog item
    gmail_op = next(o for o in operation_ranker.OPERATION_CATALOG if o["operation"] == "gmail.messages.send")
    gmail_op["request_schema"] = {"type": "object"}

    results_after = operation_ranker.rank_operations("send email", target_provider="Gmail", top_k=1)
    res_after = results_after[0]

    assert res_before.confidence == res_after.confidence
    assert res_after.request_schema == {"type": "object"}

def test_ranking_order_unchanged(clean_catalog):
    res1 = operation_ranker.rank_operations("send email", top_k=5)
    ops_before = [r.operation for r in res1]
    conf_before = [r.confidence for r in res1]

    # Re-run query
    res2 = operation_ranker.rank_operations("send email", top_k=5)
    ops_after = [r.operation for r in res2]
    conf_after = [r.confidence for r in res2]

    assert ops_before == ops_after
    assert conf_before == conf_after

def test_multiple_operations_preserve_individual_schemas(clean_catalog):
    op1 = {
        "provider": "Multi API",
        "operation": "multi.op1",
        "parameters": {},
        "request_schema": {"type": "object", "title": "Schema1"},
        "optional_params": ["p1"],
        "authentication": "APIKey",
        "keywords": ["alpha"]
    }
    op2 = {
        "provider": "Multi API",
        "operation": "multi.op2",
        "parameters": {},
        "request_schema": {"type": "object", "title": "Schema2"},
        "optional_params": ["p2"],
        "authentication": "APIKey",
        "keywords": ["beta"]
    }
    operation_ranker.OPERATION_CATALOG.extend([op1, op2])

    res1 = operation_ranker.rank_operations("alpha", target_provider="Multi API", top_k=1)[0]
    res2 = operation_ranker.rank_operations("beta", target_provider="Multi API", top_k=1)[0]

    assert res1.request_schema["title"] == "Schema1"
    assert res1.optional_params == ["p1"]
    assert res2.request_schema["title"] == "Schema2"
    assert res2.optional_params == ["p2"]
