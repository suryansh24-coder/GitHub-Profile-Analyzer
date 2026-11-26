from __future__ import annotations

from fastapi import APIRouter, Request

from ..core.validation import parse_username
from ..services.developer import build_intelligence
from ..services.github import GitHubClient

router = APIRouter(prefix="/api", tags=["developer-intelligence"])


@router.get("/profile/{username}")
async def get_profile(username: str, request: Request) -> dict[str, object]:
    client: GitHubClient = request.app.state.github
    clean = parse_username(username)
    return await build_intelligence(client, clean)
