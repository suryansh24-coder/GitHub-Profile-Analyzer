from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

EASY_LABELS = ("good first issue", "beginner", "first-timers-only", "help wanted", "documentation", "starter")
HARD_LABELS = ("architecture", "security", "performance", "breaking", "refactor", "complex")
TECH_KEYWORDS = (
    "python", "javascript", "typescript", "react", "vue", "node", "java", "go", "rust", "c++", "sql",
    "docker", "kubernetes", "aws", "api", "frontend", "backend", "documentation", "test", "machine learning",
)


def _labels(issue: dict[str, Any]) -> list[str]:
    return [str(label.get("name") or "").lower() for label in issue.get("labels") or [] if isinstance(label, dict)]


def _age_days(issue: dict[str, Any]) -> int | None:
    created = issue.get("created_at")
    if not created:
        return None
    try:
        created_dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
        return max(0, (datetime.now(timezone.utc) - created_dt).days)
    except ValueError:
        return None


def analyze_issue(issue: dict[str, Any]) -> dict[str, Any]:
    labels = _labels(issue)
    body = str(issue.get("body") or "")
    title = str(issue.get("title") or "")
    words = len(body.split())
    comments = int(issue.get("comments") or 0)
    complexity = 20
    signals: list[str] = []

    if any(label in EASY_LABELS for label in labels):
        complexity -= 15
        signals.append("Label indicates a newcomer-friendly or documentation task.")
    if any(label in HARD_LABELS for label in labels):
        complexity += 25
        signals.append("Label suggests architectural, security or cross-cutting work.")
    if words > 1200:
        complexity += 25
        signals.append("Long issue body suggests detailed or multi-part requirements.")
    elif words < 80:
        complexity -= 8
        signals.append("Short issue body; requirements may need clarification with maintainers.")
    if comments > 10:
        complexity += 12
        signals.append("Many comments often indicate discussion or changing requirements.")
    if re.search(r"acceptance criteria|steps to reproduce|expected behavior", body, re.IGNORECASE):
        complexity -= 8
        signals.append("Issue includes reproduction or acceptance criteria.")
    if re.search(r"breaking change|migrate|rewrite|redesign", title + " " + body, re.IGNORECASE):
        complexity += 15
        signals.append("Issue mentions migration, rewrite or breaking change.")

    complexity = max(0, min(100, complexity))
    difficulty = "beginner" if complexity < 35 else "intermediate" if complexity < 70 else "advanced"
    effort = "small" if complexity < 35 else "medium" if complexity < 70 else "large"
    age = _age_days(issue)
    if age is not None and age > 365:
        signals.append("Issue is over a year old; confirm it is still relevant before starting.")

    return {
        "difficulty": difficulty,
        "complexityScore": complexity,
        "estimatedScope": effort,
        "signals": signals,
        "labels": labels,
        "ageDays": age,
        "hasAssignee": bool(issue.get("assignee")),
        "isOpen": str(issue.get("state") or "").lower() == "open",
        "isPullRequest": "pull_request" in issue,
    }


def _skill_weight(skill_map: dict[str, Any]) -> dict[str, float]:
    weights = {"strong": 1.0, "moderate": 0.75, "limited": 0.5}
    return {
        str(skill["name"]).lower(): weights.get(str(skill.get("level")), 0.5)
        for skill in skill_map.get("skills") or []
    }


def match_issue(
    issue: dict[str, Any],
    skill_map: dict[str, Any],
    repo_languages: dict[str, str],
    analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    detail = analysis or analyze_issue(issue)
    weights = _skill_weight(skill_map)
    full_name = str(issue.get("repository_url") or "").replace("https://api.github.com/repos/", "")
    language = repo_languages.get(full_name) or str((issue.get("repository") or {}).get("language") or "")
    text = (str(issue.get("title") or "") + " " + str(issue.get("body") or "")).lower()
    labels = detail["labels"]

    evidence: list[str] = []
    language_points = 0.0
    if language and language.lower() in weights:
        language_points = 30 * weights[language.lower()]
        evidence.append(f"Repository uses {language}, which appears in your public repository evidence.")
    elif language:
        evidence.append(f"Repository uses {language}; no public evidence of this language was found in the analysed profile.")

    matched_tech = []
    for tech in TECH_KEYWORDS:
        if tech in text or any(tech == label or tech in label for label in labels):
            if tech in weights:
                matched_tech.append(tech)
    tech_points = min(28, 9 * len(matched_tech))
    if matched_tech:
        evidence.append("Issue mentions technologies with repository evidence: " + ", ".join(matched_tech[:6]) + ".")

    label_points = 12 if any(label in EASY_LABELS for label in labels) else 4 if labels else 0
    if label_points >= 12:
        evidence.append("Issue is labelled as newcomer-friendly or documentation work.")

    complexity_points = 12 if detail["difficulty"] == "beginner" else 8 if detail["difficulty"] == "intermediate" else 3
    if detail["difficulty"] == "beginner":
        evidence.append("Estimated complexity is beginner-friendly.")

    age = detail.get("ageDays")
    activity_points = 10
    if age is not None and age > 365:
        activity_points = 3
        evidence.append("Issue is old; revalidate status with the maintainer before starting.")
    elif age is not None and age > 180:
        activity_points = 6

    score = round(language_points + tech_points + label_points + complexity_points + activity_points)
    score = min(100, score)

    guide = [
        f"Read the issue at {issue.get('html_url', 'the GitHub issue page')} and confirm it is still open and unassigned.",
        f"Search the repository for '{str(issue.get('title') or '')[:60]}' and related terms to locate candidate files.",
    ]
    if language:
        guide.append(f"Start with files written in {language}; inspect the module closest to the described behaviour.")
    if "documentation" in labels:
        guide.append("For documentation work, update the relevant README or docs page and check links and examples.")
    else:
        guide.append("Add or update a focused test that reproduces the expected behaviour before implementing the fix.")
    guide.append("Open a draft pull request early and ask the maintainer to confirm the approach.")

    return {
        "repository": full_name,
        "issueNumber": issue.get("number"),
        "title": issue.get("title"),
        "url": issue.get("html_url"),
        "labels": labels,
        "language": language,
        "matchScore": score,
        "difficulty": detail["difficulty"],
        "complexityScore": detail["complexityScore"],
        "whyRecommended": evidence or ["No direct skill overlap detected; treat this as a stretch opportunity."],
        "startingGuide": guide,
        "disclaimer": "Recommendations are heuristic. Issues are not reserved for you and maintainers decide whether to accept contributions.",
        "revalidated": bool(issue.get("_revalidated")),
    }
