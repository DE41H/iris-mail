# AGENTS.md

Iris: developers define a plugin (questions as a JSON schema) and get an API key. Users sign in with Google and turn
plugins on. New Gmail mail is polled every 3 minutes, deduplicated and answered by Laya; only the answers are stored,
as `Result`s.

**Stack:** Django 6.1 + DRF, drf-spectacular, PostgreSQL, Procrastinate, Valkey + django-cacheops, allauth (Google),
django-otp, Laya, Astro 7 + Svelte 5, Caddy, Docker. Python 3.13 with uv.

## Layout

| Path                     | Contents                                                          |
| ------------------------ | ----------------------------------------------------------------- |
| `backend/cfg/`           | settings, urls, middleware (CSP and security headers)             |
| `backend/plugins/`       | models, views, serializers, gmail, token, validation, schema, signals |
| `backend/plugins/tasks/` | `poll` (`poll_hist`, `init_hist`), `extract` (`process`), `cleanup` (`cleanup`, `revive`) |
| `backend/static/`        | `iris.css` (dashboard and auth pages)                             |
| `backend/templates/`     | allauth pages                                                     |
| `frontend/src/`          | `pages/` (Astro), `components/` (Svelte), `lib/`                  |
| `docker/`                | compose, Dockerfiles, `caddyfile`, `deploy.sh`, `.env.example` |

## Commands

```bash
cd backend && uv sync && uv run manage.py migrate && uv run manage.py invalidate all && uv run manage.py runserver
cd backend && uv run manage.py procrastinate worker
cd frontend && npm install && npm run dev     # :4321, proxies to :8000
docker/deploy.sh                              # build, migrate, roll out backend, copy frontend, restart changed worker/Caddy
```

Admin login is password + TOTP. Give each superuser a device and scan the printed URL:

```bash
uv run manage.py shell -c "from django_otp.plugins.otp_totp.models import TOTPDevice as T; from plugins.models import CustomUser as U; print(T.objects.create(user=U.objects.get(username='NAME'), name='admin').config_url)"
```

## Rules

**Workflow**
- Read `TODO.md` first; update it when you finish or find something.
- No test files. Verify by hand against the running app; check UI in a browser against `npm run build` (CSP is
  enforced only in production).
- Keep code simple, small and lightly commented.

**Backend**
- Gmail: use `simplegmail` (`Gmail`, `Message`); call `gmail.service` only for what it lacks (history, profile).
- Log with `logging.getLogger(__name__)`, ids in `extra=`, never email content.
- `uuid7` PKs. Index every new query pattern; constraints go in `Meta.constraints`.
- Migrations run while the previous release still serves: keep them backward-compatible (new columns nullable or
  defaulted; drop or rename one release later).
- cacheops caches `CustomUser`, `Plugin`, `Subscription`: use `.invalidated_update()` and `prefetch_related`, never
  `.update()` or `select_related`. Run `manage.py invalidate all` after migrations.
- `/docs` shows the OpenAPI schema for API-key endpoints only; mark dashboard views `@extend_schema(exclude=True)`.
  Check: `uv run manage.py spectacular --validate --file /dev/null`.

**Schema and rules**
- Checks live in `plugins/validation.py` and `frontend/src/lib/schema.ts` (`rules.ts` for rules, RE2 via re2js);
  change both together.
- `rules` is reserved: rule matches land in `output.rules`.

**Frontend**
- One screen per page, `client:only="svelte"` islands, short copy.
- CSP: no inline `<script>` or `style="…"` in `.astro` files.
- Destructive actions use an inline confirmation (`ConfirmButton`), never `confirm()`.

## Invariants

- Never store email headers or whole bodies; only rule matches, cut to `MAX_MATCH_LENGTH`.
- API keys are stored as SHA-256 only and shown once.
- Google OAuth tokens are encrypted at rest (`plugins/token.py`, key from `DJANGO_SECRET_KEY` + `DJANGO_SALT_KEY`).
- Extract only for active subscriptions, and never call Laya twice for the same user, message and plugin.
- Secrets come from env.

## Known drawbacks (accepted, don't fix)

- Laya answers can be wrong (Hindi mail, number ranges); rules are reliable. Not a code bug.
- Mail simplegmail can't parse is skipped in `gmail.get`; a Laya failure skips that plugin's batch in `_guess`.
  `hist_id` moves on, so neither is retried. Both are logged.
- Dashboard plugin counts are cached by cacheops for up to 5 minutes; their subqueries don't invalidate it.
- Sessions use the Valkey cache (`volatile-lru`), so eviction logs users out. Polling is unaffected.
