# Deployment

## Local

```bash
python -m pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

Optional environment variables are listed in `.env.example`. The backend serves `index.html`, legacy assets and `/assets` directly, so one process is enough for local use.

## Vercel

`vercel.json` defines:

- `@vercel/python` for `api/index.py`.
- `@vercel/static` for `index.html`, `style.css`, `script.js` and `assets/**`.
- `/api/(.*)` routed to the Python adapter.
- Static assets routed directly.
- All other paths routed to the Python adapter, which serves `index.html`.

`api/index.py` inserts the repository root and `backend/` into `sys.path` and exports `app` from `backend/app/main.py`. Set environment variables in the Vercel project settings, not in frontend files.

This configuration has been syntax-checked locally by importing `api/index.py`; it has not been deployed to a live Vercel project in this workspace.

## Container-style deployment

Any ASGI host can run `backend.app.main:app`. Set `APP_ROOT` to the absolute repository root if the process working directory differs from the repository layout. Use a production ASGI server and terminate TLS at the platform edge.

## Operational checks

- `GET /api/health` should return `status: "ok"`.
- `GET /` should return the SPA shell.
- `GET /assets/js/app.js` should return JavaScript, not HTML.
- `GET /docs` should return OpenAPI documentation.
- Confirm `GITHUB_TOKEN` is not visible in any response or frontend bundle.
