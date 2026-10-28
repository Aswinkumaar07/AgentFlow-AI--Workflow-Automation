import pytest
from app.agents.api_discovery.dynamic_discovery import DynamicAPIDiscoveryEngine
from app.agents.connector_ai.operation_ranker import operation_ranker

@pytest.fixture
def discovery_engine():
    return DynamicAPIDiscoveryEngine()

def test_openapi3_requestbody_schema_survives_to_op_dict(discovery_engine):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Discovery Bridge API", "version": "1.0.0"},
        "servers": [{"url": "https://example.com/api/v1"}],
        "paths": {
            "/users": {
                "post": {
                    "operationId": "createUserBridge",
                    "requestBody": {
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
    result = discovery_engine.discover_and_register_api(spec)
    assert result.success is True
    op_dict = result.connector_spec.operations[0]
    assert op_dict["operation"] == "createUserBridge"
    assert "request_schema" in op_dict
    assert op_dict["request_schema"]["type"] == "object"

def test_registered_op_dict_contains_request_schema(discovery_engine):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Schema Test API", "version": "1.0.0"},
        "paths": {
            "/items": {
                "post": {
                    "operationId": "createItemBridge",
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
    result = discovery_engine.discover_and_register_api(spec)
    op_dict = result.connector_spec.operations[0]
    assert op_dict["request_schema"] == {
        "type": "object",
        "properties": {"title": {"type": "string"}}
    }

def test_request_schema_preserves_type_required_properties(discovery_engine):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Preserve Test API", "version": "1.0.0"},
        "paths": {
            "/orders": {
                "post": {
                    "operationId": "createOrderBridge",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["orderId", "amount"],
                                    "properties": {
                                        "orderId": {"type": "string"},
                                        "amount": {"type": "number"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    result = discovery_engine.discover_and_register_api(spec)
    op_dict = result.connector_spec.operations[0]
    schema = op_dict["request_schema"]
    assert schema["type"] == "object"
    assert schema["required"] == ["orderId", "amount"]
    assert schema["properties"]["orderId"]["type"] == "string"
    assert schema["properties"]["amount"]["type"] == "number"

def test_required_body_fields_in_parameter_templates(discovery_engine):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Template Test API", "version": "1.0.0"},
        "paths": {
            "/pets": {
                "post": {
                    "operationId": "addPetBridge",
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
    result = discovery_engine.discover_and_register_api(spec)
    op_dict = result.connector_spec.operations[0]
    params = op_dict["parameters"]
    assert params["petName"] == "{{petName}}"
    assert params["category"] == "{{category}}"

def test_optional_body_field_metadata_survives(discovery_engine):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Optional Test API", "version": "1.0.0"},
        "paths": {
            "/pets": {
                "post": {
                    "operationId": "addPetOptionalBridge",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "tag": {"type": "string"},
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
    result = discovery_engine.discover_and_register_api(spec)
    op_dict = result.connector_spec.operations[0]
    assert "optional_params" in op_dict
    assert "tag" in op_dict["optional_params"]
    assert "status" in op_dict["optional_params"]

def test_operation_without_requestbody_compatible(discovery_engine):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Get Test API", "version": "1.0.0"},
        "paths": {
            "/health": {
                "get": {
                    "operationId": "getHealthBridge",
                    "summary": "Health check"
                }
            }
        }
    }
    result = discovery_engine.discover_and_register_api(spec)
    op_dict = result.connector_spec.operations[0]
    assert op_dict["request_schema"] == {}
    assert op_dict["optional_params"] == []

def test_existing_url_http_method_metadata_unchanged(discovery_engine):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Metadata Test API", "version": "1.0.0"},
        "servers": [{"url": "https://api.example.com/v2"}],
        "paths": {
            "/tasks": {
                "post": {
                    "operationId": "createTaskBridge",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"taskName": {"type": "string"}}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    result = discovery_engine.discover_and_register_api(spec)
    op_dict = result.connector_spec.operations[0]
    params = op_dict["parameters"]
    assert params["url"] == "https://api.example.com/v2/tasks"
    assert params["http_method"] == "POST"
    assert params["method"] == "POST"
    assert params["is_dynamic_api"] is True

def test_existing_dynamic_operation_registration_still_works(discovery_engine):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Registration Test API", "version": "1.0.0"},
        "paths": {
            "/widgets": {
                "post": {
                    "operationId": "createWidgetBridge",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"widgetName": {"type": "string"}}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    discovery_engine.discover_and_register_api(spec)
    cat_op = next((o for o in operation_ranker.OPERATION_CATALOG if o["operation"] == "createWidgetBridge"), None)
    assert cat_op is not None
    assert cat_op["request_schema"] == {"type": "object", "properties": {"widgetName": {"type": "string"}}}
    assert cat_op["optional_params"] == ["widgetName"]
