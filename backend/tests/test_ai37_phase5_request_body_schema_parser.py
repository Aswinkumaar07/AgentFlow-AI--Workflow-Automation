import pytest
from app.agents.api_discovery.parser.spec_parser import EnterpriseSpecParser

@pytest.fixture
def parser():
    return EnterpriseSpecParser()

def test_openapi3_json_requestbody_parsing(parser):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "post": {
                    "operationId": "createUser",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["name", "email"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "email": {"type": "string"},
                                        "age": {"type": "integer"}
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
    ep = endpoints[0]
    assert ep.operation_id == "createUser"
    assert "name" in ep.required_params
    assert "email" in ep.required_params
    assert "age" in ep.optional_params
    assert ep.request_schema.get("type") == "object"
    assert "name" in ep.request_schema.get("properties", {})

def test_request_schema_stored(parser):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/items": {
                "post": {
                    "operationId": "createItem",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"title": {"type": "string"}}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    endpoints = parser.parse_spec(spec)
    ep = endpoints[0]
    assert ep.request_schema == {
        "type": "object",
        "properties": {"title": {"type": "string"}}
    }

def test_required_body_properties_detected(parser):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/pets": {
                "post": {
                    "operationId": "addPet",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["petName", "category"],
                                    "properties": {
                                        "petName": {"type": "string"},
                                        "category": {"type": "string"}
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
    ep = endpoints[0]
    assert "petName" in ep.required_params
    assert "category" in ep.required_params
    assert len(ep.optional_params) == 0

def test_optional_body_properties_detected(parser):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/pets": {
                "post": {
                    "operationId": "addPetOptional",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "tags": {"type": "array"},
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
    endpoints = parser.parse_spec(spec)
    ep = endpoints[0]
    assert "tags" in ep.optional_params
    assert "status" in ep.optional_params
    assert len(ep.required_params) == 0

def test_primitive_types_preserved_in_schema(parser):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/data": {
                "post": {
                    "operationId": "postData",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "count": {"type": "integer"},
                                        "price": {"type": "number"},
                                        "active": {"type": "boolean"}
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
    props = endpoints[0].request_schema.get("properties", {})
    assert props["count"]["type"] == "integer"
    assert props["price"]["type"] == "number"
    assert props["active"]["type"] == "boolean"

def test_operation_without_requestbody_unchanged(parser):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/status": {
                "get": {
                    "operationId": "getStatus",
                    "summary": "Check status"
                }
            }
        }
    }
    endpoints = parser.parse_spec(spec)
    ep = endpoints[0]
    assert ep.operation_id == "getStatus"
    assert ep.request_schema == {}
    assert ep.required_params == []
    assert ep.optional_params == []

def test_existing_parameters_parsing_unchanged(parser):
    spec = {
        "swagger": "2.0",
        "info": {"title": "Swagger API", "version": "2.0"},
        "paths": {
            "/user/{username}": {
                "get": {
                    "operationId": "getUser",
                    "parameters": [
                        {"name": "username", "in": "path", "required": True},
                        {"name": "verbose", "in": "query", "required": False}
                    ]
                }
            }
        }
    }
    endpoints = parser.parse_spec(spec)
    ep = endpoints[0]
    assert ep.operation_id == "getUser"
    assert ep.required_params == ["username"]
    assert ep.optional_params == ["verbose"]
    assert ep.request_schema == {}

def test_multiple_operations_mixed_requestbody(parser):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Mixed API", "version": "1.0.0"},
        "paths": {
            "/resource": {
                "get": {
                    "operationId": "getResource",
                    "parameters": [{"name": "id", "in": "query", "required": True}]
                },
                "post": {
                    "operationId": "createResource",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"title": {"type": "string"}}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    endpoints = parser.parse_spec(spec)
    assert len(endpoints) == 2
    get_ep = next(e for e in endpoints if e.http_method == "GET")
    post_ep = next(e for e in endpoints if e.http_method == "POST")
    assert get_ep.required_params == ["id"]
    assert get_ep.request_schema == {}
    assert "title" in post_ep.optional_params
    assert post_ep.request_schema == {"type": "object", "properties": {"title": {"type": "string"}}}

def test_application_json_selected_over_other_media_types(parser):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "MultiMedia API", "version": "1.0.0"},
        "paths": {
            "/upload": {
                "post": {
                    "operationId": "uploadData",
                    "requestBody": {
                        "content": {
                            "text/plain": {
                                "schema": {"type": "string"}
                            },
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"jsonField": {"type": "string"}}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    endpoints = parser.parse_spec(spec)
    ep = endpoints[0]
    assert "jsonField" in ep.optional_params
    assert ep.request_schema["properties"] == {"jsonField": {"type": "string"}}

def test_malformed_requestbody_schema_handled_gracefully(parser):
    malformed_specs = [
        # Missing schema key inside content
        {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {"/test": {"post": {"operationId": "op1", "requestBody": {"content": {"application/json": {}}}}}}
        },
        # requestBody is not a dict
        {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {"/test": {"post": {"operationId": "op2", "requestBody": "invalid"}}}
        },
        # schema is not a dict
        {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {"/test": {"post": {"operationId": "op3", "requestBody": {"content": {"application/json": {"schema": "invalid"}}}}}}
        }
    ]
    for spec in malformed_specs:
        endpoints = parser.parse_spec(spec)
        assert len(endpoints) == 1
        assert endpoints[0].request_schema == {}
