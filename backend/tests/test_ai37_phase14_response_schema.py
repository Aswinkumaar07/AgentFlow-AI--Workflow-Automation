import pytest
from app.agents.api_discovery.parser.spec_parser import EnterpriseSpecParser
from app.agents.api_discovery.dynamic_discovery import DynamicAPIDiscoveryEngine
from app.agents.connector_ai.operation_ranker import OperationRanker, OperationResult, operation_ranker
from app.agents.connector_ai.connector_selector import connector_selector


@pytest.fixture(autouse=True)
def clean_catalogs():
    orig_ops = list(operation_ranker.OPERATION_CATALOG)
    orig_conn = list(connector_selector.CONNECTOR_CATALOG)
    yield
    operation_ranker.OPERATION_CATALOG = orig_ops
    connector_selector.CONNECTOR_CATALOG = orig_conn


OPENAPI3_200_RESPONSE_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "200 Response API", "version": "1.0"},
    "paths": {
        "/users/{id}": {
            "get": {
                "operationId": "get_user_200",
                "summary": "Get user details",
                "responses": {
                    "200": {
                        "description": "User profile details",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "name": {"type": "string"},
                                        "email": {"type": "string"}
                                    },
                                    "required": ["id", "name"]
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

OPENAPI3_201_RESPONSE_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "201 Response API", "version": "1.0"},
    "paths": {
        "/items": {
            "post": {
                "operationId": "create_item_201",
                "summary": "Create item",
                "responses": {
                    "201": {
                        "description": "Item created successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "item_id": {"type": "string"},
                                        "status": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

OPENAPI3_NESTED_RESPONSE_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Nested Response API", "version": "1.0"},
    "paths": {
        "/account": {
            "get": {
                "operationId": "get_account_nested",
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "user": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "profile": {
                                                    "type": "object",
                                                    "properties": {
                                                        "bio": {"type": "string"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

OPENAPI3_ARRAY_RESPONSE_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Array Response API", "version": "1.0"},
    "paths": {
        "/products": {
            "get": {
                "operationId": "list_products_array",
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "product_id": {"type": "string"},
                                            "price": {"type": "number"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

OPENAPI3_NO_RESPONSES_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "No Responses API", "version": "1.0"},
    "paths": {
        "/ping": {
            "get": {
                "operationId": "ping_no_response"
            }
        }
    }
}

OPENAPI3_NON_JSON_RESPONSE_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Non-JSON Response API", "version": "1.0"},
    "paths": {
        "/download": {
            "get": {
                "operationId": "download_file",
                "responses": {
                    "200": {
                        "description": "Binary payload",
                        "content": {
                            "application/pdf": {
                                "schema": {"type": "string", "format": "binary"}
                            }
                        }
                    }
                }
            }
        }
    }
}


def test_01_openapi3_200_application_json_response_parsing():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(OPENAPI3_200_RESPONSE_SPEC)
    assert len(endpoints) == 1
    ep = endpoints[0]
    schema = ep.response_schema
    assert isinstance(schema, dict)
    assert schema.get("type") == "object"
    props = schema.get("properties", {})
    assert "id" in props
    assert "name" in props
    assert "email" in props
    assert props["id"]["type"] == "integer"


def test_02_openapi3_201_application_json_response_parsing():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(OPENAPI3_201_RESPONSE_SPEC)
    assert len(endpoints) == 1
    ep = endpoints[0]
    schema = ep.response_schema
    assert schema.get("type") == "object"
    props = schema.get("properties", {})
    assert "item_id" in props
    assert "status" in props


def test_03_response_schema_nested_object_preservation():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(OPENAPI3_NESTED_RESPONSE_SPEC)
    ep = endpoints[0]
    schema = ep.response_schema
    assert schema.get("type") == "object"
    user_prop = schema["properties"]["user"]
    assert user_prop["type"] == "object"
    assert "id" in user_prop["properties"]
    assert "profile" in user_prop["properties"]
    assert user_prop["properties"]["profile"]["properties"]["bio"]["type"] == "string"


def test_04_response_schema_array_items_preservation():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(OPENAPI3_ARRAY_RESPONSE_SPEC)
    ep = endpoints[0]
    schema = ep.response_schema
    assert schema.get("type") == "array"
    items = schema.get("items", {})
    assert items.get("type") == "object"
    assert "product_id" in items["properties"]
    assert "price" in items["properties"]


def test_05_operation_without_responses_produces_empty_response_schema():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(OPENAPI3_NO_RESPONSES_SPEC)
    ep = endpoints[0]
    assert ep.response_schema == {}


def test_06_non_json_response_only_produces_empty_response_schema():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(OPENAPI3_NON_JSON_RESPONSE_SPEC)
    ep = endpoints[0]
    assert ep.response_schema == {}


def test_07_dynamic_discovery_propagates_response_schema():
    engine = DynamicAPIDiscoveryEngine()
    result = engine.discover_and_register_api(OPENAPI3_200_RESPONSE_SPEC)
    assert result.success is True
    op = result.connector_spec.operations[0]
    assert "response_schema" in op
    assert op["response_schema"]["properties"]["email"]["type"] == "string"


def test_08_operation_result_propagates_response_schema():
    engine = DynamicAPIDiscoveryEngine()
    result = engine.discover_and_register_api(OPENAPI3_200_RESPONSE_SPEC)
    assert result.success is True

    ranked = operation_ranker.rank_operations("Get user details email")
    assert len(ranked) > 0
    top_op = next((r for r in ranked if r.operation == "get_user_200"), None)
    assert top_op is not None
    assert top_op.response_schema != {}
    assert "email" in top_op.response_schema["properties"]


def test_09_regression_request_schema_remains_intact():
    request_and_response_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Req Res API", "version": "1.0"},
        "paths": {
            "/resource": {
                "post": {
                    "operationId": "create_resource",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"req_field": {"type": "string"}}
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"res_field": {"type": "string"}}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    parser = EnterpriseSpecParser()
    ep = parser.parse_spec(request_and_response_spec)[0]
    assert ep.request_schema["properties"]["req_field"]["type"] == "string"
    assert ep.response_schema["properties"]["res_field"]["type"] == "string"


def test_10_regression_params_and_security_metadata_remain_intact():
    full_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Full Spec API", "version": "1.0"},
        "components": {
            "securitySchemes": {
                "HeaderKey": {"type": "apiKey", "name": "X-API-Key", "in": "header"}
            }
        },
        "security": [{"HeaderKey": []}],
        "paths": {
            "/resource": {
                "get": {
                    "operationId": "get_full_resource",
                    "parameters": [
                        {"name": "filter", "in": "query", "required": False},
                        {"name": "X-Trace", "in": "header", "required": True}
                    ],
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object", "properties": {"ok": {"type": "boolean"}}}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    parser = EnterpriseSpecParser()
    ep = parser.parse_spec(full_spec)[0]
    assert "filter" in ep.query_params
    assert "X-Trace" in ep.header_params
    assert "HeaderKey" in ep.security_schemes
    assert ep.security_requirements == [{"HeaderKey": []}]
    assert ep.response_schema["properties"]["ok"]["type"] == "boolean"
