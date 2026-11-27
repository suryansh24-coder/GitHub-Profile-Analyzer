# User Guide

**Audience:** contributors, maintainers and open-source program applicants. Every screen shows live or source-linked data; nothing is seeded as a fake result.

---

## 1. The contributor journey

```mermaid
journey
    title From curiosity to a defensible first contribution
    section Discover
      Explore real repositories: 5: Contributor
      Check activity and open issues: 4: Contributor
    section Prepare
      Match skills to open issues: 5: Contributor
      Read README and health checks: 4: Contributor
      Inspect codebase and PR context: 3: Contributor
    section Act
      Decide with evidence: 5: Contributor
      Contribute on GitHub: 5: Contributor
    section Report
      Export Markdown / JSON / CSV: 4: Contributor
```

```mermaid
flowchart LR
    A["01 Overview"] --> B["02 Explore"]
    B --> C["03 Contributions"]
    C --> D["04 Programs"]
    C --> E["05 Developer DNA"]
    E --> F["06 Repository Lab"]
    F --> G["07 AI Lab"]
    C --> H["08 Collab Hub"]
    A --> I["09 Profile Analyzer"]
```

---

## 2. Start the application

### Deployed

Open the Vercel URL. No setup is required. The sidebar status dot turns green when `/api/health` responds.

### Local

```bash
python -m pip install -r requirements.txt
python -m pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

Open <http://127.0.0.1:8000>. If the backend is stopped, workspace views show an offline message; the preserved analyzer can still call public GitHub directly.

---

## 3. View reference

### 01 — Overview

| Element | Meaning |
| --- | --- |
| Verified programs | Count from the current program registry |
| API status | `Online` when `/api/health` succeeds |
| Release | Platform version marker |
| Capability cards | Shortcuts to Explore, Contributions, Programs, Developer DNA, Repository Lab and Collab Hub |

```mermaid
flowchart LR
    O["Overview mount"] --> H["GET /api/health"]
    O --> P["GET /api/programs"]
    H --> S["status dot + GitHub mode"]
    P --> N["verified program count"]
```

---

### 02 — Explore

Enter keywords and optional filters. The backend builds a GitHub query with `archived:false`.

| Field | Behavior |
| --- | --- |
| Keywords | Free text, truncated to 200 characters |
| Language | GitHub `language:` qualifier |
| Category | One of 16 backend categories, mapped to GitHub topics |
| Minimum stars | `stars:>=N` from 0 to 1,000,000 |
| Sort | `stars`, `updated` or `forks`; invalid values fall back to `stars` |
| Results | 12 repositories per search by default |

```mermaid
flowchart TD
    F["Form submit"] --> Q["build query<br/>keywords + qualifiers"]
    Q --> G["GET /api/repos/search"]
    G --> M["map each repository"]
    M --> A["activityLevel<br/>active ≤30d · moderate ≤180d<br/>low ≤365d · inactive >365d"]
    M --> I["healthIndicators<br/>stars · issues · license · pushes"]
    M --> C["contributionAvailable<br/>openIssues > 0"]
    A --> R["Result card"]
    I --> R
    C --> R
```

Opening a result in Repository Lab carries `owner/repo` forward. Activity labels are metadata signals, not abandonment claims.

---

### 03 — Contributions

```mermaid
sequenceDiagram
    participant U as You
    participant M as Contribution Matcher
    participant B as Backend
    participant G as GitHub

    U->>M: username + optional technologies
    M->>B: POST /api/issues/match
    B->>G: profile, repos, languages
    G-->>B: public skill evidence
    B->>G: search open issues
    G-->>B: candidates
    loop bounded candidates
        B->>G: re-fetch issue without cache
        alt closed / assigned / PR
            B->>B: skip
        else still open
            B->>B: score fit + complexity
        end
    end
    B-->>M: ranked matches + evidence
    M-->>U: score, difficulty, reason, starting guide
```

| Input | Limit |
| --- | --- |
| Username | 1–100 characters |
| Extra technologies | Free text appended to the skill query |
| Maximum matches | UI 1–20; API accepts 1–25 |

Match results include candidate count, revalidated count, skipped count, top skill evidence, fit score, difficulty, and a suggested first step. **Nothing is reserved for you.** Maintainers may close or assign an issue at any time; re-check before starting work.

---

### 04 — Programs

Filter by text, status, beginner friendliness and mentorship. Search is debounced by 250 ms.

| Status | Meaning |
| --- | --- |
| `upcoming` | Announced future cycle |
| `applications_open` | Accepting applications at verification time |
| `applications_closed` | Window closed |
| `ongoing` | Program in progress |
| `completed` | Cycle concluded |
| `status_unverified` | Official current-cycle dates could not be verified |

Unpublished deadlines display as **not published**. Each card links to the official site and verification source. See [`../research/PROGRAM_SOURCES.md`](../research/PROGRAM_SOURCES.md) for all eight records.

---

### 05 — Developer DNA

Enter a GitHub username to build an evidence-based profile.

```mermaid
flowchart TD
    U["username"] --> P["profile + repositories"]
    P --> L["language bytes from top non-fork repos"]
    L --> S1["Activity score"]
    L --> S2["Portfolio quality"]
    L --> S3["Technical diversity"]
    P --> S4["Open-source engagement"]
    P --> S5["Career readiness"]
    S1 --> O["Five score tiles"]
    S2 --> O
    S3 --> O
    S4 --> O
    S5 --> O
    P --> T["Growth timeline<br/>repo years + technology adoption"]
    P --> K["Skill map from public evidence"]
```

The skill map uses public evidence only. Absence of evidence is not treated as lack of skill. Scores are transparent heuristics, not an assessment of engineering ability.

---

### 06 — Repository Lab

Enter `owner/repo` or a GitHub URL, then select a tool.

```mermaid
flowchart LR
    R["Repository input"] --> T1["README Doctor"]
    R --> T2["Health Check"]
    R --> T3["Codebase X-Ray"]
    R --> T4["PR Guardian"]
    R --> T5["Docs Drafts"]

    T1 --> O1["findings + before/after README"]
    T2 --> O2["docs · legal · security · quality · activity"]
    T3 --> O3["structure · entrypoints · routes · evidence lines"]
    T4 --> O4["confirmed findings vs hypotheses"]
    T5 --> O5["CONTRIBUTING / CODE_OF_CONDUCT / SECURITY / ARCHITECTURE"]
```

| Tool | What it checks | What it does not do |
| --- | --- | --- |
| README Doctor | Headings, installation, usage, screenshots, fences, links, badges, stale terms | Does not write to GitHub |
| Health Check | README, contributing guide, license, security policy, tests, CI, manifests, maintenance signals | Does not query a vulnerability database |
| Codebase X-Ray | Bounded file sample, extensions, directories, entrypoints, imports, routes, keywords | Does not execute code or generate a full architecture claim |
| PR Guardian | Missing tests, docs changes, possible breaking edits, TODO/FIXME, diff size, issue references, duplicate PR titles | Does not approve or merge anything |
| Docs Drafts | Four Markdown templates using repository context | Does not open pull requests |

Large repositories are sampled under explicit limits: 12 files for health, 24 for X-Ray, 20 for architecture drafts. Findings are evidence, not verdicts.

---

### 07 — AI Lab

The status panel reports whether the backend has `OPENAI_API_KEY`. Without it, requests return `503 ai_not_configured` and the UI shows setup guidance. No key reaches the browser.

AI output is labelled for critical review. Use it to draft wording or questions, not as a source of repository facts.

---

### 08 — Collab Hub

| Behavior | Detail |
| --- | --- |
| Storage key | `devatlas.collab.entries` |
| Capacity | 100 entries |
| Sync | None — current browser only |
| Seeding | None |
| URL validation | `http:` or `https:` only |
| Remove | Deletes one entry immediately |

Use this as a personal shortlist. It is not a shared marketplace or applicant directory.

---

### 09 — Profile Analyzer

The original analyzer is preserved. Enter a username or profile URL to see:

- profile overview and repository statistics;
- language distribution and the original 100-point normalized score;
- insight strip and eight deep-analysis observations;
- top repository table, two Chart.js charts and contribution heatmap;
- dark/light theme persisted under `theme`.

The legacy analyzer calls public GitHub directly and third-party image services for heatmaps. It does not use the FastAPI cache.

---

## 4. Exports

```mermaid
flowchart TD
    R["Result card"] --> MD["Markdown button<br/>UI download"]
    R --> API["POST /api/reports/export"]
    API --> J["JSON"]
    API --> C["CSV"]
    API --> M["Markdown"]
    M --> B["Blob download in browser"]
```

- Markdown buttons appear on supported result cards; not every card has one.
- JSON and CSV are API formats; call `/api/reports/export` or use `/api/docs`.
- For PDF, use your browser's print dialog. There is no fake PDF generator.

---

## 5. Understanding freshness

| Data | Freshness |
| --- | --- |
| Most GitHub GETs | Cached up to 900 seconds per function instance |
| Repository/user search | Cached up to 300 seconds |
| Issue search | Cached up to 180 seconds |
| Issue revalidation in matching | Fresh request, deliberately uncached |
| Programs | Verified snapshot dated `2026-11-26` |
| Collab Hub | Whatever your browser has stored |

If a result looks stale, wait for TTL expiry or call `DELETE /api/cache` if you have API access.

---

## 6. Troubleshooting

| Symptom | Meaning | Action |
| --- | --- | --- |
| Sidebar says **Offline** | `/api/health` unreachable | Check deployment logs or start local backend |
| `GitHub public mode` | No `GITHUB_TOKEN` | Set the backend secret to raise the 60/hour limit |
| HTTP 429 | GitHub rate limit exhausted | Wait for reset or configure a token |
| AI Lab says not configured | No backend key | Set `OPENAI_API_KEY`, or ignore AI features |
| Program deadline says not published | Source did not publish a date | Check the official site; do not guess |
| Charts have zero width | Legacy view was hidden during creation | Navigate away and back; resize is scheduled automatically |
| Empty Explore result | Filters too narrow or category mismatch | Remove filters; use one of the 16 supported categories |
| Repository Lab says invalid repository | Non-GitHub host or unsafe path | Use `owner/repo` or a GitHub URL |
