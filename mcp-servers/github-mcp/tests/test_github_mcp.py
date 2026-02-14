import pytest
import respx
from httpx import Response

pytestmark = pytest.mark.asyncio


class TestGitHubAPIClient:
    async def test_get_issue_returns_issue_data(self, github_api):
        with respx.mock(base_url="http://github-api:3001") as mock:
            mock.get("/api/v1/repos/owner/repo/issues/1").mock(
                return_value=Response(200, json={"number": 1, "title": "Bug", "state": "open"})
            )
            result = await github_api.get_issue("owner", "repo", 1)
            assert result["number"] == 1
            assert result["title"] == "Bug"
            assert result["state"] == "open"

    async def test_add_issue_comment_sends_body(self, github_api):
        import json

        with respx.mock(base_url="http://github-api:3001") as mock:
            route = mock.post("/api/v1/repos/owner/repo/issues/1/comments").mock(
                return_value=Response(201, json={"id": 10, "body": "test comment"})
            )
            result = await github_api.add_issue_comment("owner", "repo", 1, "test comment")
            assert result["body"] == "test comment"
            sent = json.loads(route.calls[0].request.content)
            assert sent == {"body": "test comment"}

    async def test_get_file_contents_with_ref(self, github_api):
        with respx.mock(base_url="http://github-api:3001") as mock:
            route = mock.get("/api/v1/repos/owner/repo/contents/README.md").mock(
                return_value=Response(200, json={"name": "README.md", "content": "data"})
            )
            await github_api.get_file_contents("owner", "repo", "README.md", ref="main")
            assert route.calls[0].request.url.params["ref"] == "main"

    async def test_get_file_contents_without_ref(self, github_api):
        with respx.mock(base_url="http://github-api:3001") as mock:
            route = mock.get("/api/v1/repos/owner/repo/contents/README.md").mock(
                return_value=Response(200, json={"name": "README.md", "content": "data"})
            )
            await github_api.get_file_contents("owner", "repo", "README.md")
            assert "ref" not in route.calls[0].request.url.params

    async def test_search_code_passes_query_params(self, github_api):
        with respx.mock(base_url="http://github-api:3001") as mock:
            route = mock.get("/api/v1/search/code").mock(
                return_value=Response(200, json={"total_count": 1, "items": []})
            )
            await github_api.search_code("test", per_page=30)
            params = route.calls[0].request.url.params
            assert params["q"] == "test"
            assert params["per_page"] == "30"

    async def test_get_pull_request_returns_pr_data(self, github_api):
        with respx.mock(base_url="http://github-api:3001") as mock:
            mock.get("/api/v1/repos/owner/repo/pulls/1").mock(
                return_value=Response(200, json={"number": 1, "title": "Fix bug"})
            )
            result = await github_api.get_pull_request("owner", "repo", 1)
            assert result["number"] == 1
            assert result["title"] == "Fix bug"

    async def test_get_repository_returns_data(self, github_api):
        with respx.mock(base_url="http://github-api:3001") as mock:
            mock.get("/api/v1/repos/owner/repo").mock(
                return_value=Response(200, json={"full_name": "owner/repo"})
            )
            result = await github_api.get_repository("owner", "repo")
            assert result["full_name"] == "owner/repo"

    async def test_create_issue_sends_payload(self, github_api):
        import json

        with respx.mock(base_url="http://github-api:3001") as mock:
            route = mock.post("/api/v1/repos/owner/repo/issues").mock(
                return_value=Response(201, json={"number": 5, "title": "New issue"})
            )
            result = await github_api.create_issue("owner", "repo", "New issue", "Description")
            assert result["number"] == 5
            sent = json.loads(route.calls[0].request.content)
            assert sent["title"] == "New issue"
            assert sent["body"] == "Description"

    async def test_list_branches_returns_list(self, github_api):
        with respx.mock(base_url="http://github-api:3001") as mock:
            mock.get("/api/v1/repos/owner/repo/branches").mock(
                return_value=Response(200, json=[{"name": "main"}, {"name": "dev"}])
            )
            result = await github_api.list_branches("owner", "repo")
            assert len(result) == 2
            assert result[0]["name"] == "main"

    async def test_http_404_propagates(self, github_api):
        import httpx

        with respx.mock(base_url="http://github-api:3001") as mock:
            mock.get("/api/v1/repos/owner/repo/issues/999").mock(
                return_value=Response(404, json={"message": "Not Found"})
            )
            with pytest.raises(httpx.HTTPStatusError):
                await github_api.get_issue("owner", "repo", 999)

    async def test_add_reaction_sends_content(self, github_api):
        import json

        with respx.mock(base_url="http://github-api:3001") as mock:
            route = mock.post("/api/v1/repos/owner/repo/issues/comments/1/reactions").mock(
                return_value=Response(201, json={"id": 1, "content": "+1"})
            )
            result = await github_api.add_reaction("owner", "repo", 1, "+1")
            assert result["content"] == "+1"
            sent = json.loads(route.calls[0].request.content)
            assert sent == {"content": "+1"}


class TestMCPToolLayer:
    @pytest.fixture
    def mock_github_api(self, monkeypatch):
        import main

        class MockGitHubAPI:
            def __init__(self):
                self.last_call: dict = {}

            async def add_issue_comment(self, owner, repo, issue_number, body):
                self.last_call = {
                    "method": "add_issue_comment",
                    "args": (owner, repo, issue_number, body),
                }
                return {"id": 1, "body": body}

            async def create_issue(self, owner, repo, title, body=None, labels=None):
                self.last_call = {
                    "method": "create_issue",
                    "args": (owner, repo, title, body, labels),
                }
                return {"number": 1, "title": title}

            async def search_code(self, query, per_page=30, page=1):
                self.last_call = {
                    "method": "search_code",
                    "args": (query, per_page, page),
                }
                return {"total_count": 0, "items": []}

        mock = MockGitHubAPI()
        monkeypatch.setattr(main, "github_api", mock)
        return mock

    async def test_add_issue_comment_calls_client(self, mock_github_api):
        from main import add_issue_comment

        await add_issue_comment.fn("owner", "repo", 42, "Hello")
        assert mock_github_api.last_call["method"] == "add_issue_comment"
        assert mock_github_api.last_call["args"] == ("owner", "repo", 42, "Hello")

    async def test_create_issue_with_labels(self, mock_github_api):
        from main import create_issue

        await create_issue.fn("owner", "repo", "Bug", "desc", ["bug", "urgent"])
        assert mock_github_api.last_call["args"] == (
            "owner",
            "repo",
            "Bug",
            "desc",
            ["bug", "urgent"],
        )

    async def test_create_issue_without_labels(self, mock_github_api):
        from main import create_issue

        await create_issue.fn("owner", "repo", "Feature", None, None)
        assert mock_github_api.last_call["args"] == ("owner", "repo", "Feature", None, None)

    async def test_search_code_default_per_page(self, mock_github_api):
        from main import search_code

        await search_code.fn("test query")
        assert mock_github_api.last_call["args"] == ("test query", 30, 1)
