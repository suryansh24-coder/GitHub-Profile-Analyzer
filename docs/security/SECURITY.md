# Security Notes

## Secrets

`GITHUB_TOKEN` and `OPENAI_API_KEY` are read only by backend settings from environment variables. No frontend module reads them. `/api/health` and `/api/ai/status` report only whether integrations are configured.

## Input validation

- `parse_username` strips profile URL prefixes and rejects invalid characters.
- `parse_repo` accepts `owner/repo` and GitHub URLs only; non-GitHub hosts and traversal segments are rejected.
- Pagination is bounded.
- Repository file reads are bounded by size and count.
- README and codebase analysis treat file content as text evidence, never as executable code.

## Output encoding

Frontend view controllers build elements with `document.createElement` and assign values through `textContent`. Links are allowed only for `http:` and `https:` URLs via `safeUrl`, with `rel="noopener noreferrer"`.

## Rate limits and upstream errors

The GitHub client caches by request path and parameters. A 403/429 response with `x-ratelimit-remaining: 0` becomes HTTP 429. Other upstream failures become structured errors without exposing credentials.

## Write actions

No endpoint writes to GitHub. `/api/repository/readme` returns `writeAction.enabled: false`. OAuth would require explicit user authorization, least-privilege scopes and an audit trail before any write feature is enabled.

## AI

AI is optional. Without a key, the backend returns 503 with setup guidance. The provider prompt instructs the model to cite evidence and avoid invented repository facts, but AI output is still labelled as Review Critically.

## CORS

CORS origins come from `CORS_ORIGINS`. Credentials are not allowed in browser requests.

## Known non-features

- No secret scanning is performed; the health report says `secretScanning: "not_performed"`.
- No vulnerability database query is performed; only manifest versions are parsed.
- No code from analysed repositories is executed.
