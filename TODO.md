# TODO

Each item says what is wrong, where, and the fix. Remove it when it ships.

| Priority | Meaning                       |
| -------- | ----------------------------- |
| **P0**   | blocks launch                 |
| **P1**   | bug, security or privacy gap  |
| **P2**   | should do soon                |
| **P3**   | nice to have                  |

## P0: launch blockers

_None._

## P1: bugs, security and privacy

- **Double `process` run.** `revive` retries jobs stalled >30s (`get_stalled_jobs` default); a frozen worker that resumes runs `process` twice → double LLM calls + usage (`extract._guess` calls LLM before the `Result` insert). Fix: raise `seconds_since_heartbeat` to ~600 in `cleanup.revive`, and claim rows first: `_extract` bulk-creates `pending` `Result` placeholders (uuid7 PKs, `ignore_conflicts`), reads back which landed, only those go to `llm.answer` + `consume`, then fills `output`; delete claims on LLM failure. Needs `pending` bool (default False), filtered in `ResultViewSet` + `_done`, stale pending rows removed by `cleanup`. Then drop it from AGENTS.md known issues.

## P2: should do soon

- **Unbounded `process` run.** `process` handles a user's whole backlog in one job: one flood blocks the single worker and lengthens stall risk. Fix: `BATCH_SIZE = 500` in `extract.py`, `ids = ids[:BATCH_SIZE]`, set `hist_id` to `added[ids[BATCH_SIZE]] - 1` when capped (else `latest`), log `capped left=`. Keep cap well above normal volume (`processed seen=` logs) or backlog outlives Gmail history (~1 week) → 404 → `reset_hist` skips mail.

## P3: nice to have

- **Agent keys.** Plugin keys are per plugin, so agents can't create/edit plugins. Done: `AgentKey` + `/api/v1/keys/` (session only) and `AgentKeyAuthentication` on `PluginViewSet`. Left: manage keys on `me` (`ConfirmButton` revoke, rotate); un-exclude plugin endpoints from `/docs` (needs an `AgentKey` scheme in `schema.py`).
- **`POST /api/v1/process/`.** Agents send an email to a plugin. Plugin key auth; rules + LLM (reuse `extract._rules`/`_match`/`_trim`, `llm.email`/`answer`), nothing stored; `quota` checked first → 429 with `{quota, left}`; `consume(questions)` only on answer; own throttle; optional `Idempotency-Key` (Valkey 24h).
- **`GET /api/v1/quota/`.** `{quota, used, left}` for today (`CustomUser.quota` + today's `Usage`), plugin or agent key. In `/docs`.
- **Agent docs.** `SKILL.md` (schema types, `MAX_*` from `meta.py`, reserved `rules`, RE2, connect flow, ack, 429 handling; link OpenAPI for endpoints) in a public repo/marketplace + served at `frontend/public/skill.md`; `frontend/public/llms.txt` listing `/docs`, `/static/schema/v1.json`, `skill.md`. Keep `MAX_*` in sync (add to AGENTS.md schema rule).
