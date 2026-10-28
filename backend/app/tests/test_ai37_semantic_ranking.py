import pytest
from app.agents.api_discovery.dynamic_discovery import dynamic_api_discovery_engine
from app.agents.connector_ai.operation_ranker import operation_ranker
from app.agents.planner.planner_v4 import intelligent_planner_v4

FULL_PETSTORE_SPEC = """
openapi: 3.0.0
info:
  title: Swagger Petstore - OpenAPI 3.0
  version: 1.0.11
paths:
  /pet:
    post:
      summary: Add a new pet to the store
      operationId: addPet
      responses:
        '200':
          description: Successful operation
    put:
      summary: Update an existing pet
      operationId: updatePet
      responses:
        '200':
          description: Successful operation
  /pet/{petId}:
    delete:
      summary: Deletes a pet
      operationId: deletePet
      parameters:
        - name: petId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Successful operation
  /user:
    post:
      summary: Create user
      operationId: createUser
      responses:
        '200':
          description: Successful operation
  /user/createWithList:
    post:
      summary: Creates list of users with given input array
      operationId: createUsersWithListInput
      responses:
        '200':
          description: Successful operation
  /user/{username}:
    get:
      summary: Get user by user name
      operationId: getUserByName
      parameters:
        - name: username
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful operation
    put:
      summary: Update user
      operationId: updateUser
      parameters:
        - name: username
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful operation
    delete:
      summary: Delete user
      operationId: deleteUser
      parameters:
        - name: username
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful operation
  /store/inventory:
    get:
      summary: Returns pet inventories by status
      operationId: getInventory
      responses:
        '200':
          description: Successful operation
  /store/order:
    post:
      summary: Place an order for a pet
      operationId: placeOrder
      responses:
        '200':
          description: Successful operation
  /store/order/{orderId}:
    get:
      summary: Find purchase order by ID
      operationId: getOrderById
      parameters:
        - name: orderId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Successful operation
    delete:
      summary: Delete purchase order by ID
      operationId: deleteOrder
      parameters:
        - name: orderId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Successful operation
"""


@pytest.fixture(autouse=True)
def setup_full_petstore_spec():
    res = dynamic_api_discovery_engine.discover_and_register_api(FULL_PETSTORE_SPEC, format_hint="openapi3")
    assert res.success is True
    assert res.provider == "Swagger Petstore - OpenAPI 3.0"


def test_tc_sem_01_delete_user():
    prompt = "Delete a user using this API specification:\nhttps://petstore3.swagger.io/api/v3/openapi.json"
    ranked = operation_ranker.rank_operations(prompt, target_provider="Swagger Petstore - OpenAPI 3.0", top_k=5)
    assert ranked[0].operation == "deleteUser"
    plan = intelligent_planner_v4.plan(prompt)
    assert plan.selected_operations == ["deleteUser"]


def test_tc_sem_02_delete_pet():
    prompt = "Delete a pet using this API specification:\nhttps://petstore3.swagger.io/api/v3/openapi.json"
    ranked = operation_ranker.rank_operations(prompt, target_provider="Swagger Petstore - OpenAPI 3.0", top_k=5)
    assert ranked[0].operation == "deletePet"
    plan = intelligent_planner_v4.plan(prompt)
    assert plan.selected_operations == ["deletePet"]


def test_tc_sem_03_update_user():
    prompt = "Update a user using this API specification:\nhttps://petstore3.swagger.io/api/v3/openapi.json"
    ranked = operation_ranker.rank_operations(prompt, target_provider="Swagger Petstore - OpenAPI 3.0", top_k=5)
    assert ranked[0].operation == "updateUser"
    plan = intelligent_planner_v4.plan(prompt)
    assert plan.selected_operations == ["updateUser"]


def test_tc_sem_04_update_pet():
    prompt = "Update a pet using this API specification:\nhttps://petstore3.swagger.io/api/v3/openapi.json"
    ranked = operation_ranker.rank_operations(prompt, target_provider="Swagger Petstore - OpenAPI 3.0", top_k=5)
    assert ranked[0].operation == "updatePet"
    plan = intelligent_planner_v4.plan(prompt)
    assert plan.selected_operations == ["updatePet"]


def test_tc_sem_05_create_user():
    prompt = "Create a new user using this API specification:\nhttps://petstore3.swagger.io/api/v3/openapi.json"
    ranked = operation_ranker.rank_operations(prompt, target_provider="Swagger Petstore - OpenAPI 3.0", top_k=5)
    assert ranked[0].operation == "createUser"
    plan = intelligent_planner_v4.plan(prompt)
    assert plan.selected_operations == ["createUser"]


def test_tc_sem_06_get_user_named_john():
    prompt = "Get the user named John using this API specification:\nhttps://petstore3.swagger.io/api/v3/openapi.json"
    ranked = operation_ranker.rank_operations(prompt, target_provider="Swagger Petstore - OpenAPI 3.0", top_k=5)
    assert ranked[0].operation == "getUserByName"
    plan = intelligent_planner_v4.plan(prompt)
    assert plan.selected_operations == ["getUserByName"]


def test_tc_sem_07_get_inventory():
    prompt = "Get the inventory using this API specification:\nhttps://petstore3.swagger.io/api/v3/openapi.json"
    ranked = operation_ranker.rank_operations(prompt, target_provider="Swagger Petstore - OpenAPI 3.0", top_k=5)
    assert ranked[0].operation == "getInventory"
    plan = intelligent_planner_v4.plan(prompt)
    assert plan.selected_operations == ["getInventory"]


def test_tc_sem_08_create_pet():
    prompt = "Create a new pet using this API specification:\nhttps://petstore3.swagger.io/api/v3/openapi.json"
    ranked = operation_ranker.rank_operations(prompt, target_provider="Swagger Petstore - OpenAPI 3.0", top_k=5)
    assert ranked[0].operation == "addPet"
    plan = intelligent_planner_v4.plan(prompt)
    assert plan.selected_operations == ["addPet"]


def test_tc_sem_09_delete_order():
    prompt = "Delete an order using this API specification:\nhttps://petstore3.swagger.io/api/v3/openapi.json"
    ranked = operation_ranker.rank_operations(prompt, target_provider="Swagger Petstore - OpenAPI 3.0", top_k=5)
    assert ranked[0].operation == "deleteOrder"
    plan = intelligent_planner_v4.plan(prompt)
    assert plan.selected_operations == ["deleteOrder"]


def test_tc_sem_10_get_order_by_id():
    prompt = "Get an order by ID using this API specification:\nhttps://petstore3.swagger.io/api/v3/openapi.json"
    ranked = operation_ranker.rank_operations(prompt, target_provider="Swagger Petstore - OpenAPI 3.0", top_k=5)
    assert ranked[0].operation == "getOrderById"
    plan = intelligent_planner_v4.plan(prompt)
    assert plan.selected_operations == ["getOrderById"]
