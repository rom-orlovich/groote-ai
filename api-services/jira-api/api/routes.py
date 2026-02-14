from typing import Annotated, Any

from client import JiraClient
from config import Settings, get_settings
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict
from token_provider import TokenProvider  # noqa: TC002

router = APIRouter(prefix="/api/v1", tags=["jira"])


async def get_jira_client(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> JiraClient:
    token_provider: TokenProvider = request.app.state.token_provider
    result = await token_provider.get_token()
    if result.auth_mode == "bearer":
        return JiraClient(
            base_url=result.base_url,
            oauth_token=result.token,
            timeout=settings.request_timeout,
        )
    return JiraClient(
        base_url=result.base_url,
        email=token_provider.static_email,
        api_token=result.token,
        timeout=settings.request_timeout,
    )


class CreateIssueRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    project_key: str
    summary: str
    description: str
    issue_type: str = "Task"


class UpdateIssueRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    fields: dict[str, Any]


class AddCommentRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    body: str


class SearchIssuesRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    jql: str
    max_results: int = 50
    start_at: int = 0
    expand: str = ""
    next_page_token: str = ""
    fields: list[str] | None = None


class TransitionIssueRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    transition_id: str


class CreateProjectRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    key: str
    name: str
    project_type_key: str = "software"
    lead_account_id: str = ""
    description: str = ""


class CreateBoardRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    name: str
    project_key: str
    board_type: str = "kanban"


@router.get("/issues/{issue_key}")
async def get_issue(
    issue_key: str,
    client: Annotated[JiraClient, Depends(get_jira_client)],
):
    return await client.get_issue(issue_key)


@router.post("/issues")
async def create_issue(
    request: CreateIssueRequest,
    client: Annotated[JiraClient, Depends(get_jira_client)],
):
    return await client.create_issue(
        request.project_key,
        request.summary,
        request.description,
        request.issue_type,
    )


@router.put("/issues/{issue_key}")
async def update_issue(
    issue_key: str,
    request: UpdateIssueRequest,
    client: Annotated[JiraClient, Depends(get_jira_client)],
):
    return await client.update_issue(issue_key, request.fields)


@router.post("/issues/{issue_key}/comments")
async def add_comment(
    issue_key: str,
    request: AddCommentRequest,
    client: Annotated[JiraClient, Depends(get_jira_client)],
):
    return await client.add_comment(issue_key, request.body)


@router.post("/search")
async def search_issues(
    request: SearchIssuesRequest,
    client: Annotated[JiraClient, Depends(get_jira_client)],
):
    return await client.search_issues(
        request.jql,
        request.max_results,
        request.start_at,
        request.expand,
        request.next_page_token,
        request.fields,
    )


@router.get("/issues/{issue_key}/transitions")
async def get_transitions(
    issue_key: str,
    client: Annotated[JiraClient, Depends(get_jira_client)],
):
    return await client.get_transitions(issue_key)


@router.post("/issues/{issue_key}/transitions")
async def transition_issue(
    issue_key: str,
    request: TransitionIssueRequest,
    client: Annotated[JiraClient, Depends(get_jira_client)],
):
    return await client.transition_issue(issue_key, request.transition_id)


@router.get("/projects")
async def get_projects(
    client: Annotated[JiraClient, Depends(get_jira_client)],
):
    return await client.get_projects()


@router.post("/projects")
async def create_project(
    request: CreateProjectRequest,
    client: Annotated[JiraClient, Depends(get_jira_client)],
):
    return await client.create_project(
        request.key,
        request.name,
        request.project_type_key,
        request.lead_account_id,
        request.description,
    )


@router.get("/boards")
async def get_boards(
    project_key: Annotated[str, Query()] = "",
    client: Annotated[JiraClient, Depends(get_jira_client)] = None,
):
    return await client.get_boards(project_key)


@router.post("/boards")
async def create_board(
    request: CreateBoardRequest,
    client: Annotated[JiraClient, Depends(get_jira_client)],
):
    return await client.create_board(
        request.name,
        request.project_key,
        request.board_type,
    )


@router.get("/confluence/pages")
async def get_confluence_pages(
    space_key: Annotated[str, Query()],
    start: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=250)] = 50,
    expand: Annotated[str, Query()] = "body.storage,metadata.labels,version",
    client: Annotated[JiraClient, Depends(get_jira_client)] = None,
):
    return await client.get_confluence_pages(space_key, start, limit, expand)


@router.get("/confluence/spaces")
async def get_confluence_spaces(
    client: Annotated[JiraClient, Depends(get_jira_client)],
):
    return await client.get_confluence_spaces()
