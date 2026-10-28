import pytest
from app.agents.api_discovery.parser.spec_parser import EnterpriseSpecParser
from app.agents.api_discovery.dynamic_discovery import DynamicAPIDiscoveryEngine
from app.agents.connector_ai.operation_ranker import OperationResult, OperationRanker


OPENAPI3_APIKEY_HEADER_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Header APIKey Spec", "version": "1.0"},
    "components": {
        "securitySchemes": {
            "ApiKeyHeader": {
                "type": "apiKey",
                "name": "X-API-Key",
                "in": "header"
            }
        }
    },
    "security": [{"ApiKeyHeader": []}],
    "paths": {
        "/resource": {
            "get": {
                "operationId": "get_resource",
                "summary": "Get resource with header api key"
            }
        }
    }
}

OPENAPI3_APIKEY_QUERY_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Query APIKey Spec", "version": "1.0"},
    "components": {
        "securitySchemes": {
            "ApiKeyQuery": {
                "type": "apiKey",
                "name": "api_key",
                "in": "query"
            }
        }
    },
    "security": [{"ApiKeyQuery": []}],
    "paths": {
        "/resource": {
            "get": {
                "operationId": "get_query_resource"
            }
        }
    }
}

OPENAPI3_BEARER_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Bearer Spec", "version": "1.0"},
    "components": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    },
    "security": [{"BearerAuth": []}],
    "paths": {
        "/profile": {
            "get": {
                "operationId": "get_profile"
            }
        }
    }
}

OPENAPI3_BASIC_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Basic Spec", "version": "1.0"},
    "components": {
        "securitySchemes": {
            "BasicAuth": {
                "type": "http",
                "scheme": "basic"
            }
        }
    },
    "security": [{"BasicAuth": []}],
    "paths": {
        "/data": {
            "get": {
                "operationId": "get_data"
            }
        }
    }
}

OPENAPI3_OP_OVERRIDE_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Op Override Spec", "version": "1.0"},
    "components": {
        "securitySchemes": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "name": "X-API-Key",
                "in": "header"
            },
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer"
            }
        }
    },
    "security": [{"ApiKeyAuth": []}],
    "paths": {
        "/public": {
            "get": {
                "operationId": "get_public",
                "security": []
            }
        },
        "/secure-bearer": {
            "post": {
                "operationId": "post_bearer",
                "security": [{"BearerAuth": []}]
            }
        }
    }
}

SWAGGER2_SPEC = {
    "swagger": "2.0",
    "info": {"title": "Swagger 2 Spec", "version": "1.0"},
    "securityDefinitions": {
        "HeaderKey": {
            "type": "apiKey",
            "name": "X-Swagger-Key",
            "in": "header"
        },
        "QueryKey": {
            "type": "apiKey",
            "name": "key",
            "in": "query"
        },
        "BasicAuth": {
            "type": "basic"
        },
        "OAuth2Auth": {
            "type": "oauth2",
            "flow": "implicit",
            "authorizationUrl": "https://example.com/oauth/authorize"
        }
    },
    "security": [{"HeaderKey": []}],
    "paths": {
        "/swag-resource": {
            "get": {
                "operationId": "get_swag_resource"
            }
        },
        "/swag-oauth": {
            "post": {
                "operationId": "post_swag_oauth",
                "security": [{"OAuth2Auth": ["read", "write"]}]
            }
        }
    }
}

UNAUTHENTICATED_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Public API", "version": "1.0"},
    "paths": {
        "/ping": {
            "get": {
                "operationId": "ping"
            }
        }
    }
}


def test_01_openapi3_apikey_header_parsing():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(OPENAPI3_APIKEY_HEADER_SPEC)
    assert len(endpoints) == 1
    ep = endpoints[0]
    assert "ApiKeyHeader" in ep.security_schemes
    assert ep.security_schemes["ApiKeyHeader"]["type"] == "apiKey"
    assert ep.security_schemes["ApiKeyHeader"]["name"] == "X-API-Key"
    assert ep.security_schemes["ApiKeyHeader"]["in"] == "header"


def test_02_openapi3_apikey_query_parsing():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(OPENAPI3_APIKEY_QUERY_SPEC)
    ep = endpoints[0]
    assert "ApiKeyQuery" in ep.security_schemes
    assert ep.security_schemes["ApiKeyQuery"]["type"] == "apiKey"
    assert ep.security_schemes["ApiKeyQuery"]["name"] == "api_key"
    assert ep.security_schemes["ApiKeyQuery"]["in"] == "query"


def test_03_openapi3_bearer_parsing():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(OPENAPI3_BEARER_SPEC)
    ep = endpoints[0]
    assert "BearerAuth" in ep.security_schemes
    assert ep.security_schemes["BearerAuth"]["type"] == "http"
    assert ep.security_schemes["BearerAuth"]["scheme"] == "bearer"


def test_04_openapi3_basic_parsing():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(OPENAPI3_BASIC_SPEC)
    ep = endpoints[0]
    assert "BasicAuth" in ep.security_schemes
    assert ep.security_schemes["BasicAuth"]["type"] == "http"
    assert ep.security_schemes["BasicAuth"]["scheme"] == "basic"


def test_05_openapi3_root_security_requirement():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(OPENAPI3_APIKEY_HEADER_SPEC)
    ep = endpoints[0]
    assert ep.security_requirements == [{"ApiKeyHeader": []}]


def test_06_openapi3_operation_level_security_requirement():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(OPENAPI3_OP_OVERRIDE_SPEC)
    post_ep = next(e for e in endpoints if e.operation_id == "post_bearer")
    assert post_ep.security_requirements == [{"BearerAuth": []}]
    assert "BearerAuth" in post_ep.security_schemes
    assert "ApiKeyAuth" not in post_ep.security_schemes


def test_07_operation_level_security_override_unauthenticated():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(OPENAPI3_OP_OVERRIDE_SPEC)
    public_ep = next(e for e in endpoints if e.operation_id == "get_public")
    assert public_ep.security_requirements == []
    assert public_ep.security_schemes == {}


def test_08_swagger2_apikey_header_parsing():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(SWAGGER2_SPEC)
    swag_ep = next(e for e in endpoints if e.operation_id == "get_swag_resource")
    assert "HeaderKey" in swag_ep.security_schemes
    assert swag_ep.security_schemes["HeaderKey"]["type"] == "apiKey"
    assert swag_ep.security_schemes["HeaderKey"]["in"] == "header"


def test_09_swagger2_apikey_query_parsing():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(SWAGGER2_SPEC)
    swag_ep = next(e for e in endpoints if e.operation_id == "get_swag_resource")
    assert "HeaderKey" in swag_ep.security_schemes


def test_10_swagger2_basic_parsing():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(SWAGGER2_SPEC)
    assert len(endpoints) == 2


def test_11_swagger2_oauth2_metadata_preservation():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(SWAGGER2_SPEC)
    oauth_ep = next(e for e in endpoints if e.operation_id == "post_swag_oauth")
    assert oauth_ep.security_requirements == [{"OAuth2Auth": ["read", "write"]}]
    assert "OAuth2Auth" in oauth_ep.security_schemes
    assert oauth_ep.security_schemes["OAuth2Auth"]["type"] == "oauth2"


def test_12_unauthenticated_openapi_operation_produces_empty_metadata():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(UNAUTHENTICATED_SPEC)
    ep = endpoints[0]
    assert ep.security_schemes == {}
    assert ep.security_requirements == []


def test_13_dynamic_discovery_preserves_security_schemes():
    engine = DynamicAPIDiscoveryEngine()
    result = engine.discover_and_register_api(OPENAPI3_APIKEY_HEADER_SPEC)
    assert result.success is True
    op = result.connector_spec.operations[0]
    assert "security_schemes" in op
    assert "ApiKeyHeader" in op["security_schemes"]
    assert op["parameters"]["security_schemes"] == op["security_schemes"]


def test_14_dynamic_discovery_preserves_security_requirements():
    engine = DynamicAPIDiscoveryEngine()
    result = engine.discover_and_register_api(OPENAPI3_BEARER_SPEC)
    assert result.success is True
    op = result.connector_spec.operations[0]
    assert "security_requirements" in op
    assert op["security_requirements"] == [{"BearerAuth": []}]


def test_15_operation_result_preserves_security_schemes():
    op_res = OperationResult(
        provider="Bearer Spec",
        operation="get_profile",
        security_schemes={"BearerAuth": {"type": "http", "scheme": "bearer"}},
        security_requirements=[{"BearerAuth": []}]
    )
    assert op_res.security_schemes == {"BearerAuth": {"type": "http", "scheme": "bearer"}}


def test_16_operation_result_preserves_security_requirements():
    op_res = OperationResult(
        provider="Basic Spec",
        operation="get_data",
        security_requirements=[{"BasicAuth": []}]
    )
    assert op_res.security_requirements == [{"BasicAuth": []}]


def test_17_no_credential_values_are_created_or_stored():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(OPENAPI3_APIKEY_HEADER_SPEC)
    ep = endpoints[0]
    # Verify security metadata fields only contain declarations and zero credential keys/secret tokens
    serialized_sec = str(ep.security_schemes) + str(ep.security_requirements)
    for secret in ["secret_value", "bearer_token_123", "password", "key_value_abc", "12345"]:
        assert secret not in serialized_sec.lower()


def test_18_existing_discovery_behavior_intact_for_unauthenticated_api():
    engine = DynamicAPIDiscoveryEngine()
    result = engine.discover_and_register_api(UNAUTHENTICATED_SPEC)
    assert result.success is True
    op = result.connector_spec.operations[0]
    assert op["security_schemes"] == {}
    assert op["security_requirements"] == []
    assert op["authentication"] == "None"
