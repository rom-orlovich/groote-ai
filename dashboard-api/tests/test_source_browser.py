from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_oauth_connected():
    with patch("api.source_browser.check_oauth_connected", new_callable=AsyncMock) as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_oauth_disconnected():
    with patch("api.source_browser.check_oauth_connected", new_callable=AsyncMock) as mock:
        mock.return_value = False
        yield mock


MOCK_GITHUB_RESPONSE = {
    "total_count": 2,
    "repositories": [
        {
            "full_name": "org/repo1",
            "description": "First repo",
            "language": "Python",
            "private": False,
            "stargazers_count": 10,
        },
        {
            "full_name": "org/repo2",
            "description": None,
            "language": "TypeScript",
            "private": True,
            "stargazers_count": 5,
        },
    ],
}

MOCK_JIRA_PROJECTS = [
    {"key": "PROJ", "name": "Project", "description": "Main project", "style": "classic"},
    {"key": "ENG", "name": "Engineering", "description": "", "style": "next-gen"},
]

MOCK_CONFLUENCE_SPACES = [
    {
        "key": "ENG",
        "name": "Engineering",
        "type": "global",
        "description": {"plain": {"value": "Eng docs"}},
    },
    {
        "key": "DOCS",
        "name": "Documentation",
        "type": "global",
        "description": {"plain": {"value": "General docs"}},
    },
]


def _mock_httpx_client(response_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = response_data
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


class TestBrowseGitHubRepos:
    async def test_returns_normalized_resources(self, async_client, mock_oauth_connected):
        with patch("api.source_browser.httpx.AsyncClient") as mock_client_cls:
            mock_client_cls.return_value = _mock_httpx_client(MOCK_GITHUB_RESPONSE)

            response = await async_client.get("/api/sources/browse/github/repos")
            assert response.status_code == 200
            data = response.json()
            assert "resources" in data
            assert "total_count" in data
            assert "has_more" in data
            assert len(data["resources"]) == 2
            resource = data["resources"][0]
            assert resource["id"] == "org/repo1"
            assert resource["name"] == "repo1"
            assert resource["description"] == "First repo"
            assert resource["metadata"]["full_name"] == "org/repo1"
            assert resource["metadata"]["language"] == "Python"
            assert resource["metadata"]["private"] is False
            assert resource["metadata"]["stargazers_count"] == 10

    async def test_null_description_becomes_empty_string(self, async_client, mock_oauth_connected):
        with patch("api.source_browser.httpx.AsyncClient") as mock_client_cls:
            mock_client_cls.return_value = _mock_httpx_client(MOCK_GITHUB_RESPONSE)

            response = await async_client.get("/api/sources/browse/github/repos")
            data = response.json()
            assert data["resources"][1]["description"] == ""

    async def test_returns_403_when_oauth_not_connected(
        self, async_client, mock_oauth_disconnected
    ):
        response = await async_client.get("/api/sources/browse/github/repos")
        assert response.status_code == 403


class TestBrowseJiraProjects:
    async def test_returns_project_keys_as_ids(self, async_client, mock_oauth_connected):
        with patch("api.source_browser.httpx.AsyncClient") as mock_client_cls:
            mock_client_cls.return_value = _mock_httpx_client(MOCK_JIRA_PROJECTS)

            response = await async_client.get("/api/sources/browse/jira/projects")
            assert response.status_code == 200
            data = response.json()
            assert len(data["resources"]) == 2
            resource = data["resources"][0]
            assert resource["id"] == "PROJ"
            assert resource["id"] == resource["metadata"]["key"]

    async def test_returns_403_when_oauth_not_connected(
        self, async_client, mock_oauth_disconnected
    ):
        response = await async_client.get("/api/sources/browse/jira/projects")
        assert response.status_code == 403


class TestBrowseConfluenceSpaces:
    async def test_returns_space_keys_as_ids(self, async_client, mock_oauth_connected):
        with patch("api.source_browser.httpx.AsyncClient") as mock_client_cls:
            mock_client_cls.return_value = _mock_httpx_client(MOCK_CONFLUENCE_SPACES)

            response = await async_client.get("/api/sources/browse/confluence/spaces")
            assert response.status_code == 200
            data = response.json()
            assert len(data["resources"]) == 2
            resource = data["resources"][0]
            assert resource["id"] == "ENG"
            assert resource["id"] == resource["metadata"]["key"]
            assert resource["description"] == "Eng docs"

    async def test_returns_403_when_oauth_not_connected(
        self, async_client, mock_oauth_disconnected
    ):
        response = await async_client.get("/api/sources/browse/confluence/spaces")
        assert response.status_code == 403


class TestBrowseResponseNormalization:
    @pytest.mark.parametrize(
        "endpoint,mock_data",
        [
            ("/api/sources/browse/github/repos", MOCK_GITHUB_RESPONSE),
            ("/api/sources/browse/jira/projects", MOCK_JIRA_PROJECTS),
            ("/api/sources/browse/confluence/spaces", MOCK_CONFLUENCE_SPACES),
        ],
    )
    async def test_all_endpoints_return_same_shape(
        self, async_client, mock_oauth_connected, endpoint, mock_data
    ):
        with patch("api.source_browser.httpx.AsyncClient") as mock_client_cls:
            mock_client_cls.return_value = _mock_httpx_client(mock_data)

            response = await async_client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            assert set(data.keys()) == {"resources", "total_count", "has_more"}
            for resource in data["resources"]:
                assert set(resource.keys()) == {"id", "name", "description", "metadata"}
