from __future__ import annotations

import time

import pytest

from app.core.cache import TTLCache
from app.core.errors import ValidationError
from app.core.validation import parse_repo, parse_username
from app.services import codebase, docs, issue_match, pr_guard, readme, reports
from app.services.scoring import compute_legacy_score


def test_repo_url_validation_blocks_ssrf() -> None:
    assert parse_repo("https://github.com/owner/repo") == ("owner", "repo")
    assert parse_repo("owner/repo.git") == ("owner", "repo")
    with pytest.raises(ValidationError):
        parse_repo("https://evil.example/owner/repo")
    with pytest.raises(ValidationError):
        parse_repo("https://github.com/owner/repo/../../secret")
    assert parse_username("https://github.com/octocat") == "octocat"
    with pytest.raises(ValidationError):
        parse_username("bad user!")


def test_ttl_cache_expires() -> None:
    cache = TTLCache(ttl_seconds=1, max_entries=10)
    cache.set("key", {"value": 1})
    assert cache.get("key") == {"value": 1}
    time.sleep(1.05)
    assert cache.get("key") is None
    assert cache.stats()["misses"] == 1


def test_legacy_score_matches_javascript_formula() -> None:
    user = {"public_repos": 3, "followers": 100, "created_at": "2011-01-26T19:01:12Z"}
    result = compute_legacy_score(user, {"totalStars": 1210}, {"Python": 5000, "HTML": 1000})
    assert result["breakdown"]["stars"] == 30
    assert result["breakdown"]["repos"] == 8
    assert result["breakdown"]["followers"] == 11
    assert result["breakdown"]["langs"] == 2
    assert result["breakdown"]["age"] == 15
    assert 0 <= result["score"] <= 100


def test_readme_analyzer_detects_missing_sections_and_empty_heading() -> None:
    report = readme.analyze("# Demo\n\n## Usage\n\n## License\n\ntext\n", ["LICENSE"])
    assert report["score"] < 100
    ids = {finding["id"] for finding in report["findings"]}
    assert "missing_installation" in ids
    assert "empty_section" in ids
    assert "no_screenshots" in ids


def test_readme_analyzer_detects_unclosed_code_fence() -> None:
    report = readme.analyze("# Demo\n\n## Overview\n\ntext\n\n```python\nprint(1)\n", [])
    assert any(finding["id"] == "unclosed_code_fence" for finding in report["findings"])


def test_issue_complexity_uses_labels_and_evidence() -> None:
    easy = {"title": "Fix typo", "body": "Change readme text", "labels": [{"name": "good first issue"}], "comments": 0, "created_at": "2026-11-01T00:00:00Z"}
    hard = {"title": "Rewrite authentication architecture", "body": "x " * 900, "labels": [{"name": "security"}], "comments": 20, "created_at": "2026-01-01T00:00:00Z"}
    assert issue_match.analyze_issue(easy)["difficulty"] == "beginner"
    assert issue_match.analyze_issue(hard)["difficulty"] == "advanced"


def test_codebase_ask_returns_evidence_with_lines() -> None:
    files = {"backend/app/auth.py": "def verify_token(token):\n    return decode_jwt(token)\n"}
    result = codebase.ask_codebase("Where is authentication implemented?", files)
    assert result["hits"][0]["path"] == "backend/app/auth.py"
    assert result["hits"][0]["line"] == 1
    assert result["hits"][0]["confidence"] in {"high", "medium", "low"}


def test_pr_guard_distinguishes_confirmed_and_hypotheses() -> None:
    pr = {"number": 7, "title": "Fix parser (#12)", "body": "", "html_url": "https://github.com/o/r/pull/7", "user": {"login": "dev"}, "state": "open", "base": {"ref": "main"}, "head": {"ref": "fix"}}
    files = [{"filename": "src/parser.py", "status": "modified", "additions": 1, "deletions": 1, "patch": "-def old_api():\n+def new_api():"}]
    report = pr_guard.analyze(pr, files, [], ["src/other.py"])
    ids = {item["id"] for item in report["confirmedFindings"]}
    assert "no_tests_in_diff" in ids
    assert "issue_references" in ids
    assert any(item["id"] == "possible_breaking_change" for item in report["hypotheses"])
    assert report["changeImpact"][0]["confidence"] == "hypothesis"


def test_docs_generator_uses_repository_context() -> None:
    repo = {"name": "demo", "owner": {"login": "owner"}, "description": "A demo"}
    guide = docs.generate("contributing", repo)
    security = docs.generate("security", repo)
    assert "# Contributing to demo" in guide
    assert "Do not open a public issue" in security
    with pytest.raises(ValueError):
        docs.generate("unknown", repo)


def test_report_exports_are_real_serializations() -> None:
    payload = {"profile": {"login": "octocat"}, "scores": {"score": 42}, "items": [{"id": 1}]}
    json_report = reports.export_report(payload, "json")
    csv_report = reports.export_report(payload, "csv")
    md_report = reports.export_report(payload, "markdown")
    assert '"login": "octocat"' in json_report["content"]
    assert "profile,login,octocat" in csv_report["content"]
    assert "## Profile" in md_report["content"]
    with pytest.raises(ValueError):
        reports.export_report(payload, "pdf")
