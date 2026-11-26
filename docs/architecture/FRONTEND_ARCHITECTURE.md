# Frontend Architecture

## Principles

- The legacy analyzer is preserved, not rewritten. Its markup, IDs, `style.css` and `script.js` still power the Profile Analyzer view.
- New workspace code is additive: `assets/css/app.css` loads after `style.css`; `assets/js/app.js` loads after `script.js` as an ES module.
- Untrusted API data is inserted with `textContent`. Static markup may be created with templates, but values are never concatenated into `innerHTML`.
- Every view controller is small and mounted once when first shown.

## Shell

`index.html` contains:

- `#platform-shell` with `.sidebar` and `.workspace`.
- `.topbar` with view label and navigation action.
- `#view-root` containing one `<section class="view">` per workspace view.
- `#view-analyzer`, which wraps the original `.app-container`.

Hash routing maps `#explore`, `#contributions`, etc. to view IDs. Buttons with `data-view` trigger navigation. The menu toggle is used on narrow screens.

## Modules

- `assets/js/api.js` — same-origin `/api` requests, error extraction, report downloads. With `file://`, it falls back to `http://127.0.0.1:8000/api`.
- `assets/js/ui.js` — DOM builders, badges, cards, meters, links, loading/error/empty states and export buttons.
- `assets/js/app.js` — navigation, view mounting and Chart.js resize after the hidden analyzer becomes visible.
- `assets/js/views/*.js` — one controller per view. Each exports `mount()`.

## Styling

`assets/css/app.css` uses separate `--shell-*` tokens so it cannot accidentally override the legacy analyzer variables. It follows a restrained, dense workspace aesthetic: neutral surfaces, hairline borders, monospace metadata and minimal gradients. Responsive rules collapse the sidebar and grid layouts below 900px and 640px.

## Preserved legacy IDs

The following IDs remain untouched because `script.js` depends on them: `theme-toggle`, `theme-icon-light`, `theme-icon-dark`, `search-form`, `github-input`, `analyze-btn`, `error-message`, `loading`, `empty-state`, `dashboard`, `avatar`, `name`, `username`, `bio`, `followers`, `following`, `public-repos`, `joined-date`, `location-line`, `company-line`, all `s-*` score rows, all `ins-*` insight rows, `repo-table-body`, `analysis-grid`, `languageChart`, `repoChart` and `streak-img-wrap`.

## Hidden chart handling

Chart.js instances created while the analyzer view is hidden can measure zero width. After navigating to the analyzer, `app.js` schedules two animation frames and calls `resize()` on all `Chart.instances`.
