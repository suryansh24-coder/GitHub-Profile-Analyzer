from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

DEPENDENCY_FILES = {
    "requirements.txt": "pip",
    "pyproject.toml": "pip",
    "package.json": "npm",
    "cargo.toml": "cargo",
    "go.mod": "go",
    "pom.xml": "maven",
    "gemfile": "bundler",
    "composer.json": "composer",
}
TEST_MARKERS = ("test", "tests", "spec", "__tests__", "pytest.ini", "vitest.config", "jest.config")
CI_MARKERS = (".github/workflows", ".gitlab-ci.yml", "jenkinsfile", ".circleci", "azure-pipelines.yml")


def _check(check_id: str, category: str, status: str, severity: str, message: str, recommendation: str) -> dict[str, str]:
    return {
        "id": check_id,
        "category": category,
        "status": status,
        "severity": severity,
        "message": message,
        "recommendation": recommendation,
    }


def parse_dependencies(files: dict[str, str]) -> list[dict[str, str]]:
    dependencies: list[dict[str, str]] = []
    for path, content in files.items():
        name = path.lower().rsplit("/", 1)[-1]
        if name == "requirements.txt":
            for line in content.splitlines()[:200]:
                match = re.match(r"^\s*([A-Za-z0-9_.-]+)\s*([<>=~!]=?[^\s;,]*)?", line)
                if match and not line.lstrip().startswith("#"):
                    dependencies.append({"name": match.group(1), "version": match.group(2) or "unpinned", "source": path})
        elif name == "package.json":
            try:
                data = json.loads(content)
            except ValueError:
                continue
            for group in ("dependencies", "devDependencies"):
                for key, value in (data.get(group) or {}).items():
                    dependencies.append({"name": str(key), "version": str(value), "source": f"{path}:{group}"})
    return dependencies[:200]


def analyze(repo: dict[str, Any], files: dict[str, str], readme_analysis: dict[str, Any] | None = None) -> dict[str, Any]:
    paths = [str(path).lower() for path in files.keys()]
    all_files = [str(path).lower() for path in (repo.get("_tree") or [])] or paths
    has = lambda marker: any(marker in path for path in all_files)

    checks: list[dict[str, str]] = []
    readme_present = any(path in {"readme.md", "readme.rst", "readme.txt"} or "readme" in path for path in all_files)
    checks.append(_check("readme", "documentation", "pass" if readme_present else "fail", "high" if not readme_present else "info", "README found." if readme_present else "No README found.", "Add a README with setup and usage instructions."))
    contributing = any("contributing" in path for path in all_files)
    checks.append(_check("contributing", "documentation", "pass" if contributing else "warning", "medium", "Contributing guide found." if contributing else "No CONTRIBUTING guide found.", "Add CONTRIBUTING.md with contribution steps."))
    license_file = any(path.startswith("license") or "license." in path for path in all_files)
    license_ok = bool(repo.get("license")) or license_file
    checks.append(_check("license", "legal", "pass" if license_ok else "fail", "high", "License metadata or file found." if license_ok else "No license detected.", "Add an OSI-approved license file and metadata."))
    security_policy = any("security.md" in path or "security_policy" in path for path in all_files)
    checks.append(_check("security_policy", "security", "pass" if security_policy else "warning", "medium", "Security policy found." if security_policy else "No SECURITY.md found.", "Add SECURITY.md with a private disclosure process."))

    tests_present = any(any(marker in path for marker in TEST_MARKERS) for path in all_files)
    checks.append(_check("tests", "quality", "pass" if tests_present else "warning", "medium", "Test infrastructure found." if tests_present else "No test files or test configuration detected.", "Add automated tests and a test runner configuration."))
    ci_present = any(any(marker in path for marker in CI_MARKERS) for path in all_files)
    checks.append(_check("ci", "quality", "pass" if ci_present else "warning", "medium", "CI configuration found." if ci_present else "No CI workflow detected.", "Add a CI workflow that runs tests on pull requests."))

    dependency_files = sorted({path for path in all_files if path.rsplit("/", 1)[-1] in DEPENDENCY_FILES})
    checks.append(_check("dependencies", "quality", "pass" if dependency_files else "warning", "low", f"{len(dependency_files)} dependency manifest(s) found.", "Declare dependencies in a manifest file for reproducible installs."))

    pushed = repo.get("pushed_at") or repo.get("updated_at")
    days_since_push = None
    if pushed:
        try:
            pushed_dt = datetime.fromisoformat(str(pushed).replace("Z", "+00:00"))
            days_since_push = (datetime.now(timezone.utc) - pushed_dt).days
        except ValueError:
            days_since_push = None
    maintenance_status = "warning"
    if days_since_push is not None and days_since_push <= 90:
        maintenance_status = "pass"
    elif days_since_push is not None and days_since_push > 365:
        maintenance_status = "fail"
    checks.append(
        _check("maintenance", "activity", maintenance_status, "medium" if maintenance_status != "pass" else "info", f"Last push {days_since_push} days ago." if days_since_push is not None else "Last push date unavailable.", "Recent activity helps contributors know the project is maintained.")
    )
    if repo.get("archived"):
        checks.append(_check("archived", "activity", "fail", "high", "Repository is archived.", "Check the organization for an active successor project."))
    if repo.get("open_issues_count", 0) > 0:
        checks.append(_check("issues", "activity", "pass", "info", f"{repo['open_issues_count']} open issues tracked.", "Triage issues with labels to help new contributors."))
    else:
        checks.append(_check("issues", "activity", "warning", "low", "No open issues detected.", "Use issues to track work and contribution opportunities."))

    dependencies = parse_dependencies({key: value for key, value in files.items() if value is not None})
    score_map = {"pass": 1.0, "info": 1.0, "warning": 0.5, "fail": 0.0}
    weights = {"documentation": 25, "legal": 10, "security": 10, "quality": 20, "activity": 25, "legal_": 10}
    category_score: dict[str, float] = {}
    for check in checks:
        category = check["category"]
        weight = weights.get(category, 10)
        current = category_score.setdefault(category, {"points": 0.0, "max": 0.0})
        current["max"] += weight
        current["points"] += weight * score_map[check["status"]]
    components = [
        {"name": key, "points": round(value["points"], 1), "maximum": value["max"]}
        for key, value in category_score.items()
    ]
    total_possible = sum(item["maximum"] for item in components) or 1
    score = round(100 * sum(item["points"] for item in components) / total_possible)

    return {
        "score": score,
        "grade": "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 50 else "D",
        "components": components,
        "checks": checks,
        "dependencyFiles": dependency_files,
        "dependencies": dependencies,
        "dependencyIntelligence": {
            "status": "parsed_versions_only",
            "note": "Versions are read from repository manifests. No vulnerability database query was performed; verify advisories with the official GitHub Advisory Database or language-specific advisory sources.",
            "advisorySources": [
                "https://github.com/advisories",
                "https://osv.dev/",
            ],
        },
        "securityIntelligence": {
            "secretScanning": "not_performed",
            "note": "No secret values are scanned, logged or displayed. Connect an approved secret-scanning tool for production use.",
            "codeExecution": "none",
        },
        "readmeScore": (readme_analysis or {}).get("score"),
        "daysSincePush": days_since_push,
    }
