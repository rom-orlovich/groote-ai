from typing import Annotated

from client import GitHubClient
from config import Settings, get_settings
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict
from token_provider import TokenProvider  # noqa: TC002

router = APIRouter(prefix="/api/v1", tags=["github"])


async def get_github_client(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> GitHubClient:
    token_provider: TokenProvider = request.app.state.token_provider
    token = await token_provider.get_token()
    return GitHubClient(
        token=token,
        base_url=settings.github_api_base_url,
        timeout=settings.request_timeout,
    )


class CreateIssueRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    title: str
    body: str | None = None
    labels: list[str] | None = None


class CreateCommentRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    body: str


class CreatePRReviewCommentRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    body: str
    commit_id: str
    path: str
    line: int


class CreatePullRequestRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    title: str
    head: str
    base: str
    body: str | None = None
    draft: bool = False


class AddReactionRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    content: str


class CreateBranchRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    ref: str
    sha: str


class CreateOrUpdateFileRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    content: str
    message: str
    branch: str
    sha: str | None = None


@router.get("/repos/{owner}/{repo}")
async def get_repository(
    owner: str,
    repo: str,
    client: Annotated[GitHubClient, Depends(get_github_client)],
):
    return await client.get_repository(owner, repo)


@router.get("/repos/{owner}/{repo}/issues/{issue_number}")
async def get_issue(
    owner: str,
    repo: str,
    issue_number: int,
    client: Annotated[GitHubClient, Depends(get_github_client)],
):
    return await client.get_issue(owner, repo, issue_number)


@router.post("/repos/{owner}/{repo}/issues")
async def create_issue(
    owner: str,
    repo: str,
    request: CreateIssueRequest,
    client: Annotated[GitHubClient, Depends(get_github_client)],
):
    return await client.create_issue(owner, repo, request.title, request.body, request.labels)


@router.post("/repos/{owner}/{repo}/issues/{issue_number}/comments")
async def create_issue_comment(
    owner: str,
    repo: str,
    issue_number: int,
    request: CreateCommentRequest,
    client: Annotated[GitHubClient, Depends(get_github_client)],
):
    return await client.create_issue_comment(owner, repo, issue_number, request.body)


@router.post("/repos/{owner}/{repo}/issues/comments/{comment_id}/reactions")
async def add_reaction(
    owner: str,
    repo: str,
    comment_id: int,
    request: AddReactionRequest,
    client: Annotated[GitHubClient, Depends(get_github_client)],
):
    return await client.add_reaction(owner, repo, comment_id, request.content)


@router.get("/repos/{owner}/{repo}/pulls/{pr_number}")
async def get_pull_request(
    owner: str,
    repo: str,
    pr_number: int,
    client: Annotated[GitHubClient, Depends(get_github_client)],
):
    return await client.get_pull_request(owner, repo, pr_number)


@router.post("/repos/{owner}/{repo}/pulls/{pr_number}/comments")
async def create_pr_review_comment(
    owner: str,
    repo: str,
    pr_number: int,
    request: CreatePRReviewCommentRequest,
    client: Annotated[GitHubClient, Depends(get_github_client)],
):
    return await client.create_pr_review_comment(
        owner,
        repo,
        pr_number,
        request.body,
        request.commit_id,
        request.path,
        request.line,
    )


@router.post("/repos/{owner}/{repo}/pulls")
async def create_pull_request(
    owner: str,
    repo: str,
    request: CreatePullRequestRequest,
    client: Annotated[GitHubClient, Depends(get_github_client)],
):
    return await client.create_pull_request(
        owner, repo, request.title, request.head, request.base, request.body, request.draft
    )


@router.get("/repos/{owner}/{repo}/contents/{path:path}")
async def get_file_contents(
    owner: str,
    repo: str,
    path: str,
    ref: Annotated[str | None, Query()] = None,
    client: Annotated[GitHubClient, Depends(get_github_client)] = None,
):
    return await client.get_file_contents(owner, repo, path, ref)


@router.get("/search/code")
async def search_code(
    q: Annotated[str, Query()],
    per_page: Annotated[int, Query(ge=1, le=100)] = 30,
    page: Annotated[int, Query(ge=1)] = 1,
    client: Annotated[GitHubClient, Depends(get_github_client)] = None,
):
    return await client.search_code(q, per_page, page)


@router.get("/repos/{owner}/{repo}/branches")
async def list_branches(
    owner: str,
    repo: str,
    per_page: Annotated[int, Query(ge=1, le=100)] = 30,
    page: Annotated[int, Query(ge=1)] = 1,
    client: Annotated[GitHubClient, Depends(get_github_client)] = None,
):
    return await client.list_branches(owner, repo, per_page, page)


@router.get("/installation/repos")
async def list_installation_repos(
    per_page: Annotated[int, Query(ge=1, le=100)] = 100,
    page: Annotated[int, Query(ge=1)] = 1,
    client: Annotated[GitHubClient, Depends(get_github_client)] = None,
):
    return await client.list_installation_repos(per_page, page)


@router.get("/users/{username}/repos")
async def list_user_repos(
    username: str,
    per_page: Annotated[int, Query(ge=1, le=100)] = 100,
    page: Annotated[int, Query(ge=1)] = 1,
    client: Annotated[GitHubClient, Depends(get_github_client)] = None,
):
    return await client.list_user_repos(username, per_page, page)


@router.get("/search/repositories")
async def search_repositories(
    q: Annotated[str, Query()],
    per_page: Annotated[int, Query(ge=1, le=100)] = 30,
    page: Annotated[int, Query(ge=1)] = 1,
    client: Annotated[GitHubClient, Depends(get_github_client)] = None,
):
    return await client.search_repositories(q, per_page, page)


@router.get("/repos/{owner}/{repo}/git/ref/heads/{branch}")
async def get_branch_sha(
    owner: str,
    repo: str,
    branch: str,
    client: Annotated[GitHubClient, Depends(get_github_client)],
):
    return await client.get_branch_sha(owner, repo, branch)


@router.post("/repos/{owner}/{repo}/git/refs")
async def create_branch(
    owner: str,
    repo: str,
    request: CreateBranchRequest,
    client: Annotated[GitHubClient, Depends(get_github_client)],
):
    return await client.create_branch(owner, repo, request.ref, request.sha)


@router.put("/repos/{owner}/{repo}/contents/{path:path}")
async def create_or_update_file(
    owner: str,
    repo: str,
    path: str,
    request: CreateOrUpdateFileRequest,
    client: Annotated[GitHubClient, Depends(get_github_client)],
):
    return await client.create_or_update_file(
        owner, repo, path, request.content, request.message, request.branch, request.sha
    )
