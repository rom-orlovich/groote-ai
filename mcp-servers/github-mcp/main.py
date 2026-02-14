from typing import Any

from config import get_settings
from fastmcp import FastMCP
from github_mcp import GitHubAPI

mcp = FastMCP("GitHub MCP Server")
github_api = GitHubAPI()


@mcp.tool()
async def get_repository(owner: str, repo: str) -> dict[str, Any]:
    """
    Get details of a GitHub repository.

    Args:
        owner: Repository owner
        repo: Repository name

    Returns:
        Repository details including name, description, and metadata
    """
    return await github_api.get_repository(owner, repo)


@mcp.tool()
async def get_issue(owner: str, repo: str, issue_number: int) -> dict[str, Any]:
    """
    Get details of a GitHub issue.

    Args:
        owner: Repository owner
        repo: Repository name
        issue_number: Issue number

    Returns:
        Issue details including title, body, state, and labels
    """
    return await github_api.get_issue(owner, repo, issue_number)


@mcp.tool()
async def create_issue(
    owner: str,
    repo: str,
    title: str,
    body: str | None = None,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """
    Create a new GitHub issue.

    Args:
        owner: Repository owner
        repo: Repository name
        title: Issue title
        body: Issue body/description
        labels: List of label names to apply

    Returns:
        Created issue details including the new issue number
    """
    return await github_api.create_issue(owner, repo, title, body, labels)


@mcp.tool()
async def add_issue_comment(owner: str, repo: str, issue_number: int, body: str) -> dict[str, Any]:
    """
    Add a comment to a GitHub issue.

    Args:
        owner: Repository owner
        repo: Repository name
        issue_number: Issue number
        body: Comment text

    Returns:
        Created comment details
    """
    return await github_api.add_issue_comment(owner, repo, issue_number, body)


@mcp.tool()
async def add_reaction(owner: str, repo: str, comment_id: int, content: str) -> dict[str, Any]:
    """
    Add a reaction to an issue comment.

    Args:
        owner: Repository owner
        repo: Repository name
        comment_id: Comment ID to react to
        content: Reaction type (+1, -1, laugh, confused, heart, hooray, rocket, eyes)

    Returns:
        Created reaction details
    """
    return await github_api.add_reaction(owner, repo, comment_id, content)


@mcp.tool()
async def create_pull_request(
    owner: str,
    repo: str,
    title: str,
    head: str,
    base: str,
    body: str | None = None,
    draft: bool = False,
) -> dict[str, Any]:
    """
    Create a pull request in a GitHub repository.

    Args:
        owner: Repository owner
        repo: Repository name
        title: PR title
        head: Branch containing changes
        base: Branch to merge into (e.g., "main")
        body: PR description (markdown)
        draft: Create as draft PR

    Returns:
        Created pull request details including number, url, and html_url
    """
    return await github_api.create_pull_request(owner, repo, title, head, base, body, draft)


@mcp.tool()
async def get_pull_request(owner: str, repo: str, pr_number: int) -> dict[str, Any]:
    """
    Get details of a GitHub pull request.

    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: Pull request number

    Returns:
        Pull request details including title, body, state, and diff
    """
    return await github_api.get_pull_request(owner, repo, pr_number)


@mcp.tool()
async def create_pr_review_comment(
    owner: str,
    repo: str,
    pr_number: int,
    body: str,
    commit_id: str,
    path: str,
    line: int,
) -> dict[str, Any]:
    """
    Create a review comment on a pull request.

    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: Pull request number
        body: Comment text
        commit_id: SHA of the commit to comment on
        path: File path to comment on
        line: Line number in the file

    Returns:
        Created review comment details
    """
    return await github_api.create_pr_review_comment(
        owner, repo, pr_number, body, commit_id, path, line
    )


@mcp.tool()
async def get_file_contents(
    owner: str, repo: str, path: str, ref: str | None = None
) -> dict[str, Any]:
    """
    Get the contents of a file in a repository.

    Args:
        owner: Repository owner
        repo: Repository name
        path: Path to the file
        ref: Git reference (branch, tag, or SHA)

    Returns:
        File contents and metadata
    """
    return await github_api.get_file_contents(owner, repo, path, ref)


@mcp.tool()
async def search_code(query: str, per_page: int = 30, page: int = 1) -> dict[str, Any]:
    """
    Search for code across GitHub repositories.

    Args:
        query: Search query string
        per_page: Number of results per page (max 100)
        page: Page number for pagination

    Returns:
        Search results with matching code snippets
    """
    return await github_api.search_code(query, per_page, page)


@mcp.tool()
async def list_branches(
    owner: str, repo: str, per_page: int = 30, page: int = 1
) -> list[dict[str, Any]]:
    """
    List branches of a repository.

    Args:
        owner: Repository owner
        repo: Repository name
        per_page: Number of results per page (max 100)
        page: Page number for pagination

    Returns:
        List of branches with names and commit SHAs
    """
    return await github_api.list_branches(owner, repo, per_page, page)


@mcp.tool()
async def list_repos(per_page: int = 100, page: int = 1) -> dict[str, Any]:
    """List repositories accessible to the installation.

    Args:
        per_page: Number of results per page (max 100)
        page: Page number for pagination
    """
    return await github_api.list_repos(per_page, page)


@mcp.tool()
async def get_branch_sha(owner: str, repo: str, branch: str) -> dict[str, Any]:
    """Get the SHA of a branch head.

    Args:
        owner: Repository owner
        repo: Repository name
        branch: Branch name
    """
    return await github_api.get_branch_sha(owner, repo, branch)


@mcp.tool()
async def create_branch(owner: str, repo: str, ref: str, sha: str) -> dict[str, Any]:
    """Create a new branch from a SHA.

    Args:
        owner: Repository owner
        repo: Repository name
        ref: New branch name
        sha: SHA to create branch from
    """
    return await github_api.create_branch(owner, repo, ref, sha)


@mcp.tool()
async def create_or_update_file(
    owner: str,
    repo: str,
    path: str,
    content: str,
    message: str,
    branch: str,
    sha: str | None = None,
) -> dict[str, Any]:
    """Create or update a file in a repository via the Contents API.

    Args:
        owner: Repository owner
        repo: Repository name
        path: File path in the repository
        content: File content (will be base64 encoded by the API service)
        message: Commit message
        branch: Branch to commit to
        sha: SHA of the file being replaced (required for updates, omit for creates)
    """
    return await github_api.create_or_update_file(owner, repo, path, content, message, branch, sha)


if __name__ == "__main__":
    settings = get_settings()
    mcp.run(transport="sse", host="0.0.0.0", port=settings.port)
