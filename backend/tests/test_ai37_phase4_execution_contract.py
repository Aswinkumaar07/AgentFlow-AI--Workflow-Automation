import pytest
import asyncio
from app.agents.api_discovery.fetcher import validate_runtime_target_url
from app.agents.planner.planner_v4 import intelligent_planner_v4
from app.agents.planner.service import planner_agent
from app.agents.workflow.service import workflow_generator_agent
from app.connectors.providers.generic_rest.adapter import GenericRESTAdapter
from app.connectors.models import ConnectorRequestModel

PETSTORE_SPEC = "https://petstore3.swagger.io/api/v3/openapi.json"


def test_url_construction():
    base_url = "https://petstore3.swagger.io/api/v3"
    endpoint = "/store/inventory"
    resolved_url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    assert resolved_url == "https://petstore3.swagger.io/api/v3/store/inventory"


def test_http_method_preservation():
    prompt = f"Get the store inventory using this API specification: {PETSTORE_SPEC}"
    res = intelligent_planner_v4.plan(prompt)
    node = res.workflow_graph["nodes"][0]
    assert node["parameters"]["http_method"] == "GET"
    assert node["parameters"]["method"] == "GET"


def test_dynamic_operation_registration_get_inventory():
    prompt = f"Get the store inventory using this API specification: {PETSTORE_SPEC}"
    res = intelligent_planner_v4.plan(prompt)
    node = res.workflow_graph["nodes"][0]
    assert node["operation"] == "getInventory"
    assert node["provider"] == "generic_rest"
    assert node["provider_name"] == "Swagger Petstore - OpenAPI 3.0"
    assert node["parameters"]["url"] == "https://petstore3.swagger.io/api/v3/store/inventory"
    assert node["parameters"]["http_method"] == "GET"


def test_delete_user_metadata():
    prompt = f"Delete a user using this API specification: {PETSTORE_SPEC}"
    res = intelligent_planner_v4.plan(prompt)
    node = res.workflow_graph["nodes"][0]
    assert node["operation"] == "deleteUser"
    assert node["parameters"]["http_method"] == "DELETE"
    assert node["parameters"]["url"] == "https://petstore3.swagger.io/api/v3/user/{username}"


def test_delete_pet_metadata():
    prompt = f"Delete a pet using this API specification: {PETSTORE_SPEC}"
    res = intelligent_planner_v4.plan(prompt)
    node = res.workflow_graph["nodes"][0]
    assert node["operation"] == "deletePet"
    assert node["parameters"]["http_method"] == "DELETE"
    assert node["parameters"]["url"] == "https://petstore3.swagger.io/api/v3/pet/{petId}"


def test_ssrf_runtime_protection():
    forbidden_urls = [
        "http://127.0.0.1/admin",
        "http://localhost/metrics",
        "http://169.254.169.254/latest/meta-data",
        "http://10.0.0.1/internal",
        "http://172.16.0.1/private",
        "http://192.168.1.1/router",
        "file:///etc/passwd",
    ]
    for url in forbidden_urls:
        assert validate_runtime_target_url(url) is False

    # Test GenericRESTAdapter execution rejection for SSRF target
    adapter = GenericRESTAdapter()
    req = ConnectorRequestModel(
        operation_id="test_op",
        parameters={"url": "http://169.254.169.254/latest/meta-data", "is_dynamic_api": True}
    )
    res = asyncio.run(adapter.execute_operation(req))
    assert res.success is False
    assert res.status_code == 400
    assert "SSRF Blocked" in res.data.get("error", "")


def test_https_public_url_validation():
    public_url = "https://petstore3.swagger.io/api/v3/store/inventory"
    assert validate_runtime_target_url(public_url) is True
