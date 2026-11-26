# Feature Status

Classification rules:

- **Implemented** — code exists, was executed, and its behaviour was verified in this repository.
- **Partially Implemented** — some working code exists, but a dependency, credential or external
  verification step prevents full functionality.
- **Experimental** — works for limited inputs and may change; not guaranteed for production data.
- **Planned** — design is documented; no working implementation exists yet.

Last updated: after Phase 2 (backend) verification.

| Feature | Status | Evidence / limitation |
| --- | --- | --- |
| Legacy GitHub profile analyzer (scores, charts, heatmap, theme) | Implemented (pre-existing) | `script.js`, `index.html`; preserved unchanged so far |
| FastAPI backend, OpenAPI docs and health endpoint | Implemented | 19 pytest tests pass; live server verified 2026-11-26 |
| GitHub API proxy with token/rate-limit handling | Implemented | `backend/app/services/github.py`; 403/429 mapping tested; unauthenticated mode verified live |
| Developer DNA, skill map, timeline, five transparent scores | Implemented | `/api/profile/{username}` verified live against `octocat` |
| Original 100-point score preserved | Implemented | `compute_legacy_score` mirrors `script.js`; unit tested |
| Open Source Explorer (real search, filters, pagination) | Implemented | `/api/repos/search` verified live with real GitHub results |
| Contribution matching with issue revalidation | Implemented | `/api/issues/match`; closed/stale issues are skipped and tested |
| Issue Intelligence (complexity, triage detail) | Implemented | `/api/issues/search`, `/api/issues/{owner}/{repo}/{number}` |
| Open Source Programs registry | Implemented | 8 records; official URLs and verification sources; no invented deadlines |
| README Doctor (deterministic analysis and suggestion) | Implemented | `/api/repository/readme`; score, findings, before/after, download data |
| AI-improved README wording | Partially Implemented | Deterministic improved draft works; LLM rewriting requires `OPENAI_API_KEY` |
| Repository health, dependency parsing, security-policy checks | Implemented | Versions parsed locally; no vulnerability DB query is claimed |
| Codebase X-Ray static analysis and evidence search | Implemented | `/api/repository/xray`; no code execution, no invented architecture |
| Pull Request Guardian static analysis | Implemented | `/api/repository/pr-guard`; confirmed findings separated from hypotheses |
| Documentation generators | Implemented | CONTRIBUTING / CODE_OF_CONDUCT / SECURITY / ARCHITECTURE drafts |
| Project Rescue signals | Implemented | `/api/repos/rescue`; explicitly not labelling projects abandoned |
| Developer discovery via GitHub user search | Implemented | `/api/developers/search` |
| Dashboard shell, navigation and all views | Planned | Phase 3/4 |
| Collaboration Hub local listings | Planned | Phase 4 |
| Roadmap and career view | Planned | frontend phase; backend data already available |
| AI Developer Lab LLM helpers | Partially Implemented | Backend endpoint and status work; returns 503 with setup guidance without a key |
| Reports & exports (JSON/CSV/Markdown) | Implemented (API) | `/api/reports/export`; browser download UI pending |
| PDF export | Planned | browser print dialog will be used instead of a fake generator |
| PostgreSQL database and migrations | Planned | no database in first release by design |
| Redis cache | Planned | bounded in-memory TTL cache implemented instead |
| GitHub OAuth and repository write actions | Planned | explicit authorization required; write endpoints remain disabled |
| Background job queue | Planned | synchronous bounded analysis used instead |
| Automated test suite | Implemented | 19 tests executed, all passed (`python -m pytest -q`) |
