from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    github_token: str | None
    github_api_base: str
    github_timeout: float
    cache_ttl_seconds: int
    cache_max_entries: int
    openai_api_key: str | None
    openai_model: str
    openai_base_url: str
    cors_origins: tuple[str, ...]
    app_root: str

    @property
    def github_auth_enabled(self) -> bool:
        return bool(self.github_token)

    @property
    def ai_enabled(self) -> bool:
        return bool(self.openai_api_key)


def _default_cors_origins() -> tuple[str, ...]:
    origins = ["http://localhost:8000", "http://127.0.0.1:8000"]
    vercel_url = os.getenv("VERCEL_URL")
    if vercel_url:
        origins.append(f"https://{vercel_url}")
    return tuple(origins)


def get_settings() -> Settings:
    configured_origins = os.getenv("CORS_ORIGINS")
    origins = (
        tuple(origin.strip() for origin in configured_origins.split(",") if origin.strip())
        if configured_origins is not None
        else _default_cors_origins()
    )
    return Settings(
        github_token=os.getenv("GITHUB_TOKEN") or None,
        github_api_base=os.getenv("GITHUB_API_BASE", "https://api.github.com").rstrip("/"),
        github_timeout=float(os.getenv("GITHUB_TIMEOUT", "15")),
        cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "900")),
        cache_max_entries=int(os.getenv("CACHE_MAX_ENTRIES", "300")),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        cors_origins=origins,
        app_root=os.getenv("APP_ROOT", os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))),
    )


settings = get_settings()
