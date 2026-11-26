from __future__ import annotations

import math
import re
from collections import Counter
from datetime import date, datetime, timezone
from typing import Any

TECHNOLOGY_SIGNALS: dict[str, tuple[str, ...]] = {
    "Python": ("python", "fastapi", "django", "flask", "pandas", "numpy", "pytest"),
    "JavaScript": ("javascript", "node", "react", "next.js", "express", "vue"),
    "TypeScript": ("typescript", "tsx", "nestjs"),
    "Java": ("java", "spring boot", "maven", "gradle"),
    "C++": ("c++", "cpp", "cmake"),
    "C": ("\bc\b", "cmake"),
    "Go": ("\bgo\b", "golang", "gin"),
    "Rust": ("rust", "cargo"),
    "Ruby": ("ruby", "rails"),
    "PHP": ("php", "laravel"),
    "Swift": ("swift", "ios"),
    "Kotlin": ("kotlin", "android"),
    "SQL": ("sql", "postgres", "mysql", "sqlite"),
    "MongoDB": ("mongodb", "mongo"),
    "Docker": ("docker", "dockerfile", "container"),
    "Kubernetes": ("kubernetes", "helm", "k8s"),
    "AWS": ("aws", "lambda", "s3", "ec2"),
    "Azure": ("azure",),
    "GCP": ("gcp", "google cloud"),
    "CI/CD": ("github actions", "workflow", "jenkins", "ci/cd"),
    "Machine Learning": ("machine learning", "scikit", "tensorflow", "pytorch", "ml "),
    "Generative AI": ("llm", "generative", "openai", "langchain", "rag"),
    "Data Science": ("data science", "visualization", "analytics", "jupyter"),
    "Web Development": ("web", "frontend", "backend", "api", "html", "css"),
    "Cybersecurity": ("security", "pentest", "encrypt", "vulnerability"),
    "Blockchain": ("blockchain", "smart contract", "solidity", "web3"),
    "Mobile Development": ("mobile", "android", "ios", "flutter", "react native"),
    "DevOps": ("devops", "terraform", "ansible", "nginx"),
}

DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Artificial Intelligence / ML": ("machine learning", "deep learning", "neural", "tensorflow", "pytorch", "llm", "ai "),
    "Web Development": ("web app", "website", "frontend", "backend", "api", "react", "next.js"),
    "Data Science": ("data science", "analytics", "dashboard", "visualization", "dataset"),
    "DevOps / Cloud": ("docker", "kubernetes", "terraform", "ci/cd", "cloud", "devops"),
    "Cybersecurity": ("security", "vulnerability", "encryption", "pentest"),
    "Blockchain": ("blockchain", "solidity", "smart contract", "web3"),
    "Mobile Development": ("android", "ios", "flutter", "mobile app"),
    "Developer Tools": ("cli", "developer tool", "editor", "sdk", "library"),
    "Education": ("education", "learning", "tutorial", "students"),
}


def _js_round(value: float) -> int:
    return math.floor(value + 0.5)


def _safe_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _text(repo: dict[str, Any]) -> str:
    parts = [str(repo.get("name") or ""), str(repo.get("description") or "")]
    parts.extend(str(topic) for topic in repo.get("topics") or [])
    return " ".join(parts).lower()


def compute_legacy_score(user: dict[str, Any], stats: dict[str, Any], languages: dict[str, int]) -> dict[str, Any]:
    stars = int(stats.get("totalStars") or 0)
    public_repos = int(user.get("public_repos") or 0)
    followers = int(user.get("followers") or 0)
    star_score = min(30, _js_round(30 * math.log10(stars + 1) / math.log10(1001)))
    repo_score = min(25, _js_round(25 * math.log10(public_repos + 1) / math.log10(101)))
    follower_score = min(20, _js_round(20 * math.log10(followers + 1) / math.log10(5001)))
    language_score = min(10, len(languages))
    created = _safe_date(user.get("created_at"))
    years = max(0.0, (datetime.now(timezone.utc) - created).days / 365.25) if created else 0.0
    age_score = min(15, _js_round(15 * min(years, 10) / 10))
    total = star_score + repo_score + follower_score + language_score + age_score
    tier = "Beginner"
    tier_class = "beginner"
    if total >= 80:
        tier, tier_class = "🏆 Elite Dev", "elite"
    elif total >= 60:
        tier, tier_class = "💜 Advanced", "advanced"
    elif total >= 35:
        tier, tier_class = "🔵 Intermediate", "intermediate"
    return {
        "score": total,
        "tier": tier,
        "tierClass": tier_class,
        "breakdown": {
            "stars": star_score,
            "repos": repo_score,
            "followers": follower_score,
            "langs": language_score,
            "age": age_score,
        },
    }


def build_skill_map(repos: list[dict[str, Any]], languages: dict[str, int]) -> dict[str, Any]:
    total_bytes = sum(languages.values()) or 1
    evidence: dict[str, list[str]] = {}
    for repo in repos:
        text = _text(repo)
        for tech, signals in TECHNOLOGY_SIGNALS.items():
            matched = any(re.search(signal, text) for signal in signals)
            if repo.get("language") and repo["language"].lower() == tech.lower():
                matched = True
            if matched:
                evidence.setdefault(tech, []).append(f"Repository `{repo.get('name')}` references {tech}.")
        language_name = repo.get("language")
        if language_name:
            evidence.setdefault(language_name, []).append(
                f"Repository `{repo.get('name')}` uses {language_name} as its primary language."
            )

    skills = []
    for tech, items in evidence.items():
        unique = list(dict.fromkeys(items))
        count = len(unique)
        byte_share = 100 * languages.get(tech, 0) / total_bytes
        if count >= 4 or byte_share >= 30:
            level = "strong"
        elif count >= 2 or byte_share >= 10:
            level = "moderate"
        else:
            level = "limited"
        skills.append(
            {
                "name": tech,
                "level": level,
                "evidenceCount": count,
                "evidence": unique[:5],
                "basis": "public repositories and language bytes",
            }
        )
    skills.sort(key=lambda item: (-item["evidenceCount"], item["name"]))

    domains = []
    joined_text = " ".join(_text(repo) for repo in repos)
    for domain, keywords in DOMAIN_KEYWORDS.items():
        hits = [repo.get("name") for repo in repos if any(word in _text(repo) for word in keywords)]
        if hits:
            domains.append({"name": domain, "repositoryCount": len(hits), "examples": hits[:4]})
    domains.sort(key=lambda item: -item["repositoryCount"])

    return {
        "skills": skills,
        "domains": domains,
        "note": "Skills are inferred only from public repository evidence. Absence from public repositories is not evidence that a developer lacks a skill.",
    }


def build_timeline(repos: list[dict[str, Any]], languages: dict[str, int]) -> dict[str, Any]:
    by_year: Counter[int] = Counter()
    adoption: dict[str, int] = {}
    for repo in repos:
        created = _safe_date(repo.get("created_at"))
        if not created:
            continue
        year = created.year
        by_year[year] += 1
        language = repo.get("language")
        if language and (language not in adoption or year < adoption[language]):
            adoption[language] = year
    return {
        "repositoriesPerYear": [{"year": year, "count": count} for year, count in sorted(by_year.items())],
        "technologyAdoption": [{"technology": key, "firstYear": value} for key, value in sorted(adoption.items())],
        "languageBytes": languages,
    }


def profile_completeness(user: dict[str, Any]) -> dict[str, Any]:
    fields = {
        "name": bool(user.get("name")),
        "bio": bool(user.get("bio")),
        "location": bool(user.get("location")),
        "company": bool(user.get("company")),
        "blog": bool(user.get("blog")),
        "email": bool(user.get("email")),
        "avatar": bool(user.get("avatar_url")),
    }
    filled = sum(1 for value in fields.values() if value)
    return {
        "fields": [{"field": key, "present": value} for key, value in fields.items()],
        "percentage": round(100 * filled / len(fields)),
    }


def _component(name: str, raw: float, maximum: float, weight: int, explanation: str) -> dict[str, Any]:
    points = round(weight * min(1.0, raw / maximum), 1) if maximum else 0.0
    return {
        "name": name,
        "raw": round(raw, 2),
        "maximum": maximum,
        "weight": weight,
        "points": points,
        "explanation": explanation,
    }


def compute_scores(
    user: dict[str, Any], repos: list[dict[str, Any]], languages: dict[str, int], skill_map: dict[str, Any]
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    created = _safe_date(user.get("created_at"))
    age_days = max(0, (now - created).days) if created else 0
    recent = 0
    for repo in repos:
        pushed = _safe_date(repo.get("pushed_at")) or _safe_date(repo.get("updated_at"))
        if pushed and (now - pushed).days <= 90:
            recent += 1

    described = sum(1 for repo in repos if repo.get("description"))
    with_topics = sum(1 for repo in repos if repo.get("topics"))
    licensed = sum(1 for repo in repos if repo.get("license"))
    original = [repo for repo in repos if not repo.get("fork")]
    stars = sum(int(repo.get("stargazers_count") or 0) for repo in repos)
    max_stars = max((int(repo.get("stargazers_count") or 0) for repo in repos), default=0)
    language_count = len(languages)
    skill_count = len(skill_map.get("skills") or [])
    domain_count = len(skill_map.get("domains") or [])
    total_repos = len(repos) or 1
    completeness = profile_completeness(user)["percentage"]

    activity_components = [
        _component("Repositories pushed in last 90 days", recent, 10, 40, "Counts public repositories pushed recently."),
        _component("Account age in years", age_days / 365.25, 10, 30, "Rewards sustained public account history."),
        _component("Repository creation spread", len({(_safe_date(r.get("created_at")) or now).year for r in repos}), 6, 30, "Counts distinct years with public repositories."),
    ]
    quality_components = [
        _component("Repositories with descriptions", 100 * described / total_repos, 100, 35, "Percentage of public repositories with a description."),
        _component("Repositories with topics", 100 * with_topics / total_repos, 100, 20, "Percentage of public repositories with topic tags."),
        _component("Most-starred repository", math.log10(max_stars + 1), 4, 25, "Log-scaled popularity of the strongest repository."),
        _component("Original repositories", 100 * len(original) / total_repos, 100, 20, "Share of original repositories versus forks."),
    ]
    diversity_components = [
        _component("Distinct languages", language_count, 10, 40, "Unique languages measured by byte counts."),
        _component("Detected technologies", skill_count, 20, 35, "Technologies with public repository evidence."),
        _component("Detected domains", domain_count, 8, 25, "Distinct technical domains inferred from repository metadata."),
    ]
    oss_components = [
        _component("Licensed original repositories", licensed, 10, 35, "Original public repositories declaring a license."),
        _component("Repositories with open issues", sum(1 for r in repos if int(r.get("open_issues_count") or 0) > 0), 10, 25, "Public repositories with an active issue tracker."),
        _component("Topic-tagged repositories", with_topics, 10, 20, "Repositories discoverable through GitHub topics."),
        _component("Total stars on original work", math.log10(sum(int(r.get("stargazers_count") or 0) for r in original) + 1), 4, 20, "Log-scaled reach of original repositories."),
    ]
    readiness_components = [
        _component("Portfolio quality", sum(c["points"] for c in quality_components), 100, 30, "Derived from the portfolio quality score."),
        _component("Technical diversity", sum(c["points"] for c in diversity_components), 100, 25, "Derived from the technical diversity score."),
        _component("Open-source engagement", sum(c["points"] for c in oss_components), 100, 20, "Derived from the open-source engagement score."),
        _component("Profile completeness", completeness, 100, 15, "Public profile fields populated on GitHub."),
        _component("Sustained activity", sum(c["points"] for c in activity_components), 100, 10, "Derived from the activity score."),
    ]

    def score_block(name: str, components: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "name": name,
            "score": round(sum(c["points"] for c in components), 1),
            "components": components,
            "caveat": "Heuristic based on public repository metadata; not a measure of engineering competence.",
        }

    return {
        "activity": score_block("Developer Activity Score", activity_components),
        "portfolio": score_block("Portfolio Quality Score", quality_components),
        "diversity": score_block("Technical Diversity Score", diversity_components),
        "openSource": score_block("Open Source Engagement Score", oss_components),
        "career": score_block("Career Readiness Score", readiness_components),
        "legacy": compute_legacy_score(user, {"totalStars": stars}, languages),
        "totals": {"stars": stars, "originalRepositories": len(original), "describedRepositories": described},
    }
