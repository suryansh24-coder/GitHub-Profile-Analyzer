from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from ..core.validation import parse_pagination, parse_repo, parse_username
from ..services.developer import build_intelligence
from ..services.github import GitHubClient
from ..services.issue_match import analyze_issue, match_issue

router = APIRouter(prefix="/api/issues", tags=["issue-intelligence"])


class MatchRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    query: str = Field(default="", max_length=200)
    repository: str | None = Field(default=None, max_length=200)
    labels: list[str] = Field(default_factory=list, max_length=5)
    limit: int = Field(default=10, ge=1, le=25)


def _issue_query(query: str, repository: str | None, labels: list[str], language: str | None) -> str:
    parts = ["is:issue", "is:open"]
    if repository:
        owner, repo = parse_repo(repository)
        parts.append(f"repo:{owner}/{repo}")
    if labels:
        for label in labels[:5]:
            cleaned = str(label).strip().replace('"', "")
            if cleaned:
                parts.append(f'label:"{cleaned}"')
    if language:
        parts.append(f"language:{language}")
    if query:
        parts.append(query.strip()[:200])
    return " ".join(parts)


def _map_issue(item: dict[str, Any]) -> dict[str, Any]:
    detail = analyze_issue(item)
    return {
        "number": item.get("number"),
        "title": item.get("title"),
        "htmlUrl": item.get("html_url"),
        "repositoryUrl": item.get("repository_url"),
        "repository": str(item.get("repository_url") or "").replace("https://api.github.com/repos/", ""),
        "labels": detail["labels"],
        "createdAt": item.get("created_at"),
        "updatedAt": item.get("updated_at"),
        "comments": item.get("comments"),
        "difficulty": detail["difficulty"],
        "complexityScore": detail["complexityScore"],
        "signals": detail["signals"],
        "ageDays": detail["ageDays"],
        "state": item.get("state"),
    }


@router.get("/search")
async def search_issues(
    request: Request,
    q: str = "",
    repository: str | None = None,
    label: list[str] = Query(default_factory=list),
    language: str | None = None,
    sort: str = "updated",
    page: int = 1,
    perPage: int = 12,
) -> dict[str, Any]:
    if sort not in {"updated", "created", "comments", "reactions"}:
        sort = "updated"
    page, per_page = parse_pagination(page, perPage)
    query = _issue_query(q, repository, label, language)
    client: GitHubClient = request.app.state.github
    result = await client.search_issues(query, sort=sort, per_page=per_page, page=page)
    items = [item for item in (result.get("items") or []) if "pull_request" not in item]
    return {
        "query": query,
        "totalCount": result.get("total_count", 0),
        "page": page,
        "perPage": per_page,
        "hasMore": bool(result.get("total_count", 0) > page * per_page),
        "items": [_map_issue(item) for item in items],
    }


@router.get("/{owner}/{repo}/{number}")
async def get_issue(owner: str, repo: str, number: int, request: Request) -> dict[str, Any]:
    client: GitHubClient = request.app.state.github
    issue = await client.get_issue(owner, repo, number)
    if "pull_request" in issue:
        return {"error": {"code": "not_an_issue", "message": "This number belongs to a pull request, not an issue."}}
    return {"issue": _map_issue(issue), "body": issue.get("body"), "htmlUrl": issue.get("html_url"), "author": (issue.get("user") or {}).get("login")}


@router.post("/match")
async def match_contributions(payload: MatchRequest, request: Request) -> dict[str, Any]:
    client: GitHubClient = request.app.state.github
    username = parse_username(payload.username)
    intelligence = await build_intelligence(client, username, language_limit=4)
    skill_map = intelligence["developerDna"]
    query = _issue_query(payload.query, payload.repository, payload.labels, None)
    search = await client.search_issues(query, sort="updated", per_page=min(30, payload.limit * 3), page=1)
    candidates = [item for item in (search.get("items") or []) if "pull_request" not in item][: payload.limit * 2]

    repo_languages: dict[str, str] = {}
    matches = []
    revalidated = 0
    skipped = 0
    for item in candidates:
        if len(matches) >= payload.limit:
            break
        repository_url = str(item.get("repository_url") or "")
        full_name = repository_url.replace("https://api.github.com/repos/", "")
        if full_name and full_name not in repo_languages:
            try:
                meta = await client.get_repository(*full_name.split("/", 1))
                repo_languages[full_name] = str(meta.get("language") or "")
            except Exception:
                repo_languages[full_name] = ""

        try:
            fresh = await client.get_issue(*full_name.split("/", 1), int(item.get("number") or 0))
        except Exception:
            skipped += 1
            continue
        if str(fresh.get("state") or "").lower() != "open" or "pull_request" in fresh or fresh.get("assignee"):
            skipped += 1
            continue
        fresh["_revalidated"] = True
        revalidated += 1
        matches.append(match_issue(fresh, skill_map, repo_languages))

    matches.sort(key=lambda entry: -entry["matchScore"])
    return {
        "username": username,
        "skillSummary": [
            {"name": skill["name"], "level": skill["level"]} for skill in skill_map["skills"][:12]
        ],
        "totalIssueCandidates": search.get("total_count", 0),
        "revalidatedCount": revalidated,
        "skippedCount": skipped,
        "matches": matches,
        "disclaimer": "Matches use real GitHub issues revalidated at request time. Nothing is reserved, and acceptance is at maintainer discretion.",
    }
