# Database Schema

## Current release

No database is used. This is a deliberate choice for the first release:

- GitHub is the source of truth for public repository data.
- A bounded in-memory `TTLCache` reduces repeated upstream calls.
- Collab Hub entries are stored in the browser's `localStorage`.
- Theme preference uses the pre-existing `localStorage` key `theme`.

This keeps deployment simple and avoids storing personal data server-side.

## Planned schema (not implemented)

If persistence becomes necessary, the following tables are the intended shape. They are documentation only; no migration exists yet.

```sql
create table users (
  id uuid primary key,
  github_login text unique not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table saved_items (
  id uuid primary key,
  user_id uuid not null references users(id) on delete cascade,
  kind text not null check (kind in ('repository', 'issue', 'program')),
  external_url text not null,
  title text not null,
  tags text[] not null default '{}',
  created_at timestamptz not null default now()
);

create table analysis_cache (
  cache_key text primary key,
  payload jsonb not null,
  expires_at timestamptz not null
);

create table oauth_accounts (
  user_id uuid primary key references users(id) on delete cascade,
  provider text not null default 'github',
  encrypted_access_token bytea not null,
  scope text not null,
  expires_at timestamptz
);

create table audit_events (
  id bigserial primary key,
  user_id uuid references users(id) on delete set null,
  action text not null,
  target text not null,
  created_at timestamptz not null default now()
);
```

## Rules for future implementation

- Tokens must be encrypted at rest and never returned to the browser.
- Cache entries must expire and be deletable.
- Audit events must never contain token values.
- Migrations must be reversible and versioned.
