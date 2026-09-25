import os
import json
import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.services.workflow_service import WorkflowService, parse_workflow_uuid
from app.services.workflow_backfill import WorkflowBackfillService, DEFAULT_USER_ID

test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestAsyncSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield

@pytest.mark.asyncio
async def test_backfill_single_workflow_and_latest_version_selection(tmp_path):
    """Verify single legacy workflow with multiple snapshots is imported into ONE SQL row using the latest version."""
    storage_dir = tmp_path / "versions"
    storage_dir.mkdir()

    wf_id = "wf_legacy_test_1"
    snapshots = [
        {
            "version_id": "v1_id",
            "workflow_id": wf_id,
            "version_number": 1,
            "name": "Version 1 Name",
            "author": "admin@agentflow.ai",
            "workflow_spec": {"nodes": [{"id": "n1"}]}
        },
        {
            "version_id": "v2_id",
            "workflow_id": wf_id,
            "version_number": 2,
            "name": "Latest Version 2 Name",
            "author": "admin@agentflow.ai",
            "workflow_spec": {"nodes": [{"id": "n1"}, {"id": "n2"}]}
        }
    ]

    file_path = storage_dir / f"{wf_id}.json"
    file_path.write_text(json.dumps(snapshots), encoding="utf-8")

    async with TestAsyncSessionLocal() as db:
        backfill = WorkflowBackfillService(db, storage_dir=str(storage_dir))
        res = await backfill.run_backfill()
        await db.commit()

        assert res["discovered_unique_workflows"] == 1
        assert res["registered_count"] == 1
        assert res["already_existing_count"] == 0
        assert res["final_sql_count"] == 1

        # Verify SQL row properties
        wf_service = WorkflowService(db)
        wf_uuid = parse_workflow_uuid(wf_id)
        entity = await wf_service.get_workflow_details(DEFAULT_USER_ID, wf_uuid)
        assert entity.title == "Latest Version 2 Name"
        assert entity.version == 2
        assert entity.owner_id == DEFAULT_USER_ID

@pytest.mark.asyncio
async def test_backfill_idempotency_running_twice(tmp_path):
    """Verify running backfill twice leaves exactly ONE SQL row without duplicates."""
    storage_dir = tmp_path / "versions"
    storage_dir.mkdir()

    wf_id = "wf_idempotent_test"
    snapshots = [
        {
            "version_id": "v1",
            "workflow_id": wf_id,
            "version_number": 1,
            "name": "Idempotent Title",
            "author": "admin@agentflow.ai"
        }
    ]
    (storage_dir / f"{wf_id}.json").write_text(json.dumps(snapshots), encoding="utf-8")

    async with TestAsyncSessionLocal() as db:
        backfill = WorkflowBackfillService(db, storage_dir=str(storage_dir))
        res1 = await backfill.run_backfill()
        await db.commit()
        assert res1["registered_count"] == 1
        assert res1["already_existing_count"] == 0

        res2 = await backfill.run_backfill()
        await db.commit()
        assert res2["registered_count"] == 0
        assert res2["already_existing_count"] == 1
        assert res2["final_sql_count"] == 1

@pytest.mark.asyncio
async def test_backfill_cross_owner_not_overwritten(tmp_path):
    """Verify existing workflow owned by another user is NOT overwritten by backfill."""
    storage_dir = tmp_path / "versions"
    storage_dir.mkdir()

    wf_id = "wf_cross_owner_backfill"
    other_user_id = uuid.uuid4()

    # Pre-register workflow under other_user_id in SQL
    async with TestAsyncSessionLocal() as db:
        wf_service = WorkflowService(db)
        await wf_service.register_or_update_workflow(
            user_id=other_user_id,
            workflow_id_str=wf_id,
            title="Original Other User Workflow",
            version=10
        )
        await db.commit()

    # Legacy snapshot file claims admin@agentflow.ai
    snapshots = [
        {
            "version_id": "v1",
            "workflow_id": wf_id,
            "version_number": 1,
            "name": "Attempted Backfill Overwrite",
            "author": "admin@agentflow.ai"
        }
    ]
    (storage_dir / f"{wf_id}.json").write_text(json.dumps(snapshots), encoding="utf-8")

    async with TestAsyncSessionLocal() as db:
        backfill = WorkflowBackfillService(db, storage_dir=str(storage_dir))
        res = await backfill.run_backfill()
        await db.commit()
        assert res["skipped_owner_mismatch_count"] == 1

        # Verify original workflow remains owned by other_user_id
        wf_service = WorkflowService(db)
        wf_uuid = parse_workflow_uuid(wf_id)
        original = await wf_service.get_workflow_details(other_user_id, wf_uuid)
        assert original.title == "Original Other User Workflow"
        assert original.owner_id == other_user_id

@pytest.mark.asyncio
async def test_backfill_skips_unmapped_author(tmp_path):
    """Verify legacy snapshot with unknown unmapped author is safely skipped and reported."""
    storage_dir = tmp_path / "versions"
    storage_dir.mkdir()

    wf_id = "wf_unmapped_author"
    snapshots = [
        {
            "version_id": "v1",
            "workflow_id": wf_id,
            "version_number": 1,
            "name": "Unmapped Author Title",
            "author": "unknown_stranger_123"
        }
    ]
    (storage_dir / f"{wf_id}.json").write_text(json.dumps(snapshots), encoding="utf-8")

    async with TestAsyncSessionLocal() as db:
        backfill = WorkflowBackfillService(db, storage_dir=str(storage_dir))
        res = await backfill.run_backfill()
        await db.commit()
        assert res["skipped_unmapped_count"] == 1
        assert "unknown_stranger_123" in res["unmapped_authors"]
        assert res["final_sql_count"] == 0

@pytest.mark.asyncio
async def test_backfill_handles_malformed_json_gracefully(tmp_path):
    """Verify malformed JSON files do not crash the migration and other valid files are processed."""
    storage_dir = tmp_path / "versions"
    storage_dir.mkdir()

    # 1. Malformed file
    (storage_dir / "wf_corrupt.json").write_text("{invalid_json: true", encoding="utf-8")

    # 2. Valid file
    wf_valid_id = "wf_valid_after_corrupt"
    snapshots = [
        {
            "version_id": "v1",
            "workflow_id": wf_valid_id,
            "version_number": 1,
            "name": "Valid Workflow",
            "author": "admin@agentflow.ai"
        }
    ]
    (storage_dir / f"{wf_valid_id}.json").write_text(json.dumps(snapshots), encoding="utf-8")

    async with TestAsyncSessionLocal() as db:
        backfill = WorkflowBackfillService(db, storage_dir=str(storage_dir))
        res = await backfill.run_backfill()
        await db.commit()

        assert res["malformed_count"] == 1
        assert "wf_corrupt.json" in res["malformed_files"]
        assert res["registered_count"] == 1
        assert res["final_sql_count"] == 1
