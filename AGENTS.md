# AGENTS.md

Iris: email intelligence infrastructure. Developers define a schema-driven
plugin and get an API key; end users OAuth their Gmail and enable plugins. Mail
arrives via Pub/Sub, is deduplicated, queued, extracted by Laya, and stored as
structured results. Raw email is never persisted.

## Stack

Django 6.1 + DRF, PostgreSQL, Celery + RabbitMQ, Dragonfly (dedupe), Google
Pub/Sub, Google OAuth (allauth), Laya (extraction). Python 3.13, uv.

## Layout

    backend/
      cfg/        settings, urls, wsgi/asgi, celery app
      plugins/    models, views, urls, admin (domain lives here)
    docker/       compose/services (empty for now)

## Commands

    cd backend
    uv sync
    uv run manage.py migrate
    uv run manage.py runserver
    uv run celery -A cfg worker -l info

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

- Never store email bodies, headers, or addresses. Only structured `Result`
  output.
- API keys are stored as SHA-256 only (`Plugin.key`), never plaintext; auth
  goes through `Plugin.authenticate()` (prefix lookup + `compare_digest`).
  Return the full key exactly once, from `rotate_key()`.
- Respect `Subscription.active`; extract only for enabled plugins.
- Deduplicate before inference — no duplicate Laya calls.
- Secrets come from env; never commit keys or `.env`.

## Current state

Scaffolding. Models + key helpers exist; `views.py`, `urls.py`, `admin.py` are
stubs, no migrations are committed, and `settings.py` is stock (SQLite, no
`plugins`/allauth/DRF/Celery/Postgres wiring). No test suite yet.

See `README.md` for the product overview.
