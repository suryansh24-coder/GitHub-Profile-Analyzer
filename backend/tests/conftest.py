from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.cache import TTLCache  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.services.ai import AIService  # noqa: E402
from app.services.github import GitHubClient  # noqa: E402

AppHandler = Callable[[httpx.Request], httpx.Response]


def json_response(data: Any, status_code: int = 200, headers: dict[str, str] | None = None) -> httpx.Response:
    return httpx.Response(status_code, json=data, headers=headers or {})


@pytest.fixture
def cache() -> TTLCache:
    return TTLCache(60, 100)


@pytest.fixture
def github_client(cache: TTLCache) -> GitHubClient:
    transport = httpx.MockTransport(lambda request: json_response({}))
    return GitHubClient(settings, cache, httpx.AsyncClient(transport=transport, base_url=settings.github_api_base))


@pytest.fixture
def api_client(cache: TTLCache) -> httpx.AsyncClient:
    transport = httpx.MockTransport(lambda request: json_response({}))
    github = GitHubClient(settings, cache, httpx.AsyncClient(transport=transport, base_url=settings.github_api_base))
    app.state.cache = cache
    app.state.github = github
    app.state.ai = AIService(settings, httpx.AsyncClient(transport=transport))
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")


@pytest.fixture
def make_client(cache: TTLCache) -> Callable[[AppHandler], httpx.AsyncClient]:
    def factory(handler: AppHandler) -> httpx.AsyncClient:
        github = GitHubClient(
            settings,
            cache,
            httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url=settings.github_api_base),
        )
        app.state.cache = cache
        app.state.github = github
        app.state.ai = AIService(settings, httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")

    return factory


def body_of(request: httpx.Request) -> dict[str, Any]:
    return json.loads(request.content or b"{}")
