from __future__ import annotations

import base64
from typing import Any
from urllib.parse import quote

import httpx

from ..core.cache import TTLCache
from ..core.config import Settings
from ..core.errors import AppError, NotFoundError, UpstreamError, ValidationError
from ..core.validation import parse_pagination


class GitHubClient:
    def __init__(self, settings: Settings, cache: TTLCache, client: httpx.AsyncClient | None = None) -> None:
        self.settings = settings
        self.cache = cache
        self._client = client or httpx.AsyncClient(
            base_url=settings.github_api_base,
            timeout=settings.github_timeout,
            follow_redirects=True,
        )
        self.owns_client = client is None

    async def close(self) -> None:
        if self.owns_client:
            await self._client.aclose()

    async def request(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        ttl_seconds: int | None = None,
        cache: bool = True,
    ) -> Any:
        clean_params = {key: value for key, value in (params or {}).items() if value not in (None, "")}
        suffix = "&".join(f"{key}={value}" for key, value in sorted(clean_params.items()))
        cache_key = f"github:{path}:{suffix}"
        if cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "github-profile-analyzer/2.0",
        }
        if self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"

        try:
            response = await self._client.get(path, params=clean_params, headers=headers)
        except httpx.TimeoutException as exc:
            raise UpstreamError("GitHub API request timed out. Try again shortly.") from exc
        except httpx.HTTPError as exc:
            raise UpstreamError("GitHub API is unreachable.") from exc

        if response.status_code == 404:
            raise NotFoundError("GitHub resource not found. Check the owner, repository and issue number.")
        if response.status_code in {401, 403, 429}:
            remaining = response.headers.get("x-ratelimit-remaining")
            if remaining == "0" or response.status_code == 429:
                reset = response.headers.get("x-ratelimit-reset")
                detail = {"rateLimitRemaining": remaining, "rateLimitReset": reset}
                raise UpstreamError(
                    "GitHub API rate limit reached. Configure GITHUB_TOKEN on the backend or wait for the limit to reset.",
                    status_code=429,
                    detail=detail,
                )
            raise UpstreamError("GitHub API rejected the request. Check backend credentials.", status_code=403)
        if response.status_code >= 500:
            raise UpstreamError("GitHub API is temporarily unavailable.")

        try:
            payload = response.json()
        except ValueError as exc:
            raise UpstreamError("GitHub API returned an unreadable response.") from exc

        if cache:
            self.cache.set(cache_key, payload, ttl_seconds)
        return payload

    async def get_user(self, username: str) -> dict[str, Any]:
        return await self.request(f"/users/{quote(username, safe='')}")

    async def get_repos(self, username: str, per_page: int = 100, page: int = 1) -> list[dict[str, Any]]:
        _, size = parse_pagination(page, per_page)
        data = await self.request(
            f"/users/{quote(username, safe='')}/repos",
            params={"per_page": size, "page": page, "sort": "updated", "type": "owner"},
        )
        if not isinstance(data, list):
            raise UpstreamError("Unexpected repository response from GitHub.")
        return data

    async def get_languages(self, owner: str, repo: str) -> dict[str, int]:
        data = await self.request(f"/repos/{quote(owner, safe='')}/{quote(repo, safe='')}/languages")
        return data if isinstance(data, dict) else {}

    async def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        return await self.request(f"/repos/{quote(owner, safe='')}/{quote(repo, safe='')}")

    async def search_repositories(
        self, query: str, *, sort: str = "stars", per_page: int = 12, page: int = 1
    ) -> dict[str, Any]:
        _, size = parse_pagination(page, per_page)
        return await self.request(
            "/search/repositories",
            params={"q": query, "sort": sort, "order": "desc", "per_page": size, "page": page},
            ttl_seconds=300,
        )

    async def search_issues(
        self, query: str, *, sort: str = "updated", per_page: int = 12, page: int = 1
    ) -> dict[str, Any]:
        _, size = parse_pagination(page, per_page)
        return await self.request(
            "/search/issues",
            params={"q": query, "sort": sort, "order": "desc", "per_page": size, "page": page},
            ttl_seconds=180,
        )

    async def search_users(self, query: str, *, per_page: int = 12, page: int = 1) -> dict[str, Any]:
        _, size = parse_pagination(page, per_page)
        return await self.request(
            "/search/users",
            params={"q": query, "per_page": size, "page": page},
            ttl_seconds=300,
        )

    async def get_issue(self, owner: str, repo: str, number: int) -> dict[str, Any]:
        if number < 1:
            raise ValidationError("Issue number must be positive.")
        return await self.request(
            f"/repos/{quote(owner, safe='')}/{quote(repo, safe='')}/issues/{number}",
            ttl_seconds=120,
            cache=False,
        )

    async def get_pull_request(self, owner: str, repo: str, number: int) -> dict[str, Any]:
        if number < 1:
            raise ValidationError("Pull request number must be positive.")
        return await self.request(f"/repos/{quote(owner, safe='')}/{quote(repo, safe='')}/pulls/{number}")

    async def get_pull_request_files(
        self, owner: str, repo: str, number: int, maximum: int = 100
    ) -> list[dict[str, Any]]:
        data = await self.request(
            f"/repos/{quote(owner, safe='')}/{quote(repo, safe='')}/pulls/{number}/files",
            params={"per_page": min(maximum, 100)},
        )
        return data if isinstance(data, list) else []

    async def get_tree(self, owner: str, repo: str, ref: str | None = None) -> dict[str, Any]:
        base = f"/repos/{quote(owner, safe='')}/{quote(repo, safe='')}"
        tree_ref = quote(ref, safe="") if ref else "HEAD"
        return await self.request(f"{base}/git/trees/{tree_ref}", params={"recursive": "1"})

    async def get_contents(self, owner: str, repo: str, path: str) -> str | None:
        if not path or path.startswith("/") or ".." in path.split("/"):
            raise ValidationError("Invalid repository file path.")
        safe_path = "/".join(quote(part, safe="") for part in path.split("/"))
        data = await self.request(f"/repos/{quote(owner, safe='')}/{quote(repo, safe='')}/contents/{safe_path}")
        if not isinstance(data, dict) or data.get("encoding") != "base64":
            return None
        size = int(data.get("size") or 0)
        if size > 200_000:
            return None
        content = str(data.get("content") or "").replace("\n", "")
        try:
            return base64.b64decode(content).decode("utf-8", errors="replace")
        except (ValueError, TypeError):
            return None

    async def get_readme_text(self, owner: str, repo: str) -> str | None:
        try:
            data = await self.request(f"/repos/{quote(owner, safe='')}/{quote(repo, safe='')}/readme")
        except NotFoundError:
            return None
        if isinstance(data, dict) and data.get("encoding") == "base64":
            content = str(data.get("content") or "").replace("\n", "")
            try:
                return base64.b64decode(content).decode("utf-8", errors="replace")
            except (ValueError, TypeError):
                return None
        return None

    async def rate_limit(self) -> dict[str, Any]:
        try:
            return await self.request("/rate_limit", cache=False)
        except AppError:
            return {"resources": {}}
