from __future__ import annotations

import json
from typing import Any

import httpx

from ..core.config import Settings
from ..core.errors import AppError, ValidationError


class AIService:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self.settings = settings
        self._client = client or httpx.AsyncClient(timeout=45.0)
        self.owns_client = client is None

    async def close(self) -> None:
        if self.owns_client:
            await self._client.aclose()

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.settings.ai_enabled,
            "model": self.settings.openai_model if self.settings.ai_enabled else None,
            "setup": "Set OPENAI_API_KEY on the backend to enable AI-assisted tools." if not self.settings.ai_enabled else "Configured via backend environment variables.",
            "keyExposedToFrontend": False,
        }

    async def complete(self, prompt: str, context: str = "", max_tokens: int = 500) -> dict[str, Any]:
        if not self.settings.ai_enabled:
            raise AppError(503, "ai_not_configured", "AI features require OPENAI_API_KEY on the backend. Deterministic tools remain available.")
        if not prompt.strip() or len(prompt) > 8000:
            raise ValidationError("Prompt must be between 1 and 8000 characters.")
        max_tokens = max(64, min(800, max_tokens))
        payload = {
            "model": self.settings.openai_model,
            "messages": [
                {"role": "system", "content": "You assist open-source developers. Cite provided file paths and line references. Never invent repository facts. If evidence is missing, say so."},
                {"role": "user", "content": f"{prompt}\n\nContext:\n{context[:16000]}"},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.2,
        }
        headers = {"Authorization": f"Bearer {self.settings.openai_api_key}", "Content-Type": "application/json"}
        try:
            response = await self._client.post(f"{self.settings.openai_base_url}/chat/completions", json=payload, headers=headers)
        except httpx.HTTPError as exc:
            raise AppError(502, "ai_provider_unavailable", "The AI provider could not be reached.", None) from exc
        if response.status_code == 401:
            raise AppError(502, "ai_provider_rejected", "The AI provider rejected the backend credential.")
        if response.status_code == 429:
            raise AppError(429, "ai_rate_limited", "AI provider rate limit reached. Try again later.")
        if response.status_code >= 500:
            raise AppError(502, "ai_provider_error", "The AI provider returned a server error.")
        try:
            data = response.json()
            text = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError) as exc:
            raise AppError(502, "ai_response_invalid", "The AI provider returned an unexpected response.") from exc
        return {
            "text": str(text),
            "model": self.settings.openai_model,
            "usage": data.get("usage") or {},
            "disclaimer": "AI output is a suggestion. Verify it against repository evidence before acting.",
        }
