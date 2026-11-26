# System Overview

Version: 1.0 (target architecture)
Status: design baseline for the `feat/developer-ecosystem` branch

## Product direction

GitHub Profile Analyzer becomes a single-page developer intelligence workspace. The product hierarchy is
deliberately contributor-first:

1. Open-source discovery
2. Contribution matching
3. Developer intelligence
4. Repository improvement
5. Developer collaboration
6. Maintainer intelligence
7. AI developer tools

The original profile analyzer remains a first-class view and keeps its scoring model and charts.

## High-level architecture

```
Browser (static SPA, hash routing)
├── index.html                 app shell + preserved legacy analyzer markup
├── style.css                  preserved legacy analyzer styles
├── script.js                  preserved legacy analyzer logic (GitHub REST, charts, theme)
├── assets/css/app.css         premium dashboard design system (loaded after style.css)
└── assets/js/
    ├── api.js                 backend client, timeout, error normalization
    ├── ui.js                  escaping, formatting, states, modal, toast, pagination
    ├── app.js                 router, shell, global search, notifications, settings
    └── views/*.js             feature modules (render + interaction handlers)

Backend (FastAPI, Python)
├── backend/app/main.py        app factory, CORS, error handlers, static fallback
├── backend/app/core/          config, TTL cache, structured logging, error types
├── backend/app/services/      github, scoring, readme, repo_health, issue_match,
│                              codebase, pr_guard, programs, docs, ai
├── backend/app/routers/       profile, explore, issues, repository, programs,
│                              community, reports, system
└── backend/tests/             API, service and security tests (pytest + httpx)
```

## Design principles

- **No fabricated data.** Repositories, issues, pull requests and profiles come from the GitHub REST
  API. Program records link to official sites and never invent deadlines. Local collaboration listings
  are explicitly labelled as stored in the browser.
- **Deterministic first, AI optional.** README analysis, health checks, scoring, issue matching, static
  codebase analysis and PR heuristics work without an LLM. AI endpoints require a server-side key and
  return a clear setup error otherwise.
- **Secrets stay server-side.** `GITHUB_TOKEN` and `OPENAI_API_KEY` are read only by the backend. The
  frontend never receives them.
- **Untrusted repositories are data only.** Repository content is fetched as text and analysed
  statically. No repository script is executed, no shell command is run on repository content, and
  file sizes / request counts are bounded.
- **Graceful degradation.** If the backend is not running (e.g. a pure static deployment), the legacy
  analyzer still works through the public GitHub API, and feature views show a setup message instead of
  fake content.

## API contract summary

All backend routes are prefixed with `/api`. Full interactive documentation is generated at `/docs`.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Backend status and integration availability (no secret values) |
| GET | `/api/profile/{username}` | Enrich developer intelligence (scores, DNA, skill map, timeline) |
| GET | `/api/repos/search` | Search real repositories with filters and pagination |
| GET | `/api/repos/{owner}/{repo}` | Repository metadata |
| GET | `/api/issues/search` | Search real open issues with filters and pagination |
| POST | `/api/issues/match` | Match real issues against a skill map from a GitHub username |
| GET | `/api/issues/{owner}/{repo}/{number}` | Issue detail + deterministic complexity analysis |
| POST | `/api/repository/readme` | README health report and before/after suggestion |
| POST | `/api/repository/health` | Repository health, dependencies and security-policy checks |
| POST | `/api/repository/xray` | Static architecture/onboarding analysis |
| POST | `/api/repository/pr-guard` | Deterministic pull-request change-impact report |
| POST | `/api/repository/docs-generate` | Generate CONTRIBUTING / CODE_OF_CONDUCT / SECURITY docs |
| GET | `/api/programs` | Verified program registry with filters |
| POST | `/api/ai/complete` | Optional LLM helper (503 when unconfigured) |
| POST | `/api/reports/export` | Serialize an analysis payload to JSON/CSV/Markdown |

## Data model

There is no database in the first implementation. This is intentional: the platform needs no user
accounts to provide value, and it avoids storing GitHub profile data or secrets. Bookmarks, local
collaboration listings, themes and notification preferences live in browser `localStorage` and are
labelled as local data. The normalized PostgreSQL schema for a future authenticated deployment is
documented in `docs/architecture/DATABASE_ARCHITECTURE.md` and is not claimed as implemented.

## Caching and rate limits

- A bounded in-memory TTL cache keyed by request path + normalized query string avoids repeat GitHub
  calls. Default TTL: 15 minutes for repository/profile data, 5 minutes for search results.
- All GitHub calls go through one client that reads `X-RateLimit-Remaining`, maps 403/429 to a clear
  API error, and supports an optional server-side token.
- Request timeouts are enforced with `httpx`.

## Frontend navigation map

| Sidebar item | View | Data source |
| --- | --- | --- |
| Overview | Landing + quick analysis entry | local state / legacy analyzer |
| Developer Intelligence | Preserved legacy analyzer + new score cards | legacy GitHub REST + backend enrichment |
| Open Source Explorer | Repository search, filters, bookmarks | `/api/repos/search` |
| Find Contributions | Issue discovery and skill matching | `/api/issues/search`, `/api/issues/match` |
| Issue Intelligence | Issue complexity and triage detail | `/api/issues/...` |
| Repository Doctor | README doctor + repo health | `/api/repository/readme`, `/api/repository/health` |
| Codebase X-Ray | Static structure analysis and Q&A evidence | `/api/repository/xray` |
| Pull Request Guardian | PR change impact | `/api/repository/pr-guard` |
| Open Source Programs | Verified registry, filters, reminders | `/api/programs` |
| Developer Community | Developer discovery from GitHub search | `/api/repos/search` + GitHub user search proxy |
| Collaboration Hub | Local listings and peer-review requests | `localStorage` |
| Developer Roadmap | Evidence-based skill gaps and roadmap | `/api/profile/{username}` |
| AI Developer Lab | Optional AI tools with integration status | `/api/ai/complete` |
| Reports & Analytics | Exports and saved items | client-side export + `/api/reports/export` |
| Settings | API base, tokens guidance, theme, data management | local settings |

## Security boundaries

1. Repo URL parsing accepts only `github.com/owner/repo` forms; other hosts are rejected (SSRF guard).
2. Markdown is rendered as escaped text or sanitized HTML generated by the backend, never as raw
   untrusted HTML.
3. External links use `rel="noopener noreferrer"`.
4. Secrets are read from environment variables by the backend only.
5. Write actions to GitHub require an explicit user click, a separate OAuth token supplied at runtime,
   and a confirmation step; no write endpoint is enabled by default.
