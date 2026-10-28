import pytest
from app.agents.api_discovery.parser.spec_parser import EnterpriseSpecParser
from app.agents.planner.parameter_mapper import ResponseToRequestParameterMapper


@pytest.fixture
def parser():
    return EnterpriseSpecParser()


def test_01_openapi3_local_ref_dereferencing(parser):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Order API", "version": "1.0"},
        "paths": {
            "/store/order/{orderId}": {
                "get": {
                    "operationId": "getOrderById",
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Order"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Order": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "petId": {"type": "integer"},
                        "quantity": {"type": "integer"},
                        "status": {"type": "string"}
                    }
                }
            }
        }
    }
    endpoints = parser.parse_spec(spec)
    assert len(endpoints) == 1
    resp_schema = endpoints[0].response_schema
    assert "properties" in resp_schema
    assert "petId" in resp_schema["properties"]
    assert resp_schema["properties"]["petId"]["type"] == "integer"


def test_02_swagger2_local_ref_dereferencing(parser):
    spec = {
        "swagger": "2.0",
        "info": {"title": "Swagger Order API", "version": "1.0"},
        "paths": {
            "/store/order/{orderId}": {
                "get": {
                    "operationId": "getOrderById",
                    "responses": {
                        "200": {
                            "schema": {"$ref": "#/definitions/Order"}
                        }
                    }
                }
            }
        },
        "definitions": {
            "Order": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "petId": {"type": "integer"}
                }
            }
        }
    }
    endpoints = parser.parse_spec(spec)
    assert len(endpoints) == 1
    resp_schema = endpoints[0].response_schema
    assert "properties" in resp_schema
    assert "petId" in resp_schema["properties"]


def test_03_nested_ref_dereferencing(parser):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Nested API", "version": "1.0"},
        "paths": {
            "/order": {
                "get": {
                    "operationId": "getOrder",
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Order"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Order": {
                    "type": "object",
                    "properties": {
                        "customer": {"$ref": "#/components/schemas/Customer"}
                    }
                },
                "Customer": {
                    "type": "object",
                    "properties": {
                        "address": {"$ref": "#/components/schemas/Address"}
                    }
                },
                "Address": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                        "zip": {"type": "string"}
                    }
                }
            }
        }
    }
    endpoints = parser.parse_spec(spec)
    resp_schema = endpoints[0].response_schema
    assert "customer" in resp_schema["properties"]
    assert "address" in resp_schema["properties"]["customer"]["properties"]
    assert "city" in resp_schema["properties"]["customer"]["properties"]["address"]["properties"]


def test_04_array_item_ref_dereferencing(parser):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Pet List API", "version": "1.0"},
        "paths": {
            "/pets": {
                "get": {
                    "operationId": "getPets",
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Pet"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Pet": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"}
                    }
                }
            }
        }
    }
    endpoints = parser.parse_spec(spec)
    resp_schema = endpoints[0].response_schema
    assert resp_schema["type"] == "array"
    assert "items" in resp_schema
    assert "properties" in resp_schema["items"]
    assert "id" in resp_schema["items"]["properties"]


def test_05_circular_ref_safety(parser):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Node API", "version": "1.0"},
        "paths": {
            "/node": {
                "get": {
                    "operationId": "getNode",
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Node"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Node": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "parent": {"$ref": "#/components/schemas/Node"}
                    }
                }
            }
        }
    }
    # Should resolve first level and stop circular loop safely without stack overflow
    endpoints = parser.parse_spec(spec)
    assert len(endpoints) == 1
    resp_schema = endpoints[0].response_schema
    assert "properties" in resp_schema
    assert "id" in resp_schema["properties"]


def test_06_missing_local_ref_fallback(parser):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Missing Ref API", "version": "1.0"},
        "paths": {
            "/item": {
                "get": {
                    "operationId": "getItem",
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/NonExistent"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    endpoints = parser.parse_spec(spec)
    assert len(endpoints) == 1
    resp_schema = endpoints[0].response_schema
    assert isinstance(resp_schema, dict)


def test_07_external_ref_rejection(parser):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "External Ref API", "version": "1.0"},
        "paths": {
            "/item": {
                "get": {
                    "operationId": "getItem",
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "https://example.com/external_schema.json"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    endpoints = parser.parse_spec(spec)
    assert len(endpoints) == 1
    resp_schema = endpoints[0].response_schema
    assert resp_schema.get("$ref") == "https://example.com/external_schema.json"


def test_08_response_schema_integration_exposes_pet_id(parser):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Petstore Integration API", "version": "1.0"},
        "paths": {
            "/store/order/{orderId}": {
                "get": {
                    "operationId": "getOrderById",
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Order"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Order": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "petId": {"type": "integer"},
                        "quantity": {"type": "integer"},
                        "status": {"type": "string"}
                    }
                }
            }
        }
    }
    endpoints = parser.parse_spec(spec)
    assert len(endpoints) == 1
    resp_schema = endpoints[0].response_schema
    assert "properties" in resp_schema
    assert "petId" in resp_schema["properties"]


def test_09_existing_inline_schema_regression(parser):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Inline API", "version": "1.0"},
        "paths": {
            "/inline": {
                "get": {
                    "operationId": "getInline",
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
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
    endpoints = parser.parse_spec(spec)
    assert len(endpoints) == 1
    resp_schema = endpoints[0].response_schema
    assert resp_schema["properties"]["status"]["type"] == "string"


def test_10_mapper_integration_generates_variable_expression(parser):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Order Pet Chaining API", "version": "1.0"},
        "paths": {
            "/store/order/{orderId}": {
                "get": {
                    "operationId": "getOrderById",
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Order"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Order": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "petId": {"type": "integer"},
                        "quantity": {"type": "integer"},
                        "status": {"type": "string"}
                    }
                }
            }
        }
    }
    endpoints = parser.parse_spec(spec)
    dereferenced_resp_schema = endpoints[0].response_schema

    # Feed dereferenced response schema to frozen ResponseToRequestParameterMapper
    mapper = ResponseToRequestParameterMapper()
    result = mapper.map_parameters(
        upstream_node_id="step_1",
        upstream_response_schema=dereferenced_resp_schema,
        downstream_required_params=["petId"]
    )
    assert result.mappings == {"petId": "{{step_1.data.petId}}"}
