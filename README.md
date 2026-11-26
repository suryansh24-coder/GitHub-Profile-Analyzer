# README

DevAtlas is a contributor-first open-source workspace built around a FastAPI backend and a browser dashboard. It keeps the original GitHub Profile Analyzer intact while adding live repository discovery, contribution matching, verified program data, developer intelligence and static repository analysis.

## What is real

- All profile, repository, issue and pull-request data comes from the GitHub REST API at request time.
- Program dates come from official sources and are marked `null` when unpublished.
- Scores are deterministic heuristics based on public repository metadata, not claims of engineering ability.
- Repository tools are read-only. No code is executed and no GitHub write action runs without explicit OAuth authorization.
- AI helpers require `OPENAI_API_KEY` on the backend. Without it, deterministic tools still work and the UI shows setup guidance.

## Run locally

```bash
python -m pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

Open `http://127.0.0.1:8000`.

Optional backend environment variables are documented in `.env.example`. Set `GITHUB_TOKEN` to raise the GitHub API limit from 60 to 5000 requests/hour. Never put tokens in frontend code.

## Run tests

```bash
cd backend
python -m pytest -q
```

All 19 tests passed at the last verification. Frontend modules were syntax-checked with `node --check --input-type=module`.

## Workspace views

| View | Purpose |
| --- | --- |
| Overview | Workspace entry point and live service status |
| Explore | Search real repositories with language, topic, star and activity filters |
| Contributions | Rank revalidated open issues against your public skill evidence |
| Programs | Verified timelines for open-source programs |
| Developer DNA | Five transparent scores, skill evidence and public history timeline |
| Repository Lab | README Doctor, health checks, static X-Ray, PR Guardian and doc drafts |
| AI Lab | Optional backend-proxied AI guidance with clear setup state |
| Collab Hub | Locally saved links; nothing is invented or shared |
| Profile Analyzer | The preserved original analyzer with charts and heatmap |

## API

The OpenAPI schema is available at `/docs`. Main route groups:

- `/api/health`, `/api/cache`
- `/api/profile/{username}`
- `/api/repos/search`, `/api/repos/rescue`, `/api/repos/{owner}/{repo}`, `/api/developers/search`
- `/api/issues/search`, `/api/issues/match`, `/api/issues/{owner}/{repo}/{number}`
- `/api/programs`
- `/api/repository/readme`, `/health`, `/xray`, `/pr-guard`, `/docs-generate`
- `/api/ai/status`, `/api/ai/complete`
- `/api/reports/export`

## Architecture

- `index.html` — SPA shell plus the preserved legacy analyzer markup.
- `style.css`, `script.js` — original analyzer styling and logic, unchanged in behaviour.
- `assets/css/app.css` — workspace design system loaded after `style.css`.
- `assets/js/` — ES modules for API access, UI helpers and view controllers.
- `backend/app/core/` — configuration, cache, validation and error types.
- `backend/app/services/` — GitHub client, scoring and analysis services.
- `backend/app/routers/` — FastAPI route groups.
- `api/index.py`, `vercel.json` — serverless adapter and deployment configuration.

## Documentation

- `docs/product/PROJECT_AUDIT.md`
- `docs/product/IMPLEMENTATION_PLAN.md`
- `docs/product/FEATURE_STATUS.md`
- `docs/product/USER_GUIDE.md`
- `docs/architecture/SYSTEM_OVERVIEW.md`
- `docs/architecture/FRONTEND_ARCHITECTURE.md`
- `docs/architecture/DATABASE_SCHEMA.md`
- `docs/security/SECURITY.md`
- `docs/operations/DEPLOYMENT.md`
- `docs/testing/TEST_PLAN.md`
- `docs/research/PROGRAM_SOURCES.md`

## Checkpoints

- `68cc42a` — audit
- `20e40a3` — architecture and plan
- `545a40a` — backend services and tests
- `e3e6004` — ignore bytecode and local env files
- next checkpoint — workspace UI and deployment adapter

## Known limits

- No database in the first release; a bounded in-memory TTL cache is used.
- Private contributions, non-GitHub work and skills without public evidence are not represented.
- PDF export is intentionally not generated; use browser print or Markdown/JSON/CSV exports.
- GitHub write actions and background jobs are planned but not enabled.
