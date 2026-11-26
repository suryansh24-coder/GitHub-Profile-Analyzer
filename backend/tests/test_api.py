from __future__ import annotations

import httpx
import pytest

from app.services.github import GitHubClient
from tests.conftest import json_response


USER = {
    "login": "octocat",
    "name": "The Octocat",
    "bio": "Cat of many languages",
    "avatar_url": "https://avatars.githubusercontent.com/u/1?v=4",
    "html_url": "https://github.com/octocat",
    "followers": 100,
    "following": 10,
    "public_repos": 3,
    "created_at": "2011-01-26T19:01:12Z",
    "location": "San Francisco",
    "company": "@github",
    "blog": "https://github.blog",
    "email": None,
}
REPOS = [
    {
        "name": "Hello-World",
        "full_name": "octocat/Hello-World",
        "description": "Python API demo with FastAPI and docker support",
        "html_url": "https://github.com/octocat/Hello-World",
        "language": "Python",
        "stargazers_count": 1200,
        "forks_count": 100,
        "open_issues_count": 3,
        "fork": False,
        "topics": ["python", "api"],
        "created_at": "2012-01-01T00:00:00Z",
        "updated_at": "2026-11-01T00:00:00Z",
        "pushed_at": "2026-11-01T00:00:00Z",
        "size": 100,
        "license": {"spdx_id": "MIT"},
        "owner": {"login": "octocat"},
    },
    {
        "name": "Spoon-Knife",
        "full_name": "octocat/Spoon-Knife",
        "description": "fork example",
        "html_url": "https://github.com/octocat/Spoon-Knife",
        "language": "JavaScript",
        "stargazers_count": 10,
        "forks_count": 2,
        "open_issues_count": 0,
        "fork": True,
        "topics": [],
        "created_at": "2014-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "pushed_at": "2024-01-01T00:00:00Z",
        "size": 20,
        "license": None,
        "owner": {"login": "octocat"},
    },
]


@pytest.mark.asyncio
async def test_health_endpoint(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "github" in data["integrations"]
    assert "ai" in data["integrations"]
    assert data["integrations"]["github"]["tokenExposedToFrontend"] is False


@pytest.mark.asyncio
async def test_profile_endpoint_uses_real_api_shape(make_client) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/users/octocat":
            return json_response(USER)
        if path == "/users/octocat/repos":
            return json_response(REPOS)
        if path.endswith("/languages"):
            return json_response({"Python": 5000, "HTML": 1000})
        return json_response({}, 404)

    client = make_client(handler)
    response = await client.get("/api/profile/octocat")
    assert response.status_code == 200
    data = response.json()
    assert data["profile"]["login"] == "octocat"
    assert data["statistics"]["totalStars"] == 1210
    assert set(data["scores"].keys()) >= {"activity", "portfolio", "diversity", "openSource", "career", "legacy"}
    assert data["scores"]["legacy"]["breakdown"]["stars"] == 30
    assert any(skill["name"] == "Python" for skill in data["developerDna"]["skills"])
    assert data["languageDataNote"].startswith("Byte counts")


@pytest.mark.asyncio
async def test_explorer_filters_and_maps_real_data(make_client) -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["q"] = request.url.params.get("q", "")
        return json_response(
            {
                "total_count": 1,
                "items": [
                    {
                        "name": "real-project",
                        "full_name": "owner/real-project",
                        "owner": {"login": "owner"},
                        "description": "A real repository",
                        "html_url": "https://github.com/owner/real-project",
                        "language": "Python",
                        "stargazers_count": 5000,
                        "forks_count": 300,
                        "open_issues_count": 12,
                        "license": {"spdx_id": "MIT"},
                        "topics": ["python"],
                        "pushed_at": "2026-11-20T00:00:00Z",
                        "updated_at": "2026-11-20T00:00:00Z",
                    }
                ],
            }
        )

    client = make_client(handler)
    response = await client.get("/api/repos/search", params={"q": "cli", "language": "Python", "category": "Developer Tools", "minStars": 1000, "perPage": 5})
    assert response.status_code == 200
    data = response.json()
    assert "language:Python" in captured["q"]
    assert "topic:developer-tools" in captured["q"]
    assert "stars:>=1000" in captured["q"]
    assert data["items"][0]["activityLevel"] == "active"
    assert data["items"][0]["contributionAvailable"] is True


@pytest.mark.asyncio
async def test_issue_matching_revalidates_open_status(make_client) -> None:
    stale = {
        "number": 1,
        "title": "Improve API error handling",
        "body": "Python FastAPI error handling with tests",
        "html_url": "https://github.com/owner/repo/issues/1",
        "repository_url": "https://api.github.com/repos/owner/repo",
        "labels": [{"name": "good first issue"}],
        "created_at": "2026-10-01T00:00:00Z",
        "updated_at": "2026-10-02T00:00:00Z",
        "comments": 1,
        "state": "open",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/users/octocat":
            return json_response(USER)
        if path == "/users/octocat/repos":
            return json_response(REPOS)
        if path.endswith("/languages"):
            return json_response({"Python": 5000})
        if path == "/search/issues":
            return json_response({"total_count": 1, "items": [stale]})
        if path == "/repos/owner/repo":
            return json_response({"language": "Python"})
        if path == "/repos/owner/repo/issues/1":
            return json_response({**stale, "state": "closed"})
        return json_response({}, 404)

    client = make_client(handler)
    response = await client.post("/api/issues/match", json={"username": "octocat", "limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["matches"] == []
    assert data["skippedCount"] == 1
    assert data["revalidatedCount"] == 0


@pytest.mark.asyncio
async def test_readme_doctor_returns_before_and_after(make_client) -> None:
    readme = "# Demo\n\n## Installation\n\nsome text\n"

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/repos/owner/demo":
            return json_response({**REPOS[0], "name": "demo", "full_name": "owner/demo", "owner": {"login": "owner"}})
        if path == "/repos/owner/demo/git/trees/HEAD":
            return json_response({"tree": [{"path": "README.md", "type": "blob", "size": 100}], "truncated": False})
        if path == "/repos/owner/demo/readme":
            import base64

            return json_response({"encoding": "base64", "content": base64.b64encode(readme.encode()).decode()})
        return json_response({}, 404)

    client = make_client(handler)
    response = await client.post("/api/repository/readme", json={"repository": "https://github.com/owner/demo"})
    assert response.status_code == 200
    data = response.json()
    assert data["analysis"]["score"] < 100
    assert "## Usage" in data["suggested"]
    assert data["original"] == readme
    assert data["writeAction"]["enabled"] is False


@pytest.mark.asyncio
async def test_programs_are_verified_shape(make_client) -> None:
    client = make_client(lambda request: json_response({}))
    response = await client.get("/api/programs", params={"beginnerFriendly": "true"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert all(program["officialUrl"].startswith("https://") for program in data["items"])
    assert all(program["applicationDeadline"] is None or isinstance(program["applicationDeadline"], str) for program in data["items"])
    assert all(program["lastVerified"] == "2026-11-26" for program in data["items"])


@pytest.mark.asyncio
async def test_ai_is_disabled_without_key(api_client: httpx.AsyncClient) -> None:
    status = await api_client.get("/api/ai/status")
    assert status.json()["enabled"] is False
    completion = await api_client.post("/api/ai/complete", json={"prompt": "hello"})
    assert completion.status_code == 503
    assert completion.json()["error"]["code"] == "ai_not_configured"


@pytest.mark.asyncio
async def test_validation_rejects_non_github_host(make_client) -> None:
    client = make_client(lambda request: json_response({}))
    response = await client.post("/api/repository/readme", json={"repository": "https://evil.example.com/owner/repo"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.asyncio
async def test_rate_limit_is_mapped_to_429(github_client: GitHubClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response({"message": "rate limited"}, 403, {"x-ratelimit-remaining": "0"})

    import httpx as _httpx

    client = GitHubClient(
        github_client.settings,
        github_client.cache,
        _httpx.AsyncClient(transport=_httpx.MockTransport(handler), base_url=github_client.settings.github_api_base),
    )
    with pytest.raises(Exception) as excinfo:
        await client.get_user("octocat")
    assert getattr(excinfo.value, "status_code", None) == 429
