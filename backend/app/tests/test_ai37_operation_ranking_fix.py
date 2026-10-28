import pytest
from app.agents.api_discovery.dynamic_discovery import dynamic_api_discovery_engine
from app.agents.connector_ai.operation_ranker import operation_ranker
from app.agents.planner.planner_v4 import intelligent_planner_v4

PETSTORE_SPEC = """
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
  /user:
    post:
      summary: Create user
      operationId: createUser
      responses:
        '200':
          description: Successful operation
  /user/{username}:
    get:
      summary: Get user by user name
      operationId: getUserByName
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
"""


@pytest.fixture(autouse=True)
def setup_petstore_spec():
    res = dynamic_api_discovery_engine.discover_and_register_api(PETSTORE_SPEC, format_hint="openapi3")
    assert res.success is True
    assert res.provider == "Swagger Petstore - OpenAPI 3.0"


def test_tc_rank_01_stop_words_do_not_select_add_pet():
    """TC-RANK-01: 'Get the available users...' must NOT select addPet because of stop-word matches."""
    prompt = "Get the available users from this OpenAPI specification: https://petstore3.swagger.io/api/v3/openapi.json"
    ranked = operation_ranker.rank_operations(prompt, target_provider="Swagger Petstore - OpenAPI 3.0", top_k=5)
    assert len(ranked) > 0
    top_op = ranked[0].operation
    assert top_op != "addPet", f"addPet was incorrectly selected as top operation: {top_op}"
    user_ops = [r.operation for r in ranked if "user" in r.operation.lower()]
    assert len(user_ops) > 0, "No user operation returned in ranked list"
    assert ranked[0].operation in ["getUserByName", "createUser", "createUsersWithListInput"]


def test_tc_rank_02_user_prompt_ranks_user_op_above_pet_op():
    """TC-RANK-02: A prompt referring to user operations ranks user ops above pet ops."""
    prompt = "Get user by user name"
    ranked = operation_ranker.rank_operations(prompt, target_provider="Swagger Petstore - OpenAPI 3.0", top_k=5)
    assert ranked[0].operation == "getUserByName"
    pet_ops = [r for r in ranked if r.operation == "addPet"]
    if pet_ops:
        assert ranked[0].confidence > pet_ops[0].confidence


def test_tc_rank_03_pet_prompt_ranks_add_pet_top():
    """TC-RANK-03: A prompt referring to pet operations ranks addPet appropriately."""
    prompt = "Add a new pet to the store"
    ranked = operation_ranker.rank_operations(prompt, target_provider="Swagger Petstore - OpenAPI 3.0", top_k=5)
    assert ranked[0].operation == "addPet"
    assert ranked[0].confidence >= 0.80


def test_tc_rank_04_store_inventory_prompt_ranks_inventory_op():
    """TC-RANK-04: A prompt referring to store/order operations ranks the appropriate operation."""
    prompt = "Get store inventory"
    ranked = operation_ranker.rank_operations(prompt, target_provider="Swagger Petstore - OpenAPI 3.0", top_k=5)
    assert ranked[0].operation == "getInventory"


def test_tc_rank_05_native_connector_ranking_behavior_unchanged():
    """TC-RANK-05: Native connector operation-ranking behavior remains unchanged."""
    ranked_gmail = operation_ranker.rank_operations("Send email to recipient", target_provider="Gmail")
    assert ranked_gmail[0].operation == "gmail.messages.send"

    ranked_slack = operation_ranker.rank_operations("Post message to slack channel", target_provider="Slack")
    assert ranked_slack[0].operation == "slack.chat.postMessage"

    ranked_sheets = operation_ranker.rank_operations("Read rows from spreadsheet", target_provider="Google Sheets")
    assert ranked_sheets[0].operation == "sheets.spreadsheets.values.get"


def test_tc_rank_06_e2e_planner_v4_selects_user_operation():
    """TC-RANK-06: Planner V4 end-to-end generates a user operation node instead of addPet for user prompts."""
    plan = intelligent_planner_v4.plan("Get the available users from this OpenAPI specification: https://petstore3.swagger.io/api/v3/openapi.json")
    assert plan.can_execute is True
    nodes = plan.workflow_graph.get("nodes", [])
    assert len(nodes) > 0
    node = nodes[0]
    op_id = node.get("operation") or node.get("operation_id")
    assert op_id != "addPet"
    assert op_id in ["getUserByName", "createUser", "createUsersWithListInput"]
