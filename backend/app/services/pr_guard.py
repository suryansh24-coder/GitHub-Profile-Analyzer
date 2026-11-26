from __future__ import annotations

import re
from typing import Any

BREAKING_PATTERNS = (
    r"-\s*(?:export|public)\s+",
    r"-\s*def\s+",
    r"-\s*CREATE\s+TABLE",
    r"-\s*@(?:app|router)\.(?:get|post|put|patch|delete)",
    r"-\s*(?:app|router)\.(?:get|post|put|patch|delete)\(",
)
TEST_MARKERS = ("test", "spec", "__tests__")


def analyze(
    pull_request: dict[str, Any],
    changed_files: list[dict[str, Any]],
    open_pull_requests: list[dict[str, Any]] | None = None,
    repository_files: list[str] | None = None,
) -> dict[str, Any]:
    changed = changed_files[:100]
    paths = [str(item.get("filename") or "") for item in changed]
    patch_text = "\n".join(str(item.get("patch") or "") for item in changed)
    title = str(pull_request.get("title") or "")
    body = str(pull_request.get("body") or "")

    confirmed: list[dict[str, str]] = []
    hypotheses: list[dict[str, str]] = []
    suggestions: list[str] = []

    if not paths:
        confirmed.append({"id": "no_files", "message": "No changed files were returned by GitHub.", "evidence": "GitHub files endpoint returned an empty list."})
    source_files = [path for path in paths if not any(marker in path.lower() for marker in TEST_MARKERS)]
    test_files = [path for path in paths if any(marker in path.lower() for marker in TEST_MARKERS)]
    if source_files and not test_files:
        confirmed.append({"id": "no_tests_in_diff", "message": "No test files were changed in this pull request.", "evidence": f"{len(source_files)} source file(s) changed; 0 test file(s) changed."})
        suggestions.append("Add or update tests covering the changed behaviour, or explain why tests are not applicable.")
    if any("readme" in path.lower() or path.lower().startswith("docs/") for path in paths):
        confirmed.append({"id": "docs_updated", "message": "Documentation files were changed.", "evidence": ", ".join(path for path in paths if "readme" in path.lower() or path.lower().startswith("docs/"))[:300]})
    else:
        suggestions.append("Check whether user-facing documentation needs updating for this change.")

    for pattern in BREAKING_PATTERNS:
        match = re.search(pattern, patch_text, re.IGNORECASE | re.MULTILINE)
        if match:
            hypotheses.append({
                "id": "possible_breaking_change",
                "message": "A removed declaration or route may be a breaking change.",
                "evidence": "Diff line starting with '-' matched a declaration/route pattern. Verify manually.",
            })
            break

    added_lines = [line for line in patch_text.splitlines() if line.startswith("+") and not line.startswith("+++")]
    if any("TODO" in line or "FIXME" in line for line in added_lines):
        hypotheses.append({"id": "todo_added", "message": "New TODO/FIXME markers were added.", "evidence": "Added diff lines contain TODO or FIXME."})
    if len(patch_text) > 60_000:
        hypotheses.append({"id": "large_diff", "message": "Large diff may be difficult to review.", "evidence": "Patch text exceeded the analysis sample limit."})

    related = sorted(set(re.findall(r"#(\d{1,6})", f"{title} {body}")))
    if related:
        confirmed.append({"id": "issue_references", "message": "Pull request references issue numbers.", "evidence": "Referenced: " + ", ".join(related[:10])})

    normalized_title = re.sub(r"[^a-z0-9 ]", "", title.lower())
    duplicates = []
    for pr in open_pull_requests or []:
        other = str(pr.get("title") or "")
        other_normalized = re.sub(r"[^a-z0-9 ]", "", other.lower())
        if other_normalized and other_normalized == normalized_title and pr.get("number") != pull_request.get("number"):
            duplicates.append({"number": pr.get("number"), "title": other, "url": pr.get("html_url")})
    if duplicates:
        hypotheses.append({"id": "possible_duplicate", "message": "Another open pull request has a matching title.", "evidence": "Exact normalized title match; verify scope manually."})

    impacted: list[dict[str, str]] = []
    directories = sorted({"/".join(path.split("/")[:-1]) for path in paths if "/" in path})
    for directory in directories:
        neighbours = [path for path in (repository_files or []) if path.startswith(directory + "/") and path not in paths][:6]
        impacted.append({"directory": directory, "relatedFiles": neighbours, "confidence": "hypothesis"})
    if not directories:
        impacted.append({"directory": "(repository root)", "relatedFiles": [path for path in (repository_files or []) if "/" not in path and path not in paths][:6], "confidence": "hypothesis"})

    reviewer_summary = [
        f"{len(changed)} file(s) changed with {sum(int(item.get('additions') or 0) for item in changed)} additions and {sum(int(item.get('deletions') or 0) for item in changed)} deletions.",
        f"Main areas: {', '.join(directories[:4]) if directories else 'repository root'}.",
        "Breaking-change and impact notes below are hypotheses from static diff inspection, not verified runtime behaviour.",
    ]

    return {
        "pullRequest": {
            "number": pull_request.get("number"),
            "title": title,
            "url": pull_request.get("html_url"),
            "author": (pull_request.get("user") or {}).get("login"),
            "state": pull_request.get("state"),
            "draft": pull_request.get("draft"),
            "base": (pull_request.get("base") or {}).get("ref"),
            "head": (pull_request.get("head") or {}).get("ref"),
        },
        "changedFiles": [
            {"filename": item.get("filename"), "status": item.get("status"), "additions": item.get("additions"), "deletions": item.get("deletions"), "changes": item.get("changes")}
            for item in changed
        ],
        "confirmedFindings": confirmed,
        "hypotheses": hypotheses,
        "changeImpact": impacted,
        "relatedIssues": related,
        "duplicateSignals": duplicates,
        "testRecommendations": suggestions,
        "reviewerSummary": reviewer_summary,
        "limitations": "No code was executed and no pull request was approved, merged or modified.",
    }
