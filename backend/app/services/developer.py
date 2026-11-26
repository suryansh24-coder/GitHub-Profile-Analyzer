from __future__ import annotations

import asyncio
from typing import Any

from .github import GitHubClient
from .scoring import build_skill_map, build_timeline, compute_scores, profile_completeness


def summarize_repo(repo: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": repo.get("name"),
        "fullName": repo.get("full_name"),
        "description": repo.get("description"),
        "htmlUrl": repo.get("html_url"),
        "language": repo.get("language"),
        "stars": repo.get("stargazers_count"),
        "forks": repo.get("forks_count"),
        "openIssues": repo.get("open_issues_count"),
        "fork": bool(repo.get("fork")),
        "topics": (repo.get("topics") or [])[:8],
        "createdAt": repo.get("created_at"),
        "updatedAt": repo.get("updated_at"),
        "pushedAt": repo.get("pushed_at"),
        "license": (repo.get("license") or {}).get("spdx_id"),
    }


async def build_intelligence(client: GitHubClient, username: str, language_limit: int = 6) -> dict[str, Any]:
    user = await client.get_user(username)
    repos = await client.get_repos(username)
    canonical = str(user.get("login") or username)
    candidates = [repo for repo in repos if not repo.get("fork")]
    candidates.sort(key=lambda repo: int(repo.get("stargazers_count") or 0), reverse=True)
    selected = candidates[:language_limit]

    language_results = await asyncio.gather(
        *(
            client.get_languages(str(repo.get("owner", {}).get("login") or canonical), str(repo.get("name")))
            for repo in selected
        ),
        return_exceptions=True,
    )
    languages: dict[str, int] = {}
    for result in language_results:
        if isinstance(result, dict):
            for language, byte_count in result.items():
                languages[str(language)] = languages.get(str(language), 0) + int(byte_count or 0)
    fallback_used = False
    if not languages:
        fallback_used = True
        for repo in repos:
            language = repo.get("language")
            if language:
                languages[str(language)] = languages.get(str(language), 0) + 1

    skill_map = build_skill_map(repos, languages)
    scores = compute_scores(user, repos, languages, skill_map)
    stats = {
        "totalRepos": len(repos),
        "originalRepos": sum(1 for repo in repos if not repo.get("fork")),
        "forkedRepos": sum(1 for repo in repos if repo.get("fork")),
        "totalStars": sum(int(repo.get("stargazers_count") or 0) for repo in repos),
        "totalForks": sum(int(repo.get("forks_count") or 0) for repo in repos),
        "mostStarred": None,
        "mostRecent": None,
    }
    if repos:
        top = max(repos, key=lambda repo: int(repo.get("stargazers_count") or 0))
        stats["mostStarred"] = top.get("name")
        recent = max(repos, key=lambda repo: str(repo.get("updated_at") or ""))
        stats["mostRecent"] = recent.get("name")

    return {
        "profile": {
            "login": user.get("login"),
            "name": user.get("name"),
            "avatarUrl": user.get("avatar_url"),
            "htmlUrl": user.get("html_url"),
            "bio": user.get("bio"),
            "location": user.get("location"),
            "company": user.get("company"),
            "blog": user.get("blog"),
            "followers": user.get("followers"),
            "following": user.get("following"),
            "publicRepos": user.get("public_repos"),
            "createdAt": user.get("created_at"),
            "updatedAt": user.get("updated_at"),
        },
        "statistics": stats,
        "languages": dict(sorted(languages.items(), key=lambda item: -item[1])),
        "languageDataNote": "Byte counts from the top original repositories." if not fallback_used else "Fallback counts from repository primary-language fields because language endpoints were unavailable.",
        "scores": scores,
        "developerDna": skill_map,
        "growthTimeline": build_timeline(repos, languages),
        "profileCompleteness": profile_completeness(user),
        "repositories": [summarize_repo(repo) for repo in repos[:30]],
        "limitations": "Only public repository metadata is analysed. Private contributions, non-GitHub work and skills without public evidence are not represented.",
    }
