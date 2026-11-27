# System Overview

**Version:** 2.0 · **Scope:** implemented system, not a target wishlist · **Last verified:** 2026-11-27

DevAtlas is a single-origin application: a static browser workspace, one FastAPI service, and bounded integrations with GitHub and an optional AI provider. It deliberately has no database and no write path.

---

## 1. System context

```mermaid
flowchart LR
    U["Contributor / maintainer"] --> UI["DevAtlas browser workspace"]
    UI --> API["FastAPI service<br/>/api/*"]
    UI --> LEG["Preserved legacy analyzer<br/>public GitHub API"]
    API --> GH["GitHub REST API"]
    API -.->|"optional"| AI["OpenAI-compatible API"]
    UI --> LS["localStorage<br/>theme · shortlist"]
    API -.->|"verified static data"| REG["Program registry"]

    subgraph DeployedUnit["One Vercel project"]
        UI
        API
        REG
    end
```

### Product hierarchy

```mermaid
flowchart TD
    ROOT["Contributor-first workspace"] --> D["Discover<br/>repositories · programs"]
    ROOT --> M["Match<br/>open issues to public evidence"]
    ROOT --> I["Inspect<br/>README · health · codebase · PR"]
    ROOT --> R["Report<br/>Markdown · JSON · CSV"]
    ROOT --> C["Collaborate<br/>browser-only shortlist"]
    ROOT --> A["Optional AI<br/>server-side key required"]
```

The original analyzer remains view **09**, with its scoring formula, charts, heatmap and theme persistence unchanged in behavior.

---

## 2. Container architecture

```mermaid
flowchart TB
    subgraph Browser["Browser"]
        HTML["index.html<br/>SPA shell + legacy markup"]
        CSS["style.css<br/>legacy design"]
        ACSS["assets/css/app.css<br/>workspace design system"]
        JS["assets/js/app.js<br/>hash router"]
        APIJS["assets/js/api.js<br/>same-origin client"]
        UIFS["assets/js/ui.js<br/>DOM builders"]
        VIEWS["assets/js/views/*.js<br/>8 controllers"]
        LEGACY["script.js<br/>legacy analyzer"]

        HTML --> CSS --> ACSS
        HTML --> LEGACY
        HTML --> JS --> VIEWS
        VIEWS --> UIFS
        VIEWS --> APIJS
    end

    subgraph Server["FastAPI application"]
        MAIN["main.py<br/>lifespan · CORS · handlers · static"]
        CORE["core/<br/>config · cache · validation · errors"]
        ROUTERS["routers/<br/>8 route groups"]
        SERVICES["services/<br/>GitHub client + 11 analyzers"]
        TESTS["tests/<br/>19 tests"]

        MAIN --> ROUTERS --> SERVICES
        SERVICES --> CORE
    end

    APIJS -->|"GET/POST /api/*"| MAIN
    LEGACY -->|"direct public API"| GH["GitHub"]

    SERVICES --> GH
    SERVICES -.-> AI["AI provider"]
```

| Layer | Modules | Responsibility |
| --- | --- | --- |
| Shell | `index.html`, `style.css`, `assets/css/app.css` | Navigation, view sections, visual system, legacy markup preservation |
| Browser logic | `assets/js/app.js`, `api.js`, `ui.js`, `views/*.js` | Routing, mounting, API access, rendering with DOM APIs |
| Legacy logic | `script.js` | Preserved analyzer, charts, heatmap, theme |
| HTTP | `backend/app/main.py` | ASGI app, middleware, exception handlers, static routes |
| Core | `backend/app/core/` | Settings, TTL cache, validators, structured errors |
| Routers | `backend/app/routers/` | Request parsing, orchestration, response shaping |
| Services | `backend/app/services/` | GitHub gateway and deterministic analysis engines |

---

## 3. Backend component map

```mermaid
flowchart TD
    subgraph Core["core"]
        CFG["config.py"]
        CACHE["cache.py<br/>TTLCache"]
        VAL["validation.py"]
        ERR["errors.py"]
    end

    subgraph Gateways["Gateway"]
        GH["github.py<br/>httpx · auth · rate limits"]
    end

    subgraph Intelligence["Intelligence"]
        DEV["developer.py"]
        SCORE["scoring.py"]
        ISS["issue_match.py"]
    end

    subgraph RepoTools["Repository lab"]
        READ["readme.py"]
        HEALTH["repo_health.py"]
        CODE["codebase.py"]
        PR["pr_guard.py"]
        DOC["docs.py"]
    end

    subgraph Other["Other"]
        PROG["programs.py"]
        AI["ai.py"]
        RPT["reports.py"]
    end

    GH --> DEV --> SCORE
    GH --> ISS
    GH --> READ
    GH --> HEALTH
    GH --> CODE
    GH --> PR
    GH --> DOC
    PROG --> CACHE
    AI --> CFG
    RPT --> VAL
    GH --> CACHE
```

### Service responsibilities

| Service | Input | Output | Deterministic? |
| --- | --- | --- | --- |
| `github.py` | Path + params | Raw GitHub JSON, mapped errors | Yes |
| `developer.py` | Username | Profile, stats, languages, scores, timeline, up to 30 summarized repos | Yes |
| `scoring.py` | Public metadata | Legacy 100-point score + five transparent score blocks | Yes |
| `issue_match.py` | Skill map + issues | Fit score, difficulty, evidence, starting guide | Yes |
| `readme.py` | README text + metadata | Findings, score, before/after Markdown | Yes |
| `repo_health.py` | Bounded file set | Docs, legal, security, quality, activity findings | Yes |
| `codebase.py` | Bounded source files | Extensions, entrypoints, routes, local imports, evidence lines | Yes |
| `pr_guard.py` | PR diff metadata | Confirmed findings separated from hypotheses | Yes |
| `docs.py` | Repository context | Four documentation drafts | Yes |
| `programs.py` | Static registry + filters | Eight verified program records | Yes |
| `ai.py` | Prompt + context | Provider text, usage, disclaimer | No — optional |
| `reports.py` | Caller payload | JSON, flattened CSV or Markdown | Yes |

---

## 4. API contract

All functional routes are under `/api`. Interactive documentation is intentionally under the same prefix so it cannot collide with the repository's physical `docs/` directory.

| Group | Endpoints | Count |
| --- | --- | --- |
| System | `GET /api/health`, `GET /api/cache`, `DELETE /api/cache` | 3 |
| Profile | `GET /api/profile/{username}` | 1 |
| Discovery | `GET /api/repos/search`, `GET /api/repos/rescue`, `GET /api/repos/{owner}/{repo}`, `GET /api/developers/search` | 4 |
| Issues | `GET /api/issues/search`, `GET /api/issues/{owner}/{repo}/{number}`, `POST /api/issues/match` | 3 |
| Programs | `GET /api/programs` | 1 |
| Repository Lab | `POST /api/repository/{readme,health,xray,pr-guard,docs-generate}` | 5 |
| AI | `GET /api/ai/status`, `POST /api/ai/complete` | 2 |
| Reports | `POST /api/reports/export` | 1 |
| Docs/static | `/api/docs`, `/api/redoc`, `/api/openapi.json`, `/`, `/style.css`, `/script.js`, `/assets/*`, `/docs-static/*` | platform |

Full parameter and response details: [`../product/API_REFERENCE.md`](../product/API_REFERENCE.md).

---

## 5. View-to-API map

```mermaid
flowchart LR
    OV["01 Overview"] --> H["/api/health"]
    OV --> P["/api/programs"]
    EX["02 Explore"] --> RS["/api/repos/search"]
    CO["03 Contributions"] --> IM["/api/issues/match"]
    PR["04 Programs"] --> P
    DV["05 Developer DNA"] --> PF["/api/profile/{username}"]
    RL["06 Repository Lab"] --> RT["/api/repository/*"]
    AI["07 AI Lab"] --> AS["/api/ai/status"]
    AI --> AC["/api/ai/complete"]
    CB["08 Collab Hub"] --> LS["localStorage"]
    PA["09 Profile Analyzer"] --> GH["api.github.com"]
```

| View | Mount behavior | Data source |
| --- | --- | --- |
| Overview | Mounted once | Health + program count |
| Explore | Form submit | Repository search with `perPage=12` |
| Contributions | Form submit | Issue match with default limit 8 |
| Programs | Mount, refresh, debounced filters | Program registry |
| Developer DNA | Form submit | Developer intelligence |
| Repository Lab | Form submit / tool buttons | Five repository endpoints |
| AI Lab | Mount + submit | AI status and completion |
| Collab Hub | Form submit / remove | Browser storage only |
| Profile Analyzer | Legacy script | Public GitHub API and third-party heatmap images |

API-only endpoints have no sidebar view: cache inspection, repository rescue, direct repository detail, developer search, issue search and issue detail.

---

## 6. Core data flows

### Discovery

```mermaid
sequenceDiagram
    participant U as User
    participant V as Explore view
    participant B as FastAPI router
    participant G as GitHubClient
    participant C as TTLCache
    participant H as GitHub

    U->>V: keywords + filters
    V->>B: GET /api/repos/search
    B->>B: clamp q, validate page/perPage, whitelist sort
    B->>G: search_repositories(query)
    G->>C: get(cache key)
    alt hit
        C-->>G: cached payload
    else miss
        G->>H: GET /search/repositories
        H-->>G: items + rate-limit headers
        G->>C: set(key, payload, 300s)
    end
    G-->>B: items
    B->>B: map activityLevel, indicators, topics, contributionAvailable
    B-->>V: normalized results + catalogs
```

### Contribution matching

```mermaid
sequenceDiagram
    participant U as User
    participant M as Match view
    participant R as issues router
    participant S as issue_match service
    participant G as GitHubClient
    participant H as GitHub

    U->>M: username + optional technologies
    M->>R: POST /api/issues/match
    R->>G: user + repos + languages
    G-->>R: public skill evidence
    R->>G: search issues (180s cache)
    G->>H: issue search
    H-->>G: candidates
    loop each candidate, bounded
        R->>G: get_issue(cache=False)
        G->>H: fresh issue detail
        H-->>G: current state
        alt closed, assigned or PR
            R->>R: skip
        else open issue
            R->>S: score fit + complexity
        end
    end
    R-->>M: matches, skipped counts, evidence, disclaimer
```

### Repository Lab

```mermaid
flowchart TD
    IN["owner/repo or GitHub URL"] --> VAL["parse_repo<br/>host + traversal guard"]
    VAL --> META["fetch repository metadata"]
    META --> TREE["default-branch tree, else HEAD"]
    TREE --> FILTER["blob ≤200,000 bytes"]
    FILTER --> RANK["rank manifests → source → short paths"]
    RANK --> TOOL{"selected tool"}
    TOOL --> RDM["README Doctor"]
    TOOL --> HLTH["Health check (≤12 files)"]
    TOOL --> XRAY["X-Ray (≤24 files)"]
    TOOL --> PRG["PR Guardian"]
    TOOL --> DOC["Docs draft (≤20 files)"]
    RDM --> OUT["findings + drafts + limitations"]
    HLTH --> OUT
    XRAY --> OUT
    PRG --> OUT
    DOC --> OUT
```

---

## 7. Caching and rate limits

```mermaid
flowchart LR
    REQ["GET request"] --> KEY["key = github:{path}:{sorted params}"]
    KEY --> LOOK{"TTLCache.get()"}
    LOOK -->|hit| RET["return cached JSON"]
    LOOK -->|miss| HTTP["httpx call"]
    HTTP --> RH{"GitHub response"}
    RH -->|"200"| STORE["set with TTL"]
    RH -->|"403/429 remaining=0"| E429["HTTP 429 upstream_error"]
    RH -->|"404"| E404["HTTP 404 not_found"]
    RH -->|"≥500 or invalid JSON"| E502["HTTP 502 upstream_error"]
    STORE --> RET
```

| Operation class | TTL |
| --- | --- |
| Profile, repository, language, tree, contents, README, PR | 900s default |
| Repository search, user search | 300s |
| Issue search | 180s |
| Issue detail used for revalidation | no cache |
| Rate-limit endpoint | no cache |

Cache properties:

- Bounded by `CACHE_MAX_ENTRIES` (default 300).
- Thread-safe with lazy expiry and monotonic time.
- Evicts stale entries first, then insertion-order entries.
- Process-local: Vercel instances do not share cache state.
- `GET /api/cache` reports `entries`, `maxEntries`, `hits`, `misses`, `ttlSeconds`.

---

## 8. Error model

```mermaid
flowchart TD
    E["Exception"] --> T{"type"}
    T -->|AppError| A["status + structured error object"]
    T -->|RequestValidationError| V["422 invalid_request + detail"]
    T -->|unexpected| U["500 internal_error<br/>details logged only"]
    A --> C["Browser api.js extracts error.message"]
    V --> C
    U --> C
```

Standard shape:

```json
{
  "error": {
    "code": "upstream_error",
    "message": "GitHub rate limit exhausted.",
    "detail": { "rateLimitRemaining": 0, "rateLimitReset": "..." }
  }
}
```

Two endpoints intentionally return an in-body `error` object with HTTP 200: invalid program status, and a PR number passed to the issue-detail route. Clients must check both `response.ok` and `data.error`.

---

## 9. Design principles

1. **No fabricated data.** Live data is fetched; registry data is source-linked; missing values stay `null`.
2. **Deterministic first.** Every core tool works without AI. AI is an optional enhancement, never a fact source.
3. **Secrets stay server-side.** Only boolean integration status reaches the browser.
4. **Repository content is data.** No execution, no shell calls, bounded file count and size.
5. **Graceful degradation.** The legacy analyzer still works against public GitHub if the backend is unavailable; workspace views show setup guidance instead of fake content.
6. **Honest labels.** Scores are heuristics, activity is inferred from push dates, and "rescue" results never claim a project is abandoned.

---

## 10. Non-goals for this release

| Non-goal | Current substitute |
| --- | --- |
| Persistent accounts and database | GitHub source of truth + process-local cache |
| OAuth and GitHub writes | Read-only endpoints; `writeAction.enabled: false` |
| Redis / shared cache | Bounded in-memory TTLCache |
| Background jobs | Synchronous bounded analysis |
| Real-time notifications | Not implemented |
| PDF generation | Browser print dialog |
| Full static-analysis engine | Representative file sampling with explicit limits |

Deployment mechanics are documented in [`../operations/DEPLOYMENT.md`](../operations/DEPLOYMENT.md); browser internals in [`frontend-architecture.md`](frontend-architecture.md).
