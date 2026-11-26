# Feature Status

Classification rules:

- **Implemented** — code exists, was executed, and its behaviour was verified in this repository.
- **Partially Implemented** — some working code exists, but a dependency, credential or external
  verification step prevents full functionality.
- **Experimental** — works for limited inputs and may change; not guaranteed for production data.
- **Planned** — design is documented; no working implementation exists yet.

This file is updated at the end of every implementation phase.

| Feature | Status | Evidence / limitation |
| --- | --- | --- |
| Legacy GitHub profile analyzer (scores, charts, heatmap, theme) | Implemented (pre-existing) | `script.js`, `index.html`; preserved by the dashboard shell |
| FastAPI backend and health endpoint | Planned | Phase 2 |
| GitHub API proxy with token/rate-limit handling | Planned | Phase 2 |
| Developer DNA, skill map, five transparent scores | Planned | Phase 2/4 |
| Open Source Explorer (real search, filters, pagination) | Planned | Phase 2/4 |
| Contribution discovery and issue matching | Planned | Phase 2/4 |
| Issue Intelligence | Planned | Phase 2/4 |
| Open Source Programs registry | Planned | Phase 2/4 |
| README Doctor (deterministic, before/after, download) | Planned | Phase 2/4 |
| Repository health and dependency/security checks | Planned | Phase 2/4 |
| Codebase X-Ray static analysis | Planned | Phase 2/4 |
| Pull Request Guardian static analysis | Planned | Phase 2/4 |
| Documentation generators | Planned | Phase 2/4 |
| Project Rescue signals | Planned | Phase 4 |
| Developer discovery and Collaboration Hub (local) | Planned | Phase 4 |
| Roadmap / career intelligence | Planned | Phase 4 |
| AI Developer Lab (LLM helpers) | Planned (requires server key) | Phase 2/4 |
| Reports & exports (JSON/CSV/Markdown) | Planned | Phase 2/4 |
| PDF export | Planned | browser print dialog used instead of a fake generator |
| PostgreSQL database and migrations | Planned | no database in first release by design |
| Redis cache | Planned | bounded in-memory TTL cache implemented instead |
| GitHub OAuth and repository write actions | Planned | explicit authorization required |
| Background job queue | Planned | synchronous bounded analysis used instead |
| Automated test suite | Planned | Phase 2/6 |
