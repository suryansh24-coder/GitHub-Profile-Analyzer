# User Guide

## Start the application

```bash
python -m pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

Open `http://127.0.0.1:8000`. The sidebar status dot shows whether the backend is reachable.

## Overview

The overview explains the contributor workflow and shows live API state and the number of verified programs. Every capability card opens its workspace view.

## Explore

Enter keywords and optional language, category and minimum stars. The backend builds a GitHub search query with `archived:false`, returns mapped repository metadata and labels activity from push dates. "Open in Repository Lab" carries the selected repository into the analysis view.

## Contributions

Enter a GitHub username and optional technologies. The backend builds a skill map from public repositories, searches open issues, then re-fetches candidates and skips closed, assigned or invalid issues. Results show a match score, difficulty, evidence and a starting guide. Nothing is reserved for you.

## Programs

Filter by status, search text, beginner friendliness or mentorship. Missing deadlines are shown as "not published". Every card links to the official site and to the source used for verification.

## Developer DNA

Build a report from a username. Five scores are shown with names and caveats: activity, portfolio quality, technical diversity, open-source engagement and career readiness. The skill map only uses public evidence; absence of evidence is not treated as lack of skill. The roadmap section shows repository creation years and first observed technology use from public metadata.

## Repository Lab

Enter `owner/repo` or a GitHub URL, then choose:

- **README Doctor** — deterministic findings plus a before/after draft. Nothing is written to GitHub.
- **Health Check** — documentation, legal, security, quality and activity checks; manifest versions are parsed but no advisory database is queried.
- **Codebase X-Ray** — static analysis of a bounded set of source files, with optional evidence search.
- **PR Guardian** — provide a pull request number or URL; findings are separated from hypotheses.
- **Docs Drafts** — choose a document kind and review the generated draft before use.

## AI Lab

The status panel states whether AI is enabled. Without `OPENAI_API_KEY` on the backend, requests return a clear 503 and no key is exposed to the browser.

## Collab Hub

Saved entries are stored in this browser's `localStorage`. The app does not seed fake listings or sync entries anywhere. Use Remove to delete an entry.

## Profile Analyzer

The original analyzer is preserved. Enter a username or profile URL and use the legacy charts, score breakdown, insights and contribution heatmap. Theme preference is stored in `localStorage` under `theme`.

## Exports

Markdown export is available from result cards. JSON and CSV formats are supported by the API and can be called through `/docs`. Use your browser's print dialog for PDF output.
