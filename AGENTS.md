# AGENTS.md

Iris: email intelligence infrastructure. Developers define a schema-driven
plugin and get an API key; end users OAuth their Gmail and enable plugins. Mail
is polled from Gmail, deduplicated, queued, extracted by Laya, and stored as
structured results. Raw email is never persisted.

## Stack

Docker, Django 6.1 + DRF, Valkey (cache), Procrastinate (background
tasks, Postgres-backed), PostgreSQL, Laya (extraction), Google OAuth (allauth),
Gmail API history polling (inbox events), Astro + TypeScript (dashboard).
Python 3.13, uv.

## Layout

    backend/
      cfg/        settings, urls, wsgi/asgi
      plugins/    models, views, urls, admin (domain lives here)
      static/     iris.css, shared by the dashboard and the Django auth pages
      templates/  allauth pages
    frontend/     Astro static site, plain TypeScript and DOM, no framework
      src/lib/    api (fetch, DRF errors), schema (Laya rules), builder
                  (schema editor), session (signed-in user), keycard
      src/pages/  plugins/, subscriptions
    docker/       compose file and Dockerfiles

## Commands

    cd backend
    uv sync
    uv run manage.py migrate
    uv run manage.py runserver
    uv run manage.py procrastinate worker

    cd frontend
    npm install
    npm run dev      # :4321, proxies /api, /accounts, /static, /admin to :8000

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
- Frontend: Astro pages with TypeScript modules in `frontend/src/lib/`. Build
  DOM with `el()` from `api.ts`; no framework. `schema.ts` mirrors the rules of
  Laya's `structured.py` (at most 32 properties; enum, boolean, or integer
  range of at most 10 levels). Update it in step when Laya changes.
- Destructive or sharing actions get an inline confirmation, not `confirm()`.

## Invariants (do not break)

- Never store email bodies or headers. Only structured `Result` output.
  User account addresses (`CustomUser.email`, required and unique) are
  stored.
- API keys are stored as SHA-256 only (`Plugin.key`), never plaintext; auth
  goes through `Plugin.auth_key()` (prefix lookup + `compare_digest`).
  Return the full key exactly once, from `rot_key()`.
- Respect `Subscription.active`; extract only for enabled plugins.
- Deduplicate before inference — no duplicate Laya calls.
- Secrets come from env; never commit keys or `.env`.

## Current state

Built, not yet run against live Google OAuth:

- Developers: create, list, view, edit, delete and rotate keys for plugins
  (API under `/api/plugins/`, dashboard under `/plugins`). Create and edit use a
  field builder (choice, yes/no, scale) that writes Laya's schema and previews
  the JSON. A saved schema the builder cannot represent is shown with the
  reason, and saving is disabled so no property is dropped.
- Users sign in with Google first; that creates their account. `/api/me/`
  returns the signed-in user, and the header reads it to show Sign in or the
  account with Sign out. Developers then add a user to a plugin with
  `POST /api/subscriptions/` (API key, user UUID). Developers see the email and
  username of each subscribed user (`/api/users/`).
- Subscriptions start inactive. Users list them at `/api/subscriptions/`, which
  include each plugin's name and description. On `/subscriptions`, turning a
  plugin on shows an inline consent prompt; turning it off takes effect at once.
- Ingestion: a periodic task (`poll_inboxes`, every three minutes) defers
  `process` for each Google user with an active subscription. `process` fetches
  Gmail history, skips messages already stored for that user and plugin (unique
  `Result` per user, message and plugin), calls Laya and stores `Result`s.
  `Result.fetched` flips to true when the developer reads results. Refreshed
  Google access tokens are saved back to `SocialToken`.
- Admin: all models registered in `plugins/admin.py`.

Known gaps: `Plugin.schema` is validated only in the frontend builder; the API
accepts any JSON, and a schema Laya rejects is logged and skipped at processing
time. The DB host defaults to `db` (set `POSTGRES_HOST` to change it). The
Docker files are written but have not been run end to end. No test suite. No
way for a developer to search for a user by email or username (`/api/users/`
lists only subscribed users).

See `README.md` for the product overview.
