import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def github_api():
    from github_mcp import GitHubAPI

    api = GitHubAPI.__new__(GitHubAPI)
    api._base_url = "http://github-api:3001"
    api._timeout = 30
    api._client = None
    return api
