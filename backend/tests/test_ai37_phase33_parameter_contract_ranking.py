import pytest
from app.agents.api_discovery.dynamic_discovery import dynamic_api_discovery_engine
from app.agents.connector_ai.operation_ranker import operation_ranker, _compute_parameter_compatibility
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
  /pet/findByStatus:
    get:
      summary: Finds Pets by status
      operationId: findPetsByStatus
      parameters:
        - name: status
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful operation
  /pet/findByTags:
    get:
      summary: Finds Pets by tags
      operationId: findPetsByTags
      parameters:
        - name: tags
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful operation
  /pet/{petId}:
    get:
      summary: Find pet by ID
      operationId: getPetById
      parameters:
        - name: petId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Successful operation
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
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Order'
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
components:
  schemas:
    Order:
      type: object
      properties:
        id:
          type: integer
        petId:
          type: integer
        quantity:
          type: integer
        status:
          type: string
        complete:
          type: boolean
"""


@pytest.fixture(autouse=True)
def setup_petstore_spec():
    res = dynamic_api_discovery_engine.discover_and_register_api(FULL_PETSTORE_SPEC, format_hint="openapi3")
    assert res.success is True
    assert res.provider == "Swagger Petstore - OpenAPI 3.0"


def test_01_get_order_by_id_to_get_pet_by_id_exact_match():
    upstream_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "petId": {"type": "integer"},
            "quantity": {"type": "integer"},
            "status": {"type": "string"},
        }
    }
    item_get_pet = {
        "operation": "getPetById",
        "parameters": {"url": "https://petstore3.swagger.io/api/v3/pet/{petId}"},
    }
    compat = _compute_parameter_compatibility(item_get_pet, upstream_schema)
    assert compat == 1.0


def test_02_get_order_by_id_to_find_pets_by_status_rejected():
    upstream_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "petId": {"type": "integer"},
            "quantity": {"type": "integer"},
            "status": {"type": "string"},
        }
    }
    item_find_status = {
        "operation": "findPetsByStatus",
        "parameters": {"url": "https://petstore3.swagger.io/api/v3/pet/findByStatus"},
        "query_params": ["status"],
    }
    compat = _compute_parameter_compatibility(item_find_status, upstream_schema)
    assert compat == 0.0


def test_03_get_order_by_id_to_find_pets_by_tags_rejected():
    upstream_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "petId": {"type": "integer"},
            "quantity": {"type": "integer"},
        }
    }
    item_find_tags = {
        "operation": "findPetsByTags",
        "parameters": {"url": "https://petstore3.swagger.io/api/v3/pet/findByTag"},
        "query_params": ["tags"],
    }
    compat = _compute_parameter_compatibility(item_find_tags, upstream_schema)
    assert compat == 0.0


def test_04_exact_parameter_name_and_compatible_type_preferred():
    upstream_schema = {
        "type": "object",
        "properties": {
            "petId": {"type": "integer"}
        }
    }
    ranked = operation_ranker.rank_operations(
        "get pet details",
        target_provider="Swagger Petstore - OpenAPI 3.0",
        top_k=5,
        upstream_response_schema=upstream_schema
    )
    assert ranked[0].operation == "getPetById"


def test_05_wrong_type_rejected():
    upstream_schema = {
        "type": "object",
        "properties": {
            "petId": {"type": "array"}
        }
    }
    item_get_pet = {
        "operation": "getPetById",
        "parameters": {"url": "https://petstore3.swagger.io/api/v3/pet/{petId}"},
    }
    compat = _compute_parameter_compatibility(item_get_pet, upstream_schema)
    assert compat == 0.0


def test_06_missing_upstream_field_rejected():
    upstream_schema = {
        "type": "object",
        "properties": {
            "orderId": {"type": "integer"}
        }
    }
    item_get_pet = {
        "operation": "getPetById",
        "parameters": {"url": "https://petstore3.swagger.io/api/v3/pet/{petId}"},
    }
    compat = _compute_parameter_compatibility(item_get_pet, upstream_schema)
    assert compat == 0.0


def test_07_single_step_ranking_unchanged():
    ranked = operation_ranker.rank_operations(
        "get pet details",
        target_provider="Swagger Petstore - OpenAPI 3.0",
        top_k=5,
        upstream_response_schema=None
    )
    assert ranked[0].operation in ["findPetsByStatus", "getPetById"]


def test_08_get_pet_by_id_still_selects_get_pet_by_id():
    ranked = operation_ranker.rank_operations(
        "get pet by id",
        target_provider="Swagger Petstore - OpenAPI 3.0",
        top_k=5
    )
    assert ranked[0].operation == "getPetById"


def test_09_find_pets_by_status_still_selects_find_pets_by_status():
    ranked = operation_ranker.rank_operations(
        "find pets by status",
        target_provider="Swagger Petstore - OpenAPI 3.0",
        top_k=5
    )
    assert ranked[0].operation == "findPetsByStatus"


def test_10_update_pet_still_selects_update_pet():
    ranked = operation_ranker.rank_operations(
        "update a pet",
        target_provider="Swagger Petstore - OpenAPI 3.0",
        top_k=5
    )
    assert ranked[0].operation == "updatePet"


def test_11_no_compatible_candidate_existing_ranking_preserved():
    upstream_schema = {
        "type": "object",
        "properties": {
            "unrelatedField": {"type": "string"}
        }
    }
    ranked = operation_ranker.rank_operations(
        "find pets by status",
        target_provider="Swagger Petstore - OpenAPI 3.0",
        top_k=5,
        upstream_response_schema=upstream_schema
    )
    assert ranked[0].operation == "findPetsByStatus"


def test_12_existing_phase28_raw_score_tiebreak_remains_unchanged():
    ranked = operation_ranker.rank_operations(
        "get pet by id",
        target_provider="Swagger Petstore - OpenAPI 3.0",
        top_k=5
    )
    assert ranked[0].operation == "getPetById"


def test_13_e2e_planner_order_to_pet_chain_selects_get_pet_by_id():
    prompt = "Get store order by ID and then get pet details using this API specification: https://petstore3.swagger.io/api/v3/openapi.json"
    plan = intelligent_planner_v4.plan(prompt)
    assert len(plan.workflow_graph["nodes"]) == 2
    node1 = plan.workflow_graph["nodes"][0]
    node2 = plan.workflow_graph["nodes"][1]
    assert node1["operation"] == "getOrderById"
    assert node2["operation"] == "getPetById"
    assert node2["parameters"].get("petId") == "{{step_1.data.petId}}"
