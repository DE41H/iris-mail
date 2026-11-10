# AGENTS.md

Iris: dev makes plugin (JSON schema questions + regex rules) → API key. User signs in with Google, subscribes. Gmail
polled /3 min, deduped, answered by LiteLLM (`tasks/llm.py`, `llm.MODELS` order: Gemini models (Flash Lite first),
then Claude Haiku as last fallback). Only answers stored (`Result`); devs list + ack (`fetched`) via API.

Stack: Django 6.1, DRF, drf-spectacular, Postgres 17, Procrastinate, Valkey, cacheops, allauth, django-otp, LiteLLM,
Granian, Astro 7, Svelte 5 (pnpm), Caddy, Docker, Python 3.13 (uv).

## Layout
- `backend/cfg/`: settings (`getenv`), urls, `middleware` (CSP, headers), `LOGGING` (structlog console)
- `backend/plugins/`: models, views, serializers, `gmail`, `token` (encrypted OAuth), `validation`, `meta`, `schema`,
  `signals`, `pagination` (uuid cursor), `authentication`+`throttling` (API keys: flat per-dev rate only; `UserThrottle` = dashboard), `admin` (OTP;
  tier editable; `Usage`, `Result` read-only), commands `mk_admin` `gen_schema`, `adapters` (Google,
  `prompt=select_account`; no refresh token → `?action=reauthenticate`)
- `plugins/tasks/`: `poll` (`poll_hist` /3 min, `init_hist`), `extract` (`process`), `llm` (router, provider schema,
  checks), `cleanup` (03:00: jobs >7d, results >100d or >30d if fetched/unsubscribed, usage >100d, codes >1d;
  `revive` /5 min retries stalled jobs)
- `backend/static/`: `iris.css`, `theme.js` (blocking, `data-theme` from `localStorage.theme`/system, `theme-color` meta from `--bg`; toggle in `Nav`);
  `templates/`: allauth
- `frontend/src/`: `pages/` (`me` account+usage, `connect` consent, `docs`), `components/`, `lib/` (`api` `session`
  `schema` `rules` `presets`)
- `docker/`: compose, Dockerfiles, `caddyfile`, `deploy.sh`, `.env.example` (all env vars)

Connect (only way to add a user): dev `POST /api/v1/codes/` → `code` + `/connect#<code>` (`Code` SHA-256, `CODE_TTL`
3 min, needs `Plugin.redirect`). User (signed in) GETs `/api/v1/connect/<code>/`, posts `accept` (subscribe, on) or
`deny` → `redirect?code&status`. Dev `GET /api/v1/codes/<code>/` (`user`/`email` if accepted). Remove:
`POST /api/v1/subscriptions/remove/`. `Connect.svelte`: code in `sessionStorage` `iris-connect` across sign-in,
stripped from URL; `?status=` → done state (empty redirect lands here); sign-in forwards `next`.

Usage: one `Usage` row/dev/day, `used` = emails × questions answered (`usage.consume` in `extract._guess`, which
checks `CustomUser.quota` from `QUOTAS` before each batch). `/api/v1/usage/` → `{today, days}` (newest first,
unpaginated). `/api/v1/me/` has `quota`, `tiers`.

## Run
Dev = prod. After every change: `docker/deploy.sh` (needs `docker/.env` from `.env.example`; builds, migrates,
`invalidate all`, collectstatic, `gen_schema`, rolls backend, copies frontend, restarts worker+caddy), test at
`https://localhost`. `dc` = `docker compose -f docker/docker-compose.yml`. Logs: `dc logs -f backend worker`. Schema:
`dc exec backend python manage.py spectacular --validate --file /dev/null`. Admin (password+TOTP): set
`DJANGO_SUPERUSER_*`, deploy, `dc exec backend python manage.py mk_admin` (creates/reuses, prints TOTP QR).

## Rules
- Read `TODO.md` first, update it. Update this file when layout/commands/tasks/rules/invariants change.
- No test files: deploy, check browser + logs. Small simple code, few comments.

Backend
- Gmail: `simplegmail` (`Gmail`, `Message`); `gmail.service` only for history, profile.
- Logs: `structlog.get_logger(__name__)`, short lowercase msg, ids as kwargs (`user=`, `plugin=`), never email
  content. `process` binds `user` (and `plugin` per sub) via `structlog.contextvars`. Prints `[level] msg [logger] k=v`.
- `uuid7` PKs, index every new query, constraints in `Meta.constraints`.
- Migrations run under the live old release: add only nullable/defaulted columns; drop/rename a release later.
- cacheops (insideout, survives Valkey eviction) caches `CustomUser`, `Plugin`, `Subscription` 5 min; never list
  `Result` (its signals kill fast-delete in cleanup/cascades): `.invalidated_update()` + `prefetch_related`, never
  `.update()`/`select_related`.
- `/docs` = API-key endpoints only; dashboard views `@extend_schema(exclude=True)`. Terse: API-wide facts in
  `SPECTACULAR_SETTINGS['DESCRIPTION']`, 1–2 lines/endpoint, `help_text` only if the name doesn't say it.
- Versioned URLs `/api/<version>/`; `ALLOWED_VERSIONS` is the only list (`v1`), no unversioned routes. New version:
  add there, branch on `request.version`. `@action` takes `**kwargs`. Frontend calls `/api/v1/`. `gen_schema` writes
  `/static/schema/<v>.json` + `versions.json` for `/docs` (no schema endpoint).

Schema
- Checks/`MAX_*` in `meta.py` (metaschemas), `validation.py`, `frontend/src/lib/schema.ts` + `rules.ts` (RE2 via
  re2js): change together. `rules` key reserved; matches → `output.rules`.
- Types: string enum (choice), array of enum (multi), boolean, integer range (scale), integer ≥ min (count), number
  ±min/max (range), short text (`string`, cut to `MAX_MATCH_LENGTH`), string `format` in `meta.FORMATS` (date,
  date-time, time, email, uri, hostname, ipv4, ipv6, uuid); `nullable: true`. Validated by `jsonschema` Draft 2020-12
  (`type` required, no extra keys). `llm._wire` → provider schema; LiteLLM validates replies (fail skips email);
  `llm._clean` handles formats (bad → null), NaN, duplicate picks, length. Only `date`/`date-time` sent as `format`;
  others = description hint + `llm.CHECKS`.

Frontend
- One screen/page, `client:only="svelte"` islands, short copy.
- CSP: no inline `<script>`/`style="…"` in `.astro`, no markdown pages.
- Destructive: inline `ConfirmButton`, never `confirm()`.
- Heavy code via `import()` beside API calls (`PluginEditor`/re2js in `NewPlugin`, `PluginDetail`). `preloadIslands` in
  `astro.config.mjs` adds modulepreload links for each page's static island imports.
- No chart lib (`Account` graph = CSS bars); no dep unless it removes more code than it adds.
- Caddy: `/_astro/*` immutable, `/static/fonts/*` 1y, rest `max-age=600`; `/x` served as `/x/index.html` (no
  redirect); `Speculation-Rules` header → `public/speculation-rules.json` prefetches pages on hover (not prerender:
  keeps load animations).
- Loading: content-shaped `.skel` + `.bone` (iris.css), hidden first 150ms.

## Invariants
- Never store email headers/bodies; only rule matches + LLM answers, snippets ≤ `MAX_MATCH_LENGTH`.
- API keys SHA-256, shown once.
- OAuth tokens encrypted (`token.py`, key = `DJANGO_SECRET_KEY` + `DJANGO_SALT_KEY`; changing either logs all out).
- Extract only active subs. Never LLM twice for same user+message+plugin.
- Secrets from env; `GEMINI_KEYS`, `ANTHROPIC_KEYS` (comma lists), paid tier only (Gmail Limited Use).
- LLM gets only sender, subject, first `llm.MAX_BODY` chars.

## Known issues (accepted, don't fix)
- LLM can be wrong / prompt-injected by email; rules are reliable.
- Unparseable mail (`gmail.get`) or LLM failure (`_guess`) skips that email (per plugin); `hist_id` moves on, no
  retry; logged.
- Dashboard plugin counts ≤5 min stale; tier changes ≤5 min (cacheops).
- Quotas overshoot (checked per batch; parallel workers); over-quota mail skipped for good.
- Sessions in Valkey (`volatile-lru`, 256 MB); eviction logs users out.
- `revive` retries jobs whose worker stopped heartbeating; a frozen worker that resumes runs `process` twice for one
  user (double LLM calls + usage, results dedupe). Rare; a slow task still heartbeats.
