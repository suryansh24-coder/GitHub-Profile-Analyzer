from __future__ import annotations

import os
import re
from collections import Counter, defaultdict
from typing import Any

ENTRYPOINT_PATTERNS = (
    "main.py", "app.py", "server.py", "index.js", "server.js", "index.ts", "main.go", "program.cs",
    "src/index", "src/main", "cmd/", "application.ts", "app.ts",
)
CONFIG_FILES = ("package.json", "pyproject.toml", "requirements.txt", "go.mod", "cargo.toml", "dockerfile", ".env.example", "vite.config", "next.config")
PY_IMPORT = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.,\s]+))", re.MULTILINE)
JS_IMPORT = re.compile(r"(?:from\s+|require\()['\"]([^'\"]+)['\"]")
ROUTE_PATTERN = re.compile(r"@(?:app|router|api)\.(get|post|put|patch|delete)\(['\"]([^'\"]+)", re.IGNORECASE)
JS_ROUTE_PATTERN = re.compile(r"\.(get|post|put|patch|delete)\(['\"]([^'\"]+)['\"]", re.IGNORECASE)
DB_PATTERN = re.compile(r"(create table|sqlalchemy|prisma|mongoose|sequelize|gorm|CREATE TABLE)", re.IGNORECASE)
AUTH_PATTERN = re.compile(r"(jwt|oauth|session|login|authenticate|authorization|password)", re.IGNORECASE)


def _external_modules(content: str, path: str) -> list[str]:
    found: list[str] = []
    if path.endswith(".py"):
        for match in PY_IMPORT.finditer(content):
            value = match.group(1) or match.group(2) or ""
            for part in value.split(","):
                module = part.strip().split(".")[0]
                if module and module not in {".", "from", "import"}:
                    found.append(module)
    elif path.endswith((".js", ".jsx", ".ts", ".tsx")):
        for module in JS_IMPORT.findall(content):
            if not module.startswith(".") and not module.startswith("/"):
                found.append(module.split("/")[0].replace("@", ""))
    elif path.endswith(".go"):
        for module in re.findall(r'"([a-z0-9.-]+\.[a-z]{2,}/[^"]+)"', content):
            found.append(module.split("/")[0])
    return list(dict.fromkeys(found))


def _local_links(content: str, path: str, all_paths: list[str]) -> list[str]:
    links = []
    if path.endswith(".py"):
        for match in re.finditer(r"from\s+([\w.]+)\s+import", content):
            candidate = match.group(1).replace(".", "/") + ".py"
            if candidate in all_paths:
                links.append(candidate)
    elif path.endswith((".js", ".jsx", ".ts", ".tsx")):
        for module in JS_IMPORT.findall(content):
            if module.startswith("."):
                base = os.path.normpath(os.path.join(os.path.dirname(path), module)).replace("\\", "/")
                for candidate in (base + ".ts", base + ".js", base + "/index.ts", base + "/index.js"):
                    if candidate in all_paths:
                        links.append(candidate)
    return list(dict.fromkeys(links))


def analyze(files: dict[str, str], repo: dict[str, Any] | None = None) -> dict[str, Any]:
    paths = sorted(files.keys())
    extensions = Counter(os.path.splitext(path)[1].lower() or "(none)" for path in paths)
    top_dirs = Counter(path.split("/")[0] for path in paths if "/" in path)
    entrypoints = [path for path in paths if any(pattern in path.lower() for pattern in ENTRYPOINT_PATTERNS)]
    important = [path for path in paths if any(name in path.lower() for name in CONFIG_FILES)]
    important += [path for path in paths if "readme" in path.lower()]

    modules: dict[str, dict[str, Any]] = {}
    external: set[str] = set()
    routes: list[dict[str, str]] = []
    db_hits: list[str] = []
    auth_hits: list[str] = []
    for path, content in files.items():
        imports = _external_modules(content, path)
        external.update(imports)
        links = _local_links(content, path, paths)
        modules[path] = {"imports": imports, "localLinks": links, "lines": len(content.splitlines())}
        for method, endpoint in ROUTE_PATTERN.findall(content):
            routes.append({"method": method.upper(), "path": endpoint, "file": path})
        for method, endpoint in JS_ROUTE_PATTERN.findall(content):
            routes.append({"method": method.upper(), "path": endpoint, "file": path})
        if DB_PATTERN.search(content):
            db_hits.append(path)
        if AUTH_PATTERN.search(content) or any(word in path.lower() for word in ("auth", "login", "session")):
            auth_hits.append(path)

    graph = defaultdict(list)
    for path, data in modules.items():
        for link in data["localLinks"]:
            graph[path].append(link)

    stack = sorted(external)[:30]
    frontend_paths = [path for path in paths if path.endswith((".tsx", ".jsx", ".vue", ".svelte")) or "src/components" in path]
    backend_paths = [path for path in paths if path.endswith(".py") or "controllers" in path or "routes" in path]
    onboarding = [
        f"Read {entrypoints[0]} to find the application entry point." if entrypoints else "Identify the entry point from the repository root files.",
        f"Install dependencies using the manifest in {important[0]}." if any("package" in path or "requirement" in path or "pyproject" in path for path in important) else "Locate the dependency manifest and install dependencies.",
        "Copy any .env.example file to .env and fill values locally; never commit secrets.",
    ]
    if routes:
        onboarding.append(f"Trace the {routes[0]['method']} {routes[0]['path']} route in {routes[0]['file']} to understand request flow.")
    if db_hits:
        onboarding.append(f"Inspect database model definitions in {db_hits[0]}.")

    return {
        "statistics": {"filesAnalysed": len(paths), "extensions": dict(extensions.most_common(12)), "topDirectories": dict(top_dirs.most_common(12))},
        "entrypoints": entrypoints[:12],
        "importantFiles": list(dict.fromkeys(important))[:20],
        "dependencyGraph": {"externalPackages": stack, "packageCount": len(external)},
        "moduleRelationships": [{"from": key, "to": value} for key, targets in graph.items() for value in targets][:200],
        "apiFlow": routes[:50],
        "databaseModels": {"files": db_hits[:20], "note": "Detected from static text patterns; verify against actual schema files."},
        "authentication": {"files": auth_hits[:20], "note": "Keyword-based detection; verify the implementation manually."},
        "frontendBackendRelationship": {"frontendFiles": len(frontend_paths), "backendFiles": len(backend_paths), "note": "Based on file extensions and directory names."},
        "executionFlow": ([f"Start at {entrypoints[0]}"] if entrypoints else []) + [f"Follow imports to {target}" for target in (graph.get(entrypoints[0], [])[:5] if entrypoints else [])],
        "onboarding": onboarding,
        "limitations": "Static analysis only. No repository code was executed, and no LLM was used. Results are evidence-based but not exhaustive.",
        "_paths": paths,
    }


def ask_codebase(question: str, files: dict[str, str], maximum: int = 8) -> dict[str, Any]:
    terms = [term.lower() for term in re.findall(r"[A-Za-z0-9_]{3,}", question) if term.lower() not in {"where", "which", "what", "how", "does", "the", "and", "for", "with", "this", "that", "file", "implemented", "handles", "process"}]
    if not terms:
        return {"hits": [], "note": "Question did not contain searchable technical terms."}
    hits: list[dict[str, Any]] = []
    for path, content in files.items():
        lines = content.splitlines()
        score = 0
        best: tuple[int, str] | None = None
        for index, line in enumerate(lines, start=1):
            lower = line.lower()
            matched = sum(1 for term in terms if term in lower or (len(term) > 5 and term[:4] in lower))
            if matched > score:
                score = matched
                best = (index, line.strip())
        path_score = sum(1 for term in terms if term[:4] in path.lower())
        if score == 0 and path_score and lines:
            score = path_score
            best = (1, lines[0].strip())
        if score and best:
            hits.append(
                {
                    "path": path,
                    "line": best[0],
                    "excerpt": best[1][:240],
                    "confidence": "high" if score >= 2 else "medium" if os.path.basename(path).lower() in terms else "low",
                    "evidenceTerms": [term for term in terms if term in best[1].lower()],
                }
            )
    hits.sort(key=lambda item: -len(item["evidenceTerms"]))
    return {
        "hits": hits[:maximum],
        "note": "Deterministic keyword evidence search over fetched source files. No generated answer is asserted; verify the cited lines.",
    }
