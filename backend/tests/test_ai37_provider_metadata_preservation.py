import pytest
import asyncio
from app.agents.planner.planner_v4 import intelligent_planner_v4
from app.agents.planner.service import planner_agent
from app.agents.workflow.service import workflow_generator_agent
from app.connectors.registry import connector_registry
from app.connectors.providers.generic_rest.adapter import GenericRESTAdapter

PETSTORE_SPEC = "https://petstore3.swagger.io/api/v3/openapi.json"

def test_dynamic_delete_user():
    prompt = f"Delete a user using this API specification: {PETSTORE_SPEC}"
    res = intelligent_planner_v4.plan(prompt)
    node = res.workflow_graph["nodes"][0]
    assert node["operation"] == "deleteUser"
    assert node["provider"] == "generic_rest"
    assert node["provider_name"] == "Swagger Petstore - OpenAPI 3.0"

    # Test full WorkflowGeneratorAgent DAG generation
    plan_dict = asyncio.run(planner_agent.create_execution_plan(prompt))
    dag = asyncio.run(workflow_generator_agent.generate_workflow_dag(plan_dict))
    dag_node = dag["nodes"][0]
    assert dag_node["provider"] == "generic_rest"
    assert dag_node["provider_name"] == "Swagger Petstore - OpenAPI 3.0"
    assert dag_node["operation"] == "deleteUser"
    assert dag_node["data"]["provider"] == "generic_rest"
    assert dag_node["data"]["provider_name"] == "Swagger Petstore - OpenAPI 3.0"

def test_dynamic_delete_pet():
    prompt = f"Delete a pet using this API specification: {PETSTORE_SPEC}"
    res = intelligent_planner_v4.plan(prompt)
    node = res.workflow_graph["nodes"][0]
    assert node["operation"] == "deletePet"
    assert node["provider"] == "generic_rest"
    assert node["provider_name"] == "Swagger Petstore - OpenAPI 3.0"

def test_dynamic_update_user():
    prompt = f"Update a user using this API specification: {PETSTORE_SPEC}"
    res = intelligent_planner_v4.plan(prompt)
    node = res.workflow_graph["nodes"][0]
    assert node["operation"] == "updateUser"
    assert node["provider"] == "generic_rest"
    assert node["provider_name"] == "Swagger Petstore - OpenAPI 3.0"

def test_dynamic_create_pet():
    prompt = f"Create a new pet using this API specification: {PETSTORE_SPEC}"
    res = intelligent_planner_v4.plan(prompt)
    node = res.workflow_graph["nodes"][0]
    assert node["operation"] == "addPet"
    assert node["provider"] == "generic_rest"
    assert node["provider_name"] == "Swagger Petstore - OpenAPI 3.0"

def test_native_gmail_regression():
    prompt = "Send an email to john@example.com saying Hello"
    res = intelligent_planner_v4.plan(prompt)
    node = res.workflow_graph["nodes"][0]
    assert node["provider"] == "gmail"
    assert node["operation"] == "gmail.messages.send"

def test_native_slack_regression():
    prompt = "Post a message to #general channel on Slack saying Hello"
    res = intelligent_planner_v4.plan(prompt)
    node = res.workflow_graph["nodes"][0]
    assert node["provider"] == "slack"
    assert node["operation"] == "slack.chat.postMessage"

def test_generic_rest_regression():
    prompt = "Make a GET HTTP request to https://api.example.com/data"
    res = intelligent_planner_v4.plan(prompt)
    node = res.workflow_graph["nodes"][0]
    assert node["provider"] in ["generic", "generic_rest"]

def test_runtime_routing_generic_rest():
    # Verify provider "generic_rest" maps to registered GenericRESTAdapter
    adapter = connector_registry.get("generic_rest")
    assert isinstance(adapter, GenericRESTAdapter)

    # Verify dynamic OpenAPI provider resolves via fallback to GenericRESTAdapter
    dynamic_adapter = connector_registry.get("Swagger Petstore - OpenAPI 3.0")
    assert isinstance(dynamic_adapter, GenericRESTAdapter)

