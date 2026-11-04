# AGENTS.md

Iris: developers define a plugin (questions as a JSON schema) and get an API key. Users sign in with
Google and turn plugins on. New Gmail mail is polled, deduplicated and answered by Laya; only the
answers are stored, as `Result`s.

Stack: Django 6.1 + DRF, drf-spectacular, PostgreSQL, Procrastinate, Valkey + django-cacheops,
allauth (Google), Laya, Astro + Svelte 5, Caddy, Docker. Python 3.13 with uv.

## Layout

    backend/cfg/        settings, urls, security headers
    backend/plugins/    models, views, serializers, tasks, gmail, validation, schema
    backend/static/     iris.css (dashboard and auth pages)
    frontend/src/       pages/ (Astro), components/ (Svelte), lib/
    docker/             compose, Dockerfiles, caddyfile

## Commands

    cd backend && uv sync && uv run manage.py migrate && uv run manage.py invalidate all && uv run manage.py runserver
    cd backend && uv run manage.py procrastinate worker
    cd frontend && npm install && npm run dev     # :4321, proxies to :8000
    cd docker && docker compose up -d --build
    # admin login is password + TOTP (django-otp); give each superuser a device, scan the printed URL:
    uv run manage.py shell -c "from django_otp.plugins.otp_totp.models import TOTPDevice as T; from plugins.models import CustomUser as U; print(T.objects.create(user=U.objects.get(username='NAME'), name='admin').config_url)"

## Rules

- No test files. Verify by hand against the running app.
- Keep code simple, small and lightly commented.
- Log with `logging.getLogger(__name__)`, ids in `extra=`, never email content.
- `uuid7` PKs. Index every new query pattern; constraints go in `Meta.constraints`.
- cacheops caches `CustomUser`, `Plugin`, `Subscription`: use `.invalidated_update()` and
  `prefetch_related`, never `.update()` or `select_related`. Run `manage.py invalidate all` after migrations.
- `/docs` renders the OpenAPI schema for the API-key endpoints only; mark dashboard views
  `@extend_schema(exclude=True)`. Check: `uv run manage.py spectacular --validate --file /dev/null`.
- Frontend: one screen per page, `client:only="svelte"` islands, short copy.
- CSP: no inline `<script>` or `style="…"` in `.astro` files.
- Schema rules live in `plugins/validation.py` and `frontend/src/lib/schema.ts`; change both together.
- Destructive actions use an inline confirmation (`ConfirmButton`), never `confirm()`.

## Invariants

- Never store email bodies or headers.
- API keys are stored as SHA-256 only and shown once.
- Extract only for active subscriptions, and never call Laya twice for the same user, message and plugin.
- Secrets come from env.

Open work is in `TODO.md`. Keep this file and `CLAUDE.md` in agreement.
