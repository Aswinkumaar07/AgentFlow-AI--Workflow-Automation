import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from app.connectors.models import ConnectorRequestModel, ConnectorCredentialModel
from app.connectors.providers.github.adapter import GitHubAdapter
from app.connectors.providers.drive.adapter import DriveAdapter
from app.connectors.providers.notion.adapter import NotionAdapter
from app.connectors.registry import connector_registry
from app.connectors.provider_operation_registry import provider_operation_registry
from app.connectors.schemas_registry import GITHUB_METADATA, DRIVE_METADATA, NOTION_METADATA
from app.agents.task_decomposer.decomposer import EnterpriseTaskDecomposer
from app.services.connection_readiness import check_workflow_readiness, is_internal_provider


@pytest.mark.asyncio
class TestGitHubIntegration:
    """Test suite for hardened GitHub adapter and operations."""

    async def test_github_adapter_metadata(self):
        adapter = GitHubAdapter()
        meta = adapter.get_metadata()
        assert meta.provider == "GitHub"
        assert "github.issues.search" in meta.supported_operations
        assert "github.issues.get" in meta.supported_operations
        assert "github.issues.create" in meta.supported_operations

    async def test_github_issues_search_operation(self):
        adapter = GitHubAdapter()
        req = ConnectorRequestModel(
            operation_id="github.issues.search",
            parameters={"q": "is:issue state:open repo:AgentFlow-AI/TERRAWATCH"},
        )
        res = await adapter.execute_operation(req)
        assert res.success is True
        assert res.operation_id == "github.issues.search"
        assert res.status_code in (200, 201)
        assert res.data is not None

    async def test_github_issues_get_operation(self):
        adapter = GitHubAdapter()
        req = ConnectorRequestModel(
            operation_id="github.issues.get",
            parameters={"owner": "AgentFlow-AI", "repo": "TERRAWATCH", "issue_number": 101},
        )
        res = await adapter.execute_operation(req)
        assert res.success is True
        assert res.operation_id == "github.issues.get"
        assert res.data is not None

    async def test_github_issues_create_operation(self):
        adapter = GitHubAdapter()
        req = ConnectorRequestModel(
            operation_id="github.issues.create",
            parameters={"repo": "AgentFlow-AI/TERRAWATCH", "title": "Test Issue", "body": "Automated body"},
        )
        res = await adapter.execute_operation(req)
        assert res.success is True
        assert res.operation_id == "github.issues.create"
        assert res.data is not None

    async def test_github_error_classification_auth(self):
        adapter = GitHubAdapter()
        req = ConnectorRequestModel(
            operation_id="github.issues.create",
            parameters={"repo": "invalid/repo", "title": "Fail Issue"},
        )
        with patch("app.connectors.cache.connection_pool.connection_pool.request", side_effect=Exception("401 Bad credentials")):
            res = await adapter.execute_operation(req)
            assert res.success is True
            assert res.data.get("error_type") == "AUTHENTICATION_ERROR"

    async def test_github_token_sanitization(self):
        adapter = GitHubAdapter()
        raw_data = {"token": "ghp_secret_token_12345", "access_token": "secret_abc", "title": "Public Title"}
        clean = adapter._sanitize_data(raw_data)
        assert clean["token"] == "***REDACTED***"
        assert clean["access_token"] == "***REDACTED***"
        assert clean["title"] == "Public Title"


@pytest.mark.asyncio
class TestGoogleDriveIntegration:
    """Test suite for hardened Google Drive adapter and operations."""

    async def test_drive_adapter_metadata(self):
        adapter = DriveAdapter()
        meta = adapter.get_metadata()
        assert meta.provider == "Google Drive"
        assert "drive.files.list" in meta.supported_operations
        assert "drive.files.get" in meta.supported_operations
        assert "drive.files.create" in meta.supported_operations

    async def test_drive_files_list_operation(self):
        adapter = DriveAdapter()
        req = ConnectorRequestModel(
            operation_id="drive.files.list",
            parameters={"q": "trashed = false", "page_size": 10},
        )
        res = await adapter.execute_operation(req)
        assert res.success is True
        assert res.operation_id == "drive.files.list"
        assert res.data is not None

    async def test_drive_files_get_operation(self):
        adapter = DriveAdapter()
        req = ConnectorRequestModel(
            operation_id="drive.files.get",
            parameters={"file_id": "file_drive_001"},
        )
        res = await adapter.execute_operation(req)
        assert res.success is True
        assert res.operation_id == "drive.files.get"
        assert res.data is not None

    async def test_drive_files_create_operation(self):
        adapter = DriveAdapter()
        req = ConnectorRequestModel(
            operation_id="drive.files.create",
            parameters={"name": "Invoice_2026.pdf", "mime_type": "application/pdf"},
        )
        res = await adapter.execute_operation(req)
        assert res.success is True
        assert res.operation_id == "drive.files.create"
        assert res.data is not None

    async def test_drive_error_classification(self):
        adapter = DriveAdapter()
        req = ConnectorRequestModel(
            operation_id="drive.files.get",
            parameters={"file_id": "invalid_id"},
        )
        with patch("app.connectors.cache.connection_pool.connection_pool.request", side_effect=Exception("404 File not found")):
            res = await adapter.execute_operation(req)
            assert res.success is True
            assert res.data.get("error_type") == "RESOURCE_NOT_FOUND"

    async def test_drive_token_sanitization(self):
        adapter = DriveAdapter()
        raw_data = {"bearer": "ya29.secret_token", "name": "Document.pdf"}
        clean = adapter._sanitize_data(raw_data)
        assert clean["bearer"] == "***REDACTED***"
        assert clean["name"] == "Document.pdf"


@pytest.mark.asyncio
class TestNotionIntegration:
    """Test suite for hardened Notion adapter and operations."""

    async def test_notion_adapter_metadata(self):
        adapter = NotionAdapter()
        meta = adapter.get_metadata()
        assert meta.provider == "Notion"
        assert "notion.databases.query" in meta.supported_operations
        assert "notion.pages.get" in meta.supported_operations
        assert "notion.pages.create" in meta.supported_operations

    async def test_notion_databases_query_operation(self):
        adapter = NotionAdapter()
        req = ConnectorRequestModel(
            operation_id="notion.databases.query",
            parameters={"database_id": "db_notion_demo_101"},
        )
        res = await adapter.execute_operation(req)
        assert res.success is True
        assert res.operation_id == "notion.databases.query"
        assert res.data is not None

    async def test_notion_pages_get_operation(self):
        adapter = NotionAdapter()
        req = ConnectorRequestModel(
            operation_id="notion.pages.get",
            parameters={"page_id": "page_notion_demo_001"},
        )
        res = await adapter.execute_operation(req)
        assert res.success is True
        assert res.operation_id == "notion.pages.get"
        assert res.data is not None

    async def test_notion_pages_create_operation(self):
        adapter = NotionAdapter()
        req = ConnectorRequestModel(
            operation_id="notion.pages.create",
            parameters={"database_id": "db_notion_demo_101", "title": "New Notion Task"},
        )
        res = await adapter.execute_operation(req)
        assert res.success is True
        assert res.operation_id == "notion.pages.create"
        assert res.data is not None

    async def test_notion_error_classification(self):
        adapter = NotionAdapter()
        req = ConnectorRequestModel(
            operation_id="notion.pages.get",
            parameters={"page_id": "invalid_page"},
        )
        with patch("app.connectors.cache.connection_pool.connection_pool.request", side_effect=Exception("401 unauthorized")):
            res = await adapter.execute_operation(req)
            assert res.success is True
            assert res.data.get("error_type") == "AUTHENTICATION_ERROR"

    async def test_notion_token_sanitization(self):
        adapter = NotionAdapter()
        raw_data = {"secret": "secret_notion_123", "title": "Project Roadmap"}
        clean = adapter._sanitize_data(raw_data)
        assert clean["secret"] == "***REDACTED***"
        assert clean["title"] == "Project Roadmap"


class TestConnectorRegistries:
    """Test suite for connector registry registration and discovery."""

    def test_all_3_connectors_in_connector_registry(self):
        assert connector_registry.has("github") is True
        assert connector_registry.has("drive") is True
        assert connector_registry.has("notion") is True

    def test_provider_operation_registry_discovery(self):
        github_ops = provider_operation_registry.get_provider_operations("github")
        drive_ops = provider_operation_registry.get_provider_operations("drive")
        notion_ops = provider_operation_registry.get_provider_operations("notion")

        assert len(github_ops) >= 3
        assert len(drive_ops) >= 3
        assert len(notion_ops) >= 3

    def test_schemas_registry_operation_schemas(self):
        assert "github.issues.search" in GITHUB_METADATA.operation_schemas
        assert "github.issues.get" in GITHUB_METADATA.operation_schemas
        assert "github.issues.create" in GITHUB_METADATA.operation_schemas

        assert "drive.files.list" in DRIVE_METADATA.operation_schemas
        assert "drive.files.get" in DRIVE_METADATA.operation_schemas
        assert "drive.files.create" in DRIVE_METADATA.operation_schemas

        assert "notion.databases.query" in NOTION_METADATA.operation_schemas
        assert "notion.pages.get" in NOTION_METADATA.operation_schemas
        assert "notion.pages.create" in NOTION_METADATA.operation_schemas

    def test_dynamic_operation_matching(self):
        gh_op = connector_registry.match_operation_dynamically("github", "Search open GitHub issues")
        assert gh_op == "github.issues.search"

        drive_op = connector_registry.match_operation_dynamically("drive", "Upload file to Google Drive")
        assert drive_op == "drive.files.create"

        notion_op = connector_registry.match_operation_dynamically("notion", "Query Notion database")
        assert notion_op == "notion.databases.query"


class TestTaskDecomposerAI34:
    """Test suite for task decomposer pattern matching on AI-34 connectors."""

    def test_decompose_github_prompt(self):
        decomposer = EnterpriseTaskDecomposer()
        res = decomposer.decompose("Search open GitHub issues, summarize them, and post to #general Slack channel")
        assert len(res.tasks) == 3
        assert res.tasks[0].provider == "github"
        assert res.tasks[0].operation == "github.issues.search"
        assert res.tasks[1].provider == "ai"
        assert res.tasks[2].provider == "slack"

    def test_decompose_notion_prompt(self):
        decomposer = EnterpriseTaskDecomposer()
        res = decomposer.decompose("Query Notion database, summarize pages, and send to #dev Slack channel")
        assert len(res.tasks) == 3
        assert res.tasks[0].provider == "notion"
        assert res.tasks[0].operation == "notion.databases.query"
        assert res.tasks[1].provider == "ai"
        assert res.tasks[2].provider == "slack"

    def test_decompose_drive_prompt(self):
        decomposer = EnterpriseTaskDecomposer()
        res = decomposer.decompose("Search invoices in Gmail, download attachment, upload to Google Drive, notify Slack")
        assert len(res.tasks) == 4
        drive_task = next(t for t in res.tasks if t.provider == "drive")
        assert drive_task.operation == "drive.files.create"


class TestConnectionReadinessAI34:
    """Test suite for connection readiness checks on GitHub, Drive, Notion."""

    @pytest.mark.asyncio
    async def test_github_drive_notion_connection_readiness(self):
        res = await check_workflow_readiness(["github", "drive", "notion"])
        assert "ready" in res
        assert "missing_connections" in res
        assert "provider_results" in res

    def test_internal_providers_never_blocked(self):
        assert is_internal_provider("ai") is True
        assert is_internal_provider("condition") is True
        assert is_internal_provider("loop") is True
        assert is_internal_provider("github") is False
        assert is_internal_provider("drive") is False
        assert is_internal_provider("notion") is False
