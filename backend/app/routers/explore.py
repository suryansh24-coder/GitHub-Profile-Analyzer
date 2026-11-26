from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Query, Request

from ..core.validation import parse_pagination
from ..services.github import GitHubClient

router = APIRouter(prefix="/api", tags=["discovery"])

CATEGORY_TOPICS = {
    "Artificial Intelligence": "topic:artificial-intelligence",
    "Machine Learning": "topic:machine-learning",
    "Generative AI": "topic:generative-ai",
    "Data Science": "topic:data-science",
    "Web Development": "topic:web-development",
    "Backend Development": "topic:backend",
    "Frontend Development": "topic:frontend",
    "DevOps": "topic:devops",
    "Cloud Computing": "topic:cloud-computing",
    "Cybersecurity": "topic:security",
    "Blockchain": "topic:blockchain",
    "Developer Tools": "topic:developer-tools",
    "Mobile Development": "topic:mobile",
    "Open Source Infrastructure": "topic:open-source",
    "Education Technology": "topic:education",
    "Healthcare Technology": "topic:healthcare",
}


def _activity_level(pushed_at: str | None) -> tuple[str, int | None]:
    if not pushed_at:
        return "unknown", None
    try:
        pushed = datetime.fromisoformat(str(pushed_at).replace("Z", "+00:00"))
        days = (datetime.now(timezone.utc) - pushed).days
    except ValueError:
        return "unknown", None
    if days <= 30:
        return "active", days
    if days <= 180:
        return "moderate", days
    if days <= 365:
        return "low", days
    return "inactive", days


def _map_repo(item: dict[str, object]) -> dict[str, object]:
    level, days = _activity_level(str(item.get("pushed_at") or ""))
    indicators = []
    if int(item.get("stargazers_count") or 0) >= 1000:
        indicators.append("Community interest (1000+ stars)")
    if int(item.get("open_issues_count") or 0) > 0:
        indicators.append("Open issues available")
    if item.get("license"):
        indicators.append("License declared")
    if level == "active":
        indicators.append("Recent pushes")
    return {
        "name": item.get("name"),
        "fullName": item.get("full_name"),
        "owner": (item.get("owner") or {}).get("login") if isinstance(item.get("owner"), dict) else None,
        "description": item.get("description"),
        "htmlUrl": item.get("html_url"),
        "language": item.get("language"),
        "stars": item.get("stargazers_count"),
        "forks": item.get("forks_count"),
        "openIssues": item.get("open_issues_count"),
        "license": (item.get("license") or {}).get("spdx_id") if isinstance(item.get("license"), dict) else None,
        "topics": (item.get("topics") or [])[:8],
        "pushedAt": item.get("pushed_at"),
        "updatedAt": item.get("updated_at"),
        "activityLevel": level,
        "daysSincePush": days,
        "healthIndicators": indicators,
        "contributionAvailable": int(item.get("open_issues_count") or 0) > 0,
    }


def _build_query(
    query: str,
    language: str | None,
    category: str | None,
    min_stars: int | None,
    pushed_within_days: int | None,
) -> str:
    parts = [query.strip()[:200]]
    if language:
        parts.append(f"language:{language}")
    if category and category in CATEGORY_TOPICS:
        parts.append(CATEGORY_TOPICS[category])
    if min_stars is not None:
        parts.append(f"stars:>={min_stars}")
    if pushed_within_days is not None:
        target = date.today() - timedelta(days=pushed_within_days)
        parts.append(f"pushed:>={target.isoformat()}")
    parts.append("archived:false")
    return " ".join(part for part in parts if part)


@router.get("/repos/search")
async def search_repositories(
    request: Request,
    q: str = "",
    language: str | None = None,
    category: str | None = None,
    minStars: int | None = Query(default=None, ge=0, le=1_000_000),
    pushedWithinDays: int | None = Query(default=None, ge=1, le=3650),
    sort: str = "stars",
    page: int = 1,
    perPage: int = 12,
) -> dict[str, object]:
    if sort not in {"stars", "updated", "forks", "help-wanted-issues"}:
        sort = "stars"
    page, per_page = parse_pagination(page, perPage)
    client: GitHubClient = request.app.state.github
    query = _build_query(q, language, category, minStars, pushedWithinDays)
    result = await client.search_repositories(query, sort=sort, per_page=per_page, page=page)
    items = result.get("items") or []
    return {
        "query": query,
        "totalCount": result.get("total_count", 0),
        "page": page,
        "perPage": per_page,
        "hasMore": bool(result.get("total_count", 0) > page * per_page),
        "items": [_map_repo(item) for item in items],
        "categories": list(CATEGORY_TOPICS.keys()),
    }


@router.get("/repos/rescue")
async def search_rescue_candidates(
    request: Request,
    language: str | None = None,
    minStars: int = 25,
    inactiveDays: int = 365,
    page: int = 1,
    perPage: int = 12,
) -> dict[str, object]:
    page, per_page = parse_pagination(page, perPage)
    client: GitHubClient = request.app.state.github
    threshold = date.today() - timedelta(days=inactiveDays)
    query = f"pushed:<{threshold.isoformat()} stars:>={minStars} archived:false"
    if language:
        query += f" language:{language}"
    result = await client.search_repositories(query, sort="updated", per_page=per_page, page=page)
    candidates = []
    for item in result.get("items") or []:
        mapped = _map_repo(item)
        signals = []
        if mapped["daysSincePush"] is not None:
            signals.append(f"No pushes in {mapped['daysSincePush']} days.")
        if int(mapped["openIssues"] or 0) > 0:
            signals.append(f"{mapped['openIssues']} open issues may need triage.")
        if not mapped["license"]:
            signals.append("No license detected in search metadata.")
        candidates.append({**mapped, "maintenanceSignals": signals, "label": "may benefit from contributors"})
    return {
        "query": query,
        "totalCount": result.get("total_count", 0),
        "page": page,
        "perPage": per_page,
        "hasMore": bool(result.get("total_count", 0) > page * per_page),
        "items": candidates,
        "disclaimer": "Signals are suggestions from public metadata, not a claim that a project is abandoned. Maintainers decide maintenance status.",
    }


@router.get("/repos/{owner}/{repo}")
async def get_repository(owner: str, repo: str, request: Request) -> dict[str, object]:
    client: GitHubClient = request.app.state.github
    data = await client.get_repository(owner, repo)
    return _map_repo(data)


@router.get("/developers/search")
async def search_developers(
    request: Request,
    q: str = "",
    language: str | None = None,
    page: int = 1,
    perPage: int = 12,
) -> dict[str, object]:
    page, per_page = parse_pagination(page, perPage)
    client: GitHubClient = request.app.state.github
    query = " ".join(part for part in [q.strip()[:150], f"language:{language}" if language else "", "type:user"] if part)
    result = await client.search_users(query, per_page=per_page, page=page)
    items = [
        {
            "login": item.get("login"),
            "avatarUrl": item.get("avatar_url"),
            "htmlUrl": item.get("html_url"),
            "type": item.get("type"),
            "score": item.get("score"),
        }
        for item in result.get("items") or []
    ]
    return {
        "query": query,
        "totalCount": result.get("total_count", 0),
        "page": page,
        "perPage": per_page,
        "hasMore": bool(result.get("total_count", 0) > page * per_page),
        "items": items,
        "note": "Demonstrated technology experience is only verified when a developer profile is analysed.",
    }
