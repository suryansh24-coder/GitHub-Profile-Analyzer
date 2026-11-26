from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .core.cache import TTLCache
from .core.config import settings
from .core.errors import AppError
from .routers import ai, explore, issues, programs, profile, reports, repository, system
from .services.ai import AIService
from .services.github import GitHubClient

logger = logging.getLogger("developer-ecosystem")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    cache = TTLCache(settings.cache_ttl_seconds, settings.cache_max_entries)
    github = GitHubClient(settings, cache)
    ai_service = AIService(settings)
    app.state.cache = cache
    app.state.github = github
    app.state.ai = ai_service
    logger.info("backend started github_authenticated=%s ai_enabled=%s", settings.github_auth_enabled, settings.ai_enabled)
    try:
        yield
    finally:
        await github.close()
        await ai_service.close()


app = FastAPI(
    title="GitHub Profile Analyzer — Developer Ecosystem API",
    version="2.0.0",
    description="Backend services for developer intelligence, open-source discovery, contribution matching and repository analysis.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

for router in (system.router, profile.router, explore.router, issues.router, repository.router, programs.router, ai.router, reports.router):
    app.include_router(router)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.as_dict())


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "invalid_request", "message": "Request validation failed.", "detail": exc.errors()}},
    )


@app.exception_handler(Exception)
async def unexpected_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error: %s", type(exc).__name__)
    return JSONResponse(status_code=500, content={"error": {"code": "internal_error", "message": "An unexpected error occurred."}})


@app.get("/", include_in_schema=False)
async def index() -> Response:
    index_path = f"{settings.app_root}/index.html"
    try:
        return FileResponse(index_path)
    except (OSError, RuntimeError):
        return JSONResponse({"service": "developer-ecosystem-api", "docs": "/docs"})


@app.get("/style.css", include_in_schema=False)
async def legacy_styles() -> Response:
    try:
        return FileResponse(f"{settings.app_root}/style.css", media_type="text/css")
    except (OSError, RuntimeError):
        return JSONResponse({"error": "style.css not found"}, status_code=404)


@app.get("/script.js", include_in_schema=False)
async def legacy_script() -> Response:
    try:
        return FileResponse(f"{settings.app_root}/script.js", media_type="application/javascript")
    except (OSError, RuntimeError):
        return JSONResponse({"error": "script.js not found"}, status_code=404)


app.mount("/assets", StaticFiles(directory=f"{settings.app_root}/assets", check_dir=False), name="assets")
app.mount("/docs-static", StaticFiles(directory=f"{settings.app_root}/docs", check_dir=False), name="docs-static")
