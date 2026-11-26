# API Reference

Base path: `/api`. OpenAPI docs: `/docs`. All responses are JSON. Errors follow `{"error": {"code": "...", "message": "..."}}`.

## System

- `GET /api/health` — service state, optional integration status and confirmation that no token is exposed to the frontend.
- `GET /api/cache` — bounded in-memory cache statistics.
- `DELETE /api/cache` — clear the cache.

## Profile

- `GET /api/profile/{username}` — profile, statistics, languages, legacy score, five transparent scores, skill map, timeline, completeness and limitations.

## Explore

- `GET /api/repos/search?q=&language=&category=&minStars=&pushedWithinDays=&sort=&page=&perPage=`
- `GET /api/repos/rescue?language=&pushedWithinDays=&minStars=&page=&perPage=`
- `GET /api/repos/{owner}/{repo}` — mapped repository details.
- `GET /api/developers/search?q=&language=&location=&perPage=`

Categories are documented in `backend/app/routers/explore.py`. Repository results include `activityLevel`, `healthIndicators` and `contributionAvailable`, but never claim abandonment.

## Issues

- `GET /api/issues/search?q=&repository=&label=&language=&sort=&page=&perPage=` — always adds `is:issue is:open` and excludes pull requests.
- `GET /api/issues/{owner}/{repo}/{number}` — issue detail and body.
- `POST /api/issues/match` with `{ "username", "query", "repository", "labels", "limit" }` — revalidates candidates before scoring.

## Programs

- `GET /api/programs?status=&search=&beginnerFriendly=&mentorship=&technology=&upcomingDays=`

Valid statuses: `upcoming`, `applications_open`, `applications_closed`, `ongoing`, `completed`, `status_unverified`.

## Repository intelligence

All are `POST` requests:

- `/api/repository/readme` — `{ "repository" }`
- `/api/repository/health` — `{ "repository" }`
- `/api/repository/xray` — `{ "repository", "question" }`
- `/api/repository/pr-guard` — `{ "repository", "number", "includeOpenPullRequests" }`
- `/api/repository/docs-generate` — `{ "repository", "kind" }`

`repository` accepts `owner/repo` or a `https://github.com/owner/repo` URL. Non-GitHub hosts are rejected. Docs kinds: `contributing`, `code_of_conduct`, `security`, `architecture`.

## AI

- `GET /api/ai/status`
- `POST /api/ai/complete` — `{ "prompt", "context", "maxTokens" }`. Returns 503 with `ai_not_configured` when no backend key exists.

## Reports

- `POST /api/reports/export` — `{ "format": "json|csv|markdown", "title", "payload" }`. Returns `filename`, `contentType` and `content`.

## Authentication and rate limits

`GITHUB_TOKEN` is read only by the backend and sent as a Bearer token to GitHub. Without it, GitHub allows 60 requests/hour per IP. The backend maps GitHub 403/429 with `x-ratelimit-remaining: 0` to HTTP 429 so the UI can explain the limit.

No API endpoint accepts or returns secrets.
