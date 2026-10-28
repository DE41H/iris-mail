# AGENTS.md

Iris: email intelligence infrastructure. Developers define a schema-driven
plugin and get an API key; end users OAuth their Gmail and enable plugins. Mail
arrives via Pub/Sub, is deduplicated, queued, extracted by Laya, and stored as
structured results. Raw email is never persisted.

## Stack

Docker, Django 6.1 + DRF, Valkey (cache and dedupe), Procrastinate (background
tasks, Postgres-backed), PostgreSQL, Laya (extraction), Google OAuth (allauth),
Google Pub/Sub (inbox events). Python 3.13, uv.

## Layout

    backend/
      cfg/        settings, urls, wsgi/asgi
      plugins/    models, views, urls, admin (domain lives here)
    docker/       compose file and Dockerfiles (not written yet)

## Commands

    cd backend
    uv sync
    uv run manage.py migrate
    uv run manage.py runserver
    uv run manage.py procrastinate worker

## Conventions

- No tests and no unnecessary code. Verify changes by hand (run the app, hit the endpoint, check the shell) and do not add test files.
- Models: `uuid7` PKs, `UUIDField(primary_key=True, editable=False)`.
- Hot writes use `.update()` / `F()` expressions, then `refresh_from_db`.
- Add a DB index whenever a new query pattern appears; keep partial indexes
  for filtered sets (see `Result`'s unfetched index).
- Unique constraints belong in `Meta.constraints`, not `unique=True`, when
  they span fields.
- Plugin names are slugs, unique per developer.
- Endpoints live in `plugins/views.py`, routes in `plugins/urls.py` under
  `/api/`; DRF for new endpoints.

## Invariants (do not break)

- Never store email bodies or headers. Only structured `Result` output.
  User account addresses (`CustomUser.email`, required and unique) are
  stored for Pub/Sub matching.
- API keys are stored as SHA-256 only (`Plugin.key`), never plaintext; auth
  goes through `Plugin.auth_key()` (prefix lookup + `compare_digest`).
  Return the full key exactly once, from `rot_key()`.
- Respect `Subscription.active`; extract only for enabled plugins.
- Deduplicate before inference — no duplicate Laya calls.
- Secrets come from env; never commit keys or `.env`.

## Current state

Built, not yet run against live Google OAuth or Pub/Sub:

- Developers: create, list, view, edit, delete and rotate keys for plugins
  (API under `/api/plugins/`, dashboard under `/plugins`).
- Developers add users to a plugin with `POST /api/subscriptions/` (API key).
  Subscriptions start inactive; users turn them on at `/subscriptions` after
  a consent prompt. Users list their subscriptions at `/api/subscriptions/`.
- Ingestion: Pub/Sub push (`PubSubView`) defers `process`, which fetches Gmail
  history, dedupes in the DB, calls Laya and stores `Result`s. `Result.fetched`
  flips to true when the developer reads results.
- Admin: all models registered in `plugins/admin.py`.

Known gaps: Valkey dedupe (the cache is configured but unused), schema
validation on `Plugin.schema`, the DB host is hardcoded to `db`, the Docker
setup is not written (`docker/` files are empty), no test suite.

See `README.md` for the product overview.
