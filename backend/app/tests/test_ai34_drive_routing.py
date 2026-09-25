import pytest
from app.agents.task_decomposer.decomposer import EnterpriseTaskDecomposer


@pytest.fixture
def decomposer():
    return EnterpriseTaskDecomposer()


def test_drive_routing_find_project_files(decomposer):
    """Test 1: 'Find project files in my Google Drive.' -> provider drive, op drive.files.list."""
    res = decomposer.decompose("Find project files in my Google Drive.")
    assert len(res.tasks) == 1
    assert res.tasks[0].provider == "drive"
    assert res.tasks[0].operation == "drive.files.list"


def test_drive_routing_search_my_google_drive(decomposer):
    """Test 2: 'Search my Google Drive.' -> drive.files.list."""
    res = decomposer.decompose("Search my Google Drive.")
    assert len(res.tasks) == 1
    assert res.tasks[0].provider == "drive"
    assert res.tasks[0].operation == "drive.files.list"


def test_drive_routing_list_files_in_drive(decomposer):
    """Test 3: 'List files in Drive.' -> drive.files.list."""
    res = decomposer.decompose("List files in Drive.")
    assert len(res.tasks) == 1
    assert res.tasks[0].provider == "drive"
    assert res.tasks[0].operation == "drive.files.list"


def test_drive_routing_find_project_files_in_drive(decomposer):
    """Test 4: 'Find project files in Drive.' -> drive.files.list."""
    res = decomposer.decompose("Find project files in Drive.")
    assert len(res.tasks) == 1
    assert res.tasks[0].provider == "drive"
    assert res.tasks[0].operation == "drive.files.list"


def test_github_routing_unaffected(decomposer):
    """Test 5: 'Find my open GitHub issues.' -> github.issues.search."""
    res = decomposer.decompose("Find my open GitHub issues.")
    assert len(res.tasks) >= 1
    assert res.tasks[0].provider == "github"
    assert res.tasks[0].operation == "github.issues.search"


def test_notion_routing_unaffected(decomposer):
    """Test 6: 'Search my Notion project documentation.' -> notion.databases.query."""
    res = decomposer.decompose("Search my Notion project documentation.")
    assert len(res.tasks) >= 1
    assert res.tasks[0].provider == "notion"
    assert res.tasks[0].operation == "notion.databases.query"


def test_gmail_routing_unaffected(decomposer):
    """Test 7: 'Find my latest email.' -> Gmail operation."""
    res = decomposer.decompose("Find my latest email.")
    assert len(res.tasks) >= 1
    assert res.tasks[0].provider == "gmail"


def test_pattern_6_does_not_intercept_drive(decomposer):
    """Test 8: Generic pattern 6 does not intercept explicit Drive prompts."""
    res = decomposer.decompose("Query Google Drive for project documents.")
    assert len(res.tasks) == 1
    assert res.tasks[0].provider == "drive"
    assert res.tasks[0].operation == "drive.files.list"


def test_multi_service_drive_ai_slack(decomposer):
    """Test 9 & 10: Multi-service prompt 'Find project files in my Google Drive, summarize them using AI, and send the summary to #all-agentflow-ai on Slack.'."""
    prompt = "Find project files in my Google Drive, summarize them using AI, and send the summary to #all-agentflow-ai on Slack."
    res = decomposer.decompose(prompt)
    assert len(res.tasks) == 3
    assert res.tasks[0].provider == "drive"
    assert res.tasks[0].operation == "drive.files.list"
    assert res.tasks[1].provider == "ai"
    assert res.tasks[1].operation == "ai.summarize"
    assert res.tasks[2].provider == "slack"
    assert res.tasks[2].operation == "slack.chat.postMessage"
    assert res.tasks[2].parameters.get("channel") == "#all-agentflow-ai"
