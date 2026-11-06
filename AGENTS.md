# AGENTS.md

Iris: devs make a plugin (JSON schema questions + regex rules) and get an API key. Users sign in with Google and
subscribe. Gmail is polled every 3 min, deduped, answered by Laya. Only answers are stored (`Result`); devs list and
ack them (`fetched`) via API.

Stack: Django 6.1, DRF, drf-spectacular, Postgres 17, Procrastinate, Valkey, cacheops, allauth, django-otp, Laya,
Granian, Astro 7, Svelte 5, Caddy, Docker, Python 3.13 (uv).

## Layout

- `backend/cfg/`: settings (env via `getenv`), urls, `middleware.py` (CSP, headers)
- `backend/plugins/`: models, views, serializers, `gmail`, `token` (encrypted OAuth), `validation`, `schema`, `signals`,
  `adapters` (Google OAuth), `authentication`/`throttling` (API keys, flat developer rate), `pagination` (uuid cursor)
- Usage: `Usage` is one row per developer per day (`used` = emails × schema questions sent to Laya, charged by
  `usage.consume` in `extract._guess` after Laya succeeds). `/me` reads it at `/api/usage/` (`{today, days}`: last 90 days, unpaginated). Daily quota per
  tier is `QUOTAS` in `models.py` (`CustomUser.quota`), checked in `_guess` before each Laya batch;
  `/api/me/` returns it as `quota`.
- `backend/plugins/tasks/`: `poll` (`poll_hist` every 3 min, `init_hist`), `extract` (`process`), `cleanup`
  (`cleanup` 03:00 daily: jobs >7d, results >100d, or >30d if fetched/unsubscribed, usage >100d; `revive` every 5 min: retry stalled jobs)
- `backend/static/`: `iris.css` (dashboard, auth pages), `nav.js` (swipe direction for page view transitions);
  `backend/templates/` (allauth)
- `frontend/src/`: `pages/` (Astro; `me` = account, quota and usage), `components/` (Svelte), `lib/` (`api`, `session`,
  `schema`, `rules`, `presets`)
- `docker/`: compose, Dockerfiles, `caddyfile`, `deploy.sh`, `.env.example` (all env vars)

## Run

Dev = prod. Run `docker/deploy.sh` after every change and test at `SITE_ADDRESS` (`https://localhost`). Needs
`docker/.env` (copy `.env.example`). It builds, migrates, runs `invalidate all` and collectstatic, rolls out backend,
copies frontend, restarts worker and caddy. `dc` = `docker compose -f docker/docker-compose.yml`.

```bash
docker/deploy.sh
dc logs -f backend worker
dc exec backend python manage.py spectacular --validate --file /dev/null
```

Admin needs password + TOTP. Make a device per superuser:

```bash
dc exec backend python manage.py shell -c "from django_otp.plugins.otp_totp.models import TOTPDevice as T; from plugins.models import CustomUser as U; print(T.objects.create(user=U.objects.get(username='NAME'), name='admin').config_url)"
```

## Rules

- Read `TODO.md` first. Update it when you finish or find something.
- Update this file in the same change when layout, commands, tasks, rules or invariants change.
- No test files. Test by hand: deploy, check the site in a browser and the logs.
- Small, simple code, few comments.

Backend
- Gmail: use `simplegmail` (`Gmail`, `Message`). Use `gmail.service` only for history and profile.
- Log with `logging.getLogger(__name__)`, ids in `extra=`, never email content.
- `uuid7` PKs. Index every new query. Constraints in `Meta.constraints`.
- Migrations run while the old release is live: only add nullable or defaulted columns; drop or rename a release later.
- cacheops caches `CustomUser`, `Plugin`, `Subscription` for 5 min. On them use `.invalidated_update()` and
  `prefetch_related`, never `.update()` or `select_related`.
- `/docs` shows API-key endpoints only. Mark dashboard views `@extend_schema(exclude=True)`.

Schema
- Checks and `MAX_*` limits are in `plugins/validation.py` and `frontend/src/lib/schema.ts` (+ `rules.ts`, RE2 via
  re2js). Change both together.
- `rules` is a reserved key; rule matches go to `output.rules`.

Frontend
- One screen per page, `client:only="svelte"` islands, short copy.
- CSP: no inline `<script>` or `style="…"` in `.astro`, no markdown pages.
- Destructive actions: inline `ConfirmButton`, never `confirm()`.
- Loading: content-shaped `.skel` wrapper with `.bone` placeholders (iris.css); it stays hidden for 150ms.

## Invariants

- Never store email headers or bodies. Only rule matches, cut to `MAX_MATCH_LENGTH`.
- API keys: SHA-256 only, shown once.
- OAuth tokens encrypted (`plugins/token.py`, key = `DJANGO_SECRET_KEY` + `DJANGO_SALT_KEY`; changing one logs out all users).
- Extract only for active subscriptions. Never call Laya twice for the same user, message and plugin.
- Secrets come from env.

## Known issues (accepted, don't fix)

- Laya can be wrong (Hindi mail, number ranges). Rules are reliable.
- Mail simplegmail can't parse is skipped (`gmail.get`). A Laya failure skips that plugin's batch (`_guess`).
  `hist_id` moves on, so no retry. Both logged.
- Dashboard plugin counts can be 5 min stale.
- Usage quotas overshoot: the check runs before a whole batch, and two workers on one developer can both pass it.
  Over-quota mail is skipped for good (`hist_id` moves on). Tier changes take up to 5 min (cacheops).
- Sessions are in Valkey (`volatile-lru`, 256 MB); eviction logs users out. Polling is fine.
