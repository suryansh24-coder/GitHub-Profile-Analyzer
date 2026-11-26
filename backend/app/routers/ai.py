from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from ..services.ai import AIService

router = APIRouter(prefix="/api/ai", tags=["ai-tools"])


class CompletionRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    context: str = Field(default="", max_length=16000)
    maxTokens: int = Field(default=500, ge=64, le=800)


@router.get("/status")
async def ai_status(request: Request) -> dict[str, object]:
    service: AIService = request.app.state.ai
    return service.status()


@router.post("/complete")
async def complete(payload: CompletionRequest, request: Request) -> dict[str, object]:
    service: AIService = request.app.state.ai
    return await service.complete(payload.prompt, payload.context, payload.maxTokens)
