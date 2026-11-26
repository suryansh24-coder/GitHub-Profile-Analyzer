# Project Audit — GitHub Profile Analyzer

**Audit date:** 2026-11-26
**Branch before changes:** `main` (HEAD `50951bc`)
**Development branch:** `feat/developer-ecosystem`
**Auditor:** automated repository inspection (all source files read in full)

This document records the state of the project before the platform transformation. Every claim below is
based on files present in this repository at the audited commit.

---

## 1. Repository inventory

| Path | Lines / size | Role |
| --- | --- | --- |
| `index.html` | 270 lines | Single static HTML document; header, search form, analyzer dashboard markup |
| `script.js` | 713 lines | All application logic, scoring, API calls, chart rendering, theme switching |
| `style.css` | 645 lines / 24 KB | All styling, CSS variables, dark/light themes, responsive rules |
| `README.md` | 164 lines | Project overview and usage instructions (partly outdated) |

There is **no** build system, package manifest, backend, test suite, database, CI configuration,
`vercel.json`, or environment-variable template. The application is a fully static site that can be
opened directly from `index.html` or served by any static host (the existing Vercel deployment works
because of that).

## 2. Existing architecture and data flow

1. The user types a username or a `github.com/...` URL into `#github-input`.
2. `script.js` parses the username from the input.
3. Two parallel requests are made directly from the browser:
   - `GET https://api.github.com/users/{username}`
   - `GET https://api.github.com/users/{username}/repos?per_page=100&sort=updated`
4. For the 12 most-starred non-fork repositories, `GET /repos/{owner}/{repo}/languages` is called.
5. A 100-point score is computed and rendered with Chart.js doughnut/bar charts.
6. A contribution heatmap is loaded from the third-party image services `ghchart.rshah.org` and
   `streak-stats.demolab.com` (with a fallback link when both fail).
7. Theme choice is persisted in `localStorage` under the key `theme`.

## 3. Working features inventory

| Feature | Implementation | Status |
| --- | --- | --- |
| GitHub username / URL parsing | `script.js:94-111` | Working |
| Profile overview (avatar, name, bio, followers, following, repos, joined, location, company) | `script.js:307-328` | Working |
| Repository statistics (total, stars, forks, original vs forks, most starred, most recent) | `script.js:499-521` | Working |
| Language distribution from real `/languages` endpoints with fallback | `script.js:135-161`, `530-581` | Working |
| Transparent normalized 0–100 score with five explained components | `script.js:202-242` | Working |
| Insight strip (years active, avg stars, originals, language count) | `script.js:245-304`, `340-345` | Working |
| Deep-analysis cards (8 evidence-based observations) | `script.js:377-471` | Working |
| Top repositories table (15 rows, links to GitHub) | `script.js:473-496` | Working |
| Repository popularity bar chart | `script.js:583-633` | Working |
| Contribution activity image with two sources and graceful failure | `script.js:643-707` | Working |
| Dark/light theme with persistence | `script.js:65-91`, `style.css:4-43` | Working |
| Loading, empty and error states for profile analysis | `index.html:57-69`, `script.js:709-713` | Working |
| Responsive layouts (900 / 700 / 480 px breakpoints) | `style.css:629-645` | Working |

## 4. Feature preservation checklist (must remain functional)

- [x] Entering a GitHub username or profile URL must still produce the same analyzer dashboard.
- [x] The existing 100-point score formula and its five component rows must be preserved exactly.
- [x] The existing insight strip, deep-analysis cards, repository table and both Chart.js charts must
      remain available with the same semantics.
- [x] The contribution heatmap with its primary/fallback sources must remain available.
- [x] Dark/light theme switch and `localStorage` persistence must continue to work.
- [x] Public GitHub REST API integration must continue to work with no token configured.
- [x] Static deployment compatibility (no required build step for the browser entry point) must be kept.
- [x] Legacy `#search-form`, `#github-input`, `#analyze-btn`, `#dashboard` element IDs must remain
      present wherever the legacy analyzer markup is rendered, so `script.js` keeps working.
- [x] Backward compatibility: `index.html` at the repository root must remain the site entry point.

## 5. Dependencies and integrations

- Runtime (browser): Chart.js 4.x via jsDelivr CDN, Google Fonts (Inter + Space Grotesk).
- GitHub REST API: unauthenticated (60 requests/hour per IP).
- Third-party contribution images: `ghchart.rshah.org`, `streak-stats.demolab.com`.
- No AI provider, authentication provider, or database is currently integrated.

## 6. Identified issues and risks

| ID | Severity | Finding | Evidence |
| --- | --- | --- | --- |
| A-01 | Medium | README documents an outdated scoring formula (`Stars×2 + Repos×3 + Followers×1`) that does not match the implemented normalized score. | `README.md:60-69` vs `script.js:202-242` |
| A-02 | Medium | Unauthenticated GitHub API is limited to 60 requests/hour; one profile analysis can use 15+ requests, so rate-limit exhaustion is likely in a shared deployment. | `script.js:120-152` |
| A-03 | Medium | No server-side cache; identical analyses repeat all requests. | `script.js:114-186` |
| A-04 | Medium | Profile data is interpolated through `innerHTML` in the table and analysis grid without explicit escaping. GitHub normalizes most fields, but defensive escaping is needed for untrusted repository metadata. | `script.js:461-470`, `486-493` |
| A-05 | Low | `avgStars` divides total stars (including forks) by the count of original repositories only, so the displayed average can be inflated. | `script.js:251-253` |
| A-06 | Low | Language fetch failures are silently swallowed; users are not told that the chart used the fallback field. | `script.js:142-161` |
| A-07 | Low | Third-party image services receive the analyzed username; no privacy notice exists. | `script.js:670-706` |
| A-08 | Low | No automated tests exist, so regressions cannot be detected. | repository inventory |
| A-09 | Low | No `vercel.json`, but static hosting works via zero-config detection. | repository inventory |

## 7. Baseline verification

- Python 3.14.6, Node 24.18.0, npm 11.16.0 available.
- `fastapi`, `uvicorn`, `pytest`, `httpx` already installed in the environment.
- Live check: `GET https://api.github.com/users/octocat` returned HTTP 200 — network access to the
  GitHub REST API is available from this environment.
- No baseline test suite exists; therefore there is no test result to preserve. A new suite is added in
  Phase 2 and executed in Phase 6.

## 8. Recovery state

- `main` remains untouched at `50951bc`.
- All transformation work happens on `feat/developer-ecosystem`.
- A checkpoint commit is created after each completed phase.
