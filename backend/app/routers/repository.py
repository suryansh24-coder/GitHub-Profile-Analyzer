from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from ..core.validation import parse_repo
from ..services import codebase as codebase_service
from ..services import docs as docs_service
from ..services import pr_guard as pr_service
from ..services import readme as readme_service
from ..services import repo_health
from ..services.github import GitHubClient

router = APIRouter(prefix="/api/repository", tags=["repository-intelligence"])

SOURCE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".rb", ".php", ".cs"}
PREFERRED_FILES = ("package.json", "pyproject.toml", "requirements.txt", "go.mod", "cargo.toml", "dockerfile", ".env.example", "readme.md")


class RepositoryRequest(BaseModel):
    repository: str = Field(min_length=3, max_length=300)


class XRayRequest(RepositoryRequest):
    question: str | None = Field(default=None, max_length=500)


class PullRequestRequest(RepositoryRequest):
    number: int = Field(ge=1, le=1_000_000)
    includeOpenPullRequests: bool = False


class DocsRequest(RepositoryRequest):
    kind: str = Field(default="contributing", pattern="^(contributing|code_of_conduct|security|architecture)$")


async def _context(client: GitHubClient, repository: str, maximum_files: int = 0) -> dict[str, Any]:
    owner, repo = parse_repo(repository)
    meta = await client.get_repository(owner, repo)
    tree: dict[str, Any] = {}
    try:
        tree = await client.get_tree(owner, repo, str(meta.get("default_branch") or "HEAD"))
    except Exception:
        tree = {}
    entries = tree.get("tree") or []
    paths = [
        str(entry.get("path"))
        for entry in entries
        if entry.get("type") == "blob" and int(entry.get("size") or 0) <= 200_000
    ]
    files: dict[str, str] = {}
    if maximum_files and paths:
        ranked = sorted(
            paths,
            key=lambda path: (
                0 if any(path.lower().endswith(name) or path.lower() == name for name in PREFERRED_FILES) else 1,
                0 if path.rsplit(".", 1)[-1].lower() in {"py", "ts", "tsx", "js", "jsx"} else 1,
                len(path),
            ),
        )
        selected = [path for path in ranked if path.rsplit(".", 1)[-1].lower() in SOURCE_EXTENSIONS or path.lower().endswith(PREFERRED_FILES)][:maximum_files]
        results = await asyncio.gather(
            *(client.get_contents(owner, repo, path) for path in selected),
            return_exceptions=True,
        )
        for path, content in zip(selected, results):
            if isinstance(content, str):
                files[path] = content
    return {
        "owner": owner,
        "repo": repo,
        "meta": meta,
        "paths": paths,
        "treeTruncated": bool(tree.get("truncated")),
        "files": files,
        "ownerRepo": f"{owner}/{repo}",
    }


@router.post("/readme")
async def readme_doctor(payload: RepositoryRequest, request: Request) -> dict[str, Any]:
    client: GitHubClient = request.app.state.github
    ctx = await _context(client, payload.repository)
    readme = await client.get_readme_text(ctx["owner"], ctx["repo"])
    analysis = readme_service.analyze(readme, ctx["paths"], ctx["meta"])
    suggestion = readme_service.suggest_readme(readme, ctx["meta"], ctx["paths"], analysis)
    return {
        "repository": ctx["ownerRepo"],
        "htmlUrl": ctx["meta"].get("html_url"),
        "defaultBranch": ctx["meta"].get("default_branch"),
        "analysis": analysis,
        "original": readme or "",
        "suggested": suggestion["suggested"],
        "changes": suggestion["changes"],
        "mode": suggestion["mode"],
        "warning": suggestion["warning"],
        "writeAction": {
            "enabled": False,
            "message": "No GitHub write action is available without explicit OAuth authorization. Review and commit changes manually.",
        },
    }


@router.post("/health")
async def repository_health(payload: RepositoryRequest, request: Request) -> dict[str, Any]:
    client: GitHubClient = request.app.state.github
    ctx = await _context(client, payload.repository, maximum_files=12)
    readme = await client.get_readme_text(ctx["owner"], ctx["repo"])
    readme_analysis = readme_service.analyze(readme, ctx["paths"], ctx["meta"])
    meta = dict(ctx["meta"])
    meta["_tree"] = ctx["paths"]
    result = repo_health.analyze(meta, ctx["files"], readme_analysis)
    return {
        "repository": ctx["ownerRepo"],
        "htmlUrl": ctx["meta"].get("html_url"),
        "health": result,
        "treeTruncated": ctx["treeTruncated"],
        "filesFetched": len(ctx["files"]),
    }


@router.post("/xray")
async def codebase_xray(payload: XRayRequest, request: Request) -> dict[str, Any]:
    client: GitHubClient = request.app.state.github
    ctx = await _context(client, payload.repository, maximum_files=24)
    analysis = codebase_service.analyze(ctx["files"], ctx["meta"])
    answer = codebase_service.ask_codebase(payload.question, ctx["files"]) if payload.question else None
    return {
        "repository": ctx["ownerRepo"],
        "htmlUrl": ctx["meta"].get("html_url"),
        "analysis": analysis,
        "askResult": answer,
        "treeTruncated": ctx["treeTruncated"],
        "filesFetched": len(ctx["files"]),
    }


@router.post("/pr-guard")
async def pull_request_guard(payload: PullRequestRequest, request: Request) -> dict[str, Any]:
    client: GitHubClient = request.app.state.github
    owner, repo = parse_repo(payload.repository)
    pull_request = await client.get_pull_request(owner, repo, payload.number)
    changed = await client.get_pull_request_files(owner, repo, payload.number)
    open_prs: list[dict[str, Any]] = []
    if payload.includeOpenPullRequests:
        data = await client.request(
            f"/repos/{owner}/{repo}/pulls",
            params={"state": "open", "per_page": 30, "sort": "updated"},
        )
        open_prs = data if isinstance(data, list) else []
    tree_paths: list[str] = []
    try:
        tree = await client.get_tree(owner, repo, str((pull_request.get("base") or {}).get("ref") or "HEAD"))
        tree_paths = [str(entry.get("path")) for entry in tree.get("tree") or [] if entry.get("type") == "blob"]
    except Exception:
        tree_paths = []
    return {
        "repository": f"{owner}/{repo}",
        "report": pr_service.analyze(pull_request, changed, open_prs, tree_paths),
    }


@router.post("/docs-generate")
async def generate_documentation(payload: DocsRequest, request: Request) -> dict[str, Any]:
    client: GitHubClient = request.app.state.github
    ctx = await _context(client, payload.repository, maximum_files=20 if payload.kind == "architecture" else 0)
    technical_context = codebase_service.analyze(ctx["files"], ctx["meta"]) if payload.kind == "architecture" else {}
    content = docs_service.generate(payload.kind, ctx["meta"], technical_context)
    return {
        "repository": ctx["ownerRepo"],
        "kind": payload.kind,
        "filename": {"contributing": "CONTRIBUTING.md", "code_of_conduct": "CODE_OF_CONDUCT.md", "security": "SECURITY.md", "architecture": "ARCHITECTURE.md"}[payload.kind],
        "content": content,
        "warning": "Generated draft. Review before adding it to a repository.",
    }
