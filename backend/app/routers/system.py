from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
async def health(request: Request) -> dict[str, object]:
    github = request.app.state.github
    ai = request.app.state.ai
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "backend": "fastapi",
        "integrations": {
            "github": {
                "apiBase": github.settings.github_api_base,
                "authenticated": github.settings.github_auth_enabled,
                "tokenExposedToFrontend": False,
            },
            "ai": ai.status(),
        },
        "cache": request.app.state.cache.stats(),
    }


@router.get("/cache")
async def cache_stats(request: Request) -> dict[str, object]:
    return {"cache": request.app.state.cache.stats()}


@router.delete("/cache")
async def clear_cache(request: Request) -> dict[str, object]:
    return {"clearedEntries": request.app.state.cache.clear()}
