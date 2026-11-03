# AGENTS.md

Iris: email intelligence infrastructure. A developer defines a plugin (questions as a JSON schema) and
gets an API key. A user signs in with Google and turns the plugin on. New Gmail mail is polled,
deduplicated, answered by Laya, and only the answers are stored as `Result`s.

Stack: Django 6.1 + DRF, PostgreSQL, Procrastinate (tasks), Valkey (cache), allauth (Google OAuth),
Laya, Astro + Svelte 5 + TypeScript, Caddy, Docker. Python 3.13 with uv.

## Layout

    backend/cfg/        settings, urls, security headers
    backend/plugins/    models, views, serializers, tasks (polling + Laya), gmail, validation
    backend/static/     iris.css: theme for the dashboard and the Django auth pages
    backend/templates/  allauth pages
    frontend/src/       pages/ (Astro), components/ (Svelte islands), lib/ (api, schema, presets, session)
    docker/             compose, Dockerfiles, caddyfile

## Commands

    cd backend && uv sync && uv run manage.py migrate && uv run manage.py runserver
    cd backend && uv run manage.py procrastinate worker
    cd frontend && npm install && npm run dev     # :4321, proxies /api /accounts /static /admin to :8000
    cd docker && docker compose up -d --build     # full stack behind Caddy

## Conventions

- No test files. Verify by hand: run the app, hit the endpoint, check the shell or browser.
- Keep code simple, modular and lightly commented.
- Models use `uuid7` PKs. Hot writes use `.update()` / `F()`, then `refresh_from_db`.
- Every new query pattern gets an index; filtered sets get partial indexes.
- Constraints across fields go in `Meta.constraints`.
- Endpoints in `plugins/views.py`, routes in `plugins/urls.py` under `/api/`, built with DRF.
- Frontend: Astro pages mount Svelte islands with `client:only="svelte"`. Each page fits one screen and
  scrolls inside its panels. Keep copy short.
- CSP: no inline `<script>` or `style="…"` attributes in `.astro` files. Astro hashes its own inline
  code into a meta CSP, and Caddy blocks anything else. Svelte `style:` directives are fine.
- `Plugin.schema` is validated by Laya's own `plan_from_json_schema` (`plugins/validation.py`).
  `frontend/src/lib/schema.ts` mirrors those rules for the builder; update both when Laya changes.
- Destructive or sharing actions get an inline confirmation, never `confirm()`.

## Invariants

- Never store email bodies or headers; only `Result.output`.
- API keys are stored as SHA-256 only, checked via `Plugin.auth_key()`, and shown once from `rot_key()`.
- Extract only for subscriptions with `active=True`.
- Deduplicate before inference: never call Laya twice for the same user, message and plugin.
- Secrets come from env. Never commit keys or `.env`.

## Status and work

Built and running in Docker; not yet tested against live Google OAuth. Open work, bugs and ideas live in
`TODO.md` by priority. Update it when you finish or find something.

## Keep in sync

`AGENTS.md` and `CLAUDE.md` describe the same project. When you change one, update the other in the
same change.
