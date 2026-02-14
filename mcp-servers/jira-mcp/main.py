from typing import Any

from config import get_settings
from fastmcp import FastMCP
from jira_mcp import JiraAPI

mcp = FastMCP("Jira MCP Server")
jira_api = JiraAPI()


@mcp.tool()
async def get_jira_issue(issue_key: str) -> dict[str, Any]:
    """
    Get details of a Jira issue.

    Args:
        issue_key: The Jira issue key (e.g., PROJ-123)

    Returns:
        Issue details including summary, description, status, and assignee
    """
    return await jira_api.get_issue(issue_key)


@mcp.tool()
async def create_jira_issue(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Task",
) -> dict[str, Any]:
    """
    Create a new Jira issue with well-formatted markdown description.

    Args:
        project_key: The project key (e.g., PROJ)
        summary: Short issue title (max 80 chars). Format: "[Component] Action - Brief detail"
        description: Markdown-formatted description. Use real newlines (not literal backslash-n).
            Structure it as:
            ## Overview
            One-paragraph summary of what this task accomplishes.

            ## Acceptance Criteria
            - Criterion 1
            - Criterion 2

            ## Technical Notes
            - Key files: `path/to/file.py`
            - Dependencies: list any blocking work
            - Estimated scope: S/M/L

        issue_type: Type of issue - Task, Bug, Story, Epic, Sub-task

    Returns:
        Created issue details including the new issue key
    """
    return await jira_api.create_issue(project_key, summary, description, issue_type)


@mcp.tool()
async def update_jira_issue(issue_key: str, fields: dict[str, Any]) -> dict[str, Any]:
    """
    Update fields of an existing Jira issue.

    Args:
        issue_key: The Jira issue key (e.g., PROJ-123)
        fields: Dictionary of fields to update

    Returns:
        Success status
    """
    return await jira_api.update_issue(issue_key, fields)


@mcp.tool()
async def add_jira_comment(issue_key: str, body: str) -> dict[str, Any]:
    """
    Add a comment to a Jira issue.

    Args:
        issue_key: The Jira issue key (e.g., PROJ-123)
        body: Comment text

    Returns:
        Created comment details
    """
    return await jira_api.add_comment(issue_key, body)


@mcp.tool()
async def search_jira_issues(jql: str, max_results: int = 50, start_at: int = 0) -> dict[str, Any]:
    """
    Search for Jira issues using JQL.

    Args:
        jql: JQL query string
        max_results: Maximum number of results to return
        start_at: Index to start from for pagination

    Returns:
        Search results with matching issues
    """
    return await jira_api.search_issues(jql, max_results, start_at)


@mcp.tool()
async def get_jira_transitions(issue_key: str) -> dict[str, Any]:
    """
    Get available transitions for a Jira issue.

    Args:
        issue_key: The Jira issue key (e.g., PROJ-123)

    Returns:
        List of available transitions
    """
    return await jira_api.get_transitions(issue_key)


@mcp.tool()
async def transition_jira_issue(issue_key: str, transition_id: str) -> dict[str, Any]:
    """
    Transition a Jira issue to a new status.

    Args:
        issue_key: The Jira issue key (e.g., PROJ-123)
        transition_id: ID of the transition to perform

    Returns:
        Success status
    """
    return await jira_api.transition_issue(issue_key, transition_id)


@mcp.tool()
async def create_jira_project(
    key: str,
    name: str,
    project_type_key: str = "software",
    lead_account_id: str = "",
    description: str = "",
) -> dict[str, Any]:
    """
    Create a new Jira project.

    Args:
        key: Project key (uppercase, 2-10 chars, e.g., "GROOTE")
        name: Human-readable project name (e.g., "Groote AI")
        project_type_key: Project type - "software" (default), "business", "service_desk"
        lead_account_id: Atlassian account ID of the project lead (optional)
        description: Brief project description

    Returns:
        Created project details including project ID and key
    """
    return await jira_api.create_project(key, name, project_type_key, lead_account_id, description)


@mcp.tool()
async def get_jira_boards(project_key: str = "") -> dict[str, Any]:
    """
    List Jira boards, optionally filtered by project.

    Args:
        project_key: Filter boards by project key (optional)

    Returns:
        List of boards with their IDs, names, and types
    """
    return await jira_api.get_boards(project_key)


@mcp.tool()
async def create_jira_board(
    name: str,
    project_key: str,
    board_type: str = "kanban",
) -> dict[str, Any]:
    """
    Create a new Jira board for a project. Creates a JQL filter automatically.

    Args:
        name: Board name (e.g., "Groote AI Kanban")
        project_key: Project key the board is associated with
        board_type: Board type - "kanban" (default) or "scrum"

    Returns:
        Created board details including board ID
    """
    return await jira_api.create_board(name, project_key, board_type)


if __name__ == "__main__":
    settings = get_settings()
    mcp.run(transport="sse", host="0.0.0.0", port=settings.port)
