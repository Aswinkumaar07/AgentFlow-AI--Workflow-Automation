import uuid
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.models.base import Base
from app.dependencies.database import get_db_session
from app.services.workflow_service import WorkflowService, parse_workflow_uuid
from app.core.exceptions import ForbiddenException
from app.core.config import Settings

client = TestClient(app)

test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestAsyncSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Setup isolated in-memory SQLite tables and FastAPI dependency override for tests."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db_session():
        async with TestAsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db_session] = override_get_db_session
    yield
    app.dependency_overrides.pop(get_db_session, None)


def test_parse_workflow_uuid_deterministic():
    """Verify parse_workflow_uuid produces a valid UUID and is deterministic for string IDs."""
    id1 = parse_workflow_uuid("wf_studio_1")
    id2 = parse_workflow_uuid("wf_studio_1")
    assert isinstance(id1, uuid.UUID)
    assert id1 == id2

    raw_uuid = str(uuid.uuid4())
    parsed = parse_workflow_uuid(raw_uuid)
    assert str(parsed) == raw_uuid


@pytest.mark.asyncio
async def test_same_owner_workflow_update():
    """Verify same owner can create and update workflow idempotently without duplicating rows."""
    async with TestAsyncSessionLocal() as db_session:
        service = WorkflowService(db_session)
        user_id = uuid.uuid4()
        wf_id_str = f"wf_same_owner_{uuid.uuid4().hex[:6]}"

        # Initial registration
        wf1 = await service.register_or_update_workflow(
            user_id=user_id,
            workflow_id_str=wf_id_str,
            title="Initial Title",
            version=1
        )
        assert wf1.title == "Initial Title"
        assert wf1.version == 1
        assert wf1.owner_id == user_id

        # Update by SAME owner
        wf2 = await service.register_or_update_workflow(
            user_id=user_id,
            workflow_id_str=wf_id_str,
            title="Updated Title",
            version=2
        )
        assert wf2.id == wf1.id
        assert wf2.title == "Updated Title"
        assert wf2.version == 2
        assert wf2.owner_id == user_id

        # Verify only one row exists in DB
        wf_list = await service.list_workflows(user_id=user_id)
        matching = [w for w in wf_list.items if w.id == wf1.id]
        assert len(matching) == 1


@pytest.mark.asyncio
async def test_cross_owner_protection():
    """Verify cross-owner update attempts raise ForbiddenException and leave original workflow untouched."""
    async with TestAsyncSessionLocal() as db_session:
        service = WorkflowService(db_session)
        user_a = uuid.uuid4()
        user_b = uuid.uuid4()
        wf_id_str = f"wf_cross_owner_{uuid.uuid4().hex[:6]}"

        # User A creates workflow
        wf_a = await service.register_or_update_workflow(
            user_id=user_a,
            workflow_id_str=wf_id_str,
            title="User A Workflow",
            version=1
        )
        assert wf_a.owner_id == user_a

        # User B attempts to overwrite User A's workflow
        with pytest.raises(ForbiddenException):
            await service.register_or_update_workflow(
                user_id=user_b,
                workflow_id_str=wf_id_str,
                title="User B Overwrite Attempt",
                version=2
            )

        # Verify User A's workflow remains unchanged
        wf_check = await service.get_workflow_details(user_id=user_a, workflow_id=wf_a.id)
        assert wf_check.title == "User A Workflow"
        assert wf_check.version == 1
        assert wf_check.owner_id == user_a


@pytest.mark.asyncio
async def test_owner_assignment_correctness():
    """Verify newly registered workflow receives the exact owner_id of the authenticated user."""
    async with TestAsyncSessionLocal() as db_session:
        service = WorkflowService(db_session)
        owner_id = uuid.uuid4()
        wf_id_str = f"wf_owner_test_{uuid.uuid4().hex[:6]}"

        wf = await service.register_or_update_workflow(
            user_id=owner_id,
            workflow_id_str=wf_id_str,
            title="Owner Test Workflow"
        )
        assert wf.owner_id == owner_id


def test_ai_generation_registration_path():
    """Verify AI workflow generation registers workflow entity in SQL without requiring external LLM calls."""
    mock_orchestrated_state = {
        "user_prompt": "Test AI Prompt",
        "goal": "Test Goal",
        "services": ["github"],
        "workflow_json": {
            "workflow_id": f"wf_gen_test_{uuid.uuid4().hex[:6]}",
            "nodes": [{"id": "step_1", "provider": "github", "operation": "github.get_repo"}],
            "edges": []
        },
        "validation_report": {"is_valid": True, "errors": []},
        "is_valid": True,
        "is_repaired": False,
        "execution_metadata": {},
        "logs": [],
    }

    with patch("app.agents.graph.langgraph_orchestrator.run", new=AsyncMock(return_value=mock_orchestrated_state)):
        res = client.post("/api/v1/ai/generate", json={"prompt": "Test AI Prompt"})
        assert res.status_code == 200
        data = res.json()["data"]
        wf_id = data["workflow_json"]["workflow_id"]
        assert wf_id.startswith("wf_gen_")

        # Verify entity returned in workflows list
        wf_list_res = client.get("/api/v1/workflows")
        assert wf_list_res.status_code == 200
        items = wf_list_res.json()["data"]["items"]
        matching = [w for w in items if w["id"] == str(parse_workflow_uuid(wf_id))]
        assert len(matching) == 1
        assert matching[0]["title"] == "Test Goal"


def test_database_configuration_fallback_safety():
    """Verify explicit PostgreSQL DATABASE_URL remains PostgreSQL even with postgres:5432 hostname."""
    pg_url = "postgresql://user:pass@postgres:5432/agentflow_db"
    s_pg = Settings(DATABASE_URL=pg_url)
    assert s_pg.ASYNC_DATABASE_URL == "postgresql+asyncpg://user:pass@postgres:5432/agentflow_db"

    # Verify SQLite is used when DATABASE_URL is unset
    s_local = Settings(DATABASE_URL=None)
    assert "sqlite+aiosqlite" in s_local.ASYNC_DATABASE_URL
