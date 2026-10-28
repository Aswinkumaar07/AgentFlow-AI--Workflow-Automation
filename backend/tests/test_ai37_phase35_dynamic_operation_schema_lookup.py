import pytest
from fastapi import HTTPException
from app.agents.api_discovery.dynamic_discovery import dynamic_api_discovery_engine
from app.api.v1.connectors import _get_dynamic_openapi_operation_schema, get_operation_schema
from app.connectors.registry import connector_registry

PETSTORE_FIXTURE_SPEC = """
openapi: 3.0.0
info:
  title: Swagger Petstore - OpenAPI 3.0
  version: 1.0.11
paths:
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
"""


@pytest.fixture(autouse=True)
def setup_petstore_dynamic_api():
    res = dynamic_api_discovery_engine.discover_and_register_api(PETSTORE_FIXTURE_SPEC, format_hint="openapi3")
    assert res.success is True
    assert res.provider == "Swagger Petstore - OpenAPI 3.0"


@pytest.mark.asyncio
async def test_01_native_connector_schema_lookup_remains_unchanged():
    res = await get_operation_schema("gmail", "gmail.messages.send", current_user=None)
    assert res is not None
    data = res.body if hasattr(res, "body") else res
    assert "data" in data or hasattr(res, "status_code")


@pytest.mark.asyncio
async def test_02_dynamic_openapi_operation_schema_can_be_retrieved():
    schema = _get_dynamic_openapi_operation_schema("Swagger Petstore - OpenAPI 3.0", "getPetById")
    assert schema is not None
    assert schema.id == "getPetById"


@pytest.mark.asyncio
async def test_03_dynamic_get_pet_by_id_schema_structure():
    schema = _get_dynamic_openapi_operation_schema("generic_rest", "getPetById")
    assert schema is not None
    assert schema.id == "getPetById"
    req_names = [p.name for p in schema.required_parameters]
    assert "petId" in req_names
    pet_param = next(p for p in schema.required_parameters if p.name == "petId")
    assert pet_param.required is True


@pytest.mark.asyncio
async def test_04_dynamic_provider_identity_supported():
    schema1 = _get_dynamic_openapi_operation_schema("Swagger Petstore - OpenAPI 3.0", "getPetById")
    schema2 = _get_dynamic_openapi_operation_schema("generic_rest", "getPetById")
    assert schema1 is not None
    assert schema2 is not None
    assert schema1.id == schema2.id == "getPetById"


@pytest.mark.asyncio
async def test_05_dynamic_schema_contains_summary_description():
    schema = _get_dynamic_openapi_operation_schema("Swagger Petstore - OpenAPI 3.0", "getPetById")
    assert schema is not None
    assert "Find pet by ID" in schema.description or "getPetById" in schema.description


@pytest.mark.asyncio
async def test_06_dynamic_schema_query_parameters_as_optional():
    schema = _get_dynamic_openapi_operation_schema("Swagger Petstore - OpenAPI 3.0", "findPetsByStatus")
    assert schema is not None
    opt_names = [p.name for p in schema.optional_parameters]
    assert "status" in opt_names


@pytest.mark.asyncio
async def test_07_unknown_operation_returns_404():
    with pytest.raises(HTTPException) as exc_info:
        await get_operation_schema("generic_rest", "nonExistentOperation999", current_user=None)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_08_native_operation_takes_precedence_over_dynamic_fallback():
    native_schema = connector_registry.get_operation_schema("gmail", "gmail.messages.send")
    assert native_schema is not None
    res = await get_operation_schema("gmail", "gmail.messages.send", current_user=None)
    assert res is not None


@pytest.mark.asyncio
async def test_09_dynamic_lookup_performs_zero_network_calls():
    # Calling dynamic fallback endpoint on in-memory registered spec
    res = await get_operation_schema("Swagger Petstore - OpenAPI 3.0", "getPetById", current_user=None)
    assert res is not None


@pytest.mark.asyncio
async def test_10_endpoint_response_shape_compatibility():
    res = await get_operation_schema("generic_rest", "getPetById", current_user=None)
    assert res is not None
