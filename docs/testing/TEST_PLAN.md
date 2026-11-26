# Test Plan

## Automated tests already executed

Command:

```bash
cd backend
python -m pytest -q
```

Result: `19 passed`.

Coverage:

- Health, profile, repository search, issue matching, README Doctor, programs, AI-disabled state and validation errors.
- GitHub 403 rate-limit mapping to HTTP 429.
- Username and repository URL validation, including SSRF host and traversal rejection.
- TTL cache expiry and statistics.
- Legacy score formula equivalence with the original JavaScript implementation.
- README findings, issue complexity, codebase evidence, PR Guardian findings, docs generation and report exports.

## Frontend checks already executed

- HTML tag balance checked with Python `html.parser`; no unclosed or mismatched tags.
- All 11 ES modules checked with `node --check --input-type=module`.
- FastAPI served `/`, `/style.css`, `/script.js`, `/assets/css/app.css`, `/assets/js/app.js` and `/assets/js/views/repository.js` with HTTP 200.
- Live backend verified with real GitHub data for `/api/health`, `/api/programs`, `/api/profile/octocat` and `/api/repos/search`.
- Headless Chromium DOM verified that `app.js` executes: overview shows `Online`, the sidebar reports GitHub public mode, `#programs` renders eight verified program cards, and `#analyzer` activates the preserved analyzer view with its original IDs.
- A headless screenshot was generated successfully; visual inspection by this model was unavailable because image input is not supported.

## Manual verification checklist

- Navigate through all sidebar views and confirm the view label and hash update.
- Confirm the Profile Analyzer still analyses a username and charts render after the view becomes visible.
- Confirm theme toggle persists across reloads.
- Confirm Collab Hub entries survive reload and Remove works.
- Confirm API-offline message appears when the backend is stopped.
- Confirm program deadlines are never shown as invented values.
- Confirm README Doctor and write-action message state that no GitHub write occurred.

## Not yet verified

- Browser automation with Playwright/jsdom was unavailable in this environment.
- Vercel deployment has not been executed against a live project.
- AI provider responses have not been tested because no key is configured.
- OAuth and GitHub write flows are intentionally not implemented.
