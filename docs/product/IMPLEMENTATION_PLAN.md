# Implementation Plan

This plan replaces uncontrolled "build everything at once" with verified milestones. Each phase ends
with a test run and a git checkpoint on `feat/developer-ecosystem`.

| Phase | Scope | Exit criteria | Status |
| --- | --- | --- | --- |
| 0 — Audit | Read all files, inventory features, preserve checklist, recovery branch | `PROJECT_AUDIT.md`, branch created | Complete |
| 1 — Architecture | Modules, API contracts, design system, honest status file | `SYSTEM_OVERVIEW.md`, `FEATURE_STATUS.md` | Complete |
| 2 — Backend | FastAPI app, GitHub client, TTL cache, deterministic analyzers, tests | pytest suite passes; `/docs` and `/api/health` work | In progress |
| 3 — Dashboard shell | Sidebar, topbar, hash router, premium CSS, legacy analyzer preserved | Every nav item renders a view; legacy analyzer still analyses profiles | Pending |
| 4 — Ecosystem modules | Explorer, contributions, issues, programs, doctor, X-Ray, PR Guardian, community, growth, reports | Each view performs real requests and shows real states | Pending |
| 5 — Documentation | Full docs tree, root README, status updates | All docs match implemented code | Pending |
| 6 — Quality | Tests, build/import checks, console check, responsive review, deployment guide | Suite passes; status file reflects verified results | Pending |

## Scope policy

The master prompt contains more than a hundred feature bullets. To keep engineering quality high, the
first release implements a coherent vertical slice: every sidebar item is a working view, but depth is
prioritised as follows.

**Deep implementation:** developer intelligence preservation, repository search, contribution matching
on real open issues, README doctor, repository health, program registry, deterministic exports.

**Functional implementation:** issue intelligence, codebase X-Ray static analysis, PR Guardian static
analysis, documentation generators, developer discovery, local collaboration hub, roadmap, reports.

**Structure only, explicitly marked:** LLM-dependent tools (require `OPENAI_API_KEY`), GitHub write
actions (require OAuth and explicit authorization), PostgreSQL persistence, Redis cache, background job
queue, real-time notifications. These are documented as Planned/Experimental rather than presented as
finished features.

## Checkpoints

- `68cc42a` — audit and preservation checklist
- subsequent commits are created after each phase with concise messages
- `main` is never rewritten or force-pushed
