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

- **Agent keys + MCP.** Plugin keys are per plugin, so agents can't create/edit plugins. Fix: `AgentKey` (developer FK, name, prefix, SHA-256 key, shown once, no cap, prefix `iris_agent_`; `PluginKeyAuthentication` returns `None` for non-`iris_` keys); `AgentKeyAuthentication` on `PluginViewSet` + results (with `plugin` filter); manage keys on `me` only (`ConfirmButton` revoke). `POST /api/v1/process/`: rules + LLM on agent-sent email, nothing stored, `quota` checked first (429), `consume(questions)` only on answer, own throttle, optional `Idempotency-Key` (Valkey 24h). `/api/v1/mcp/`: stateless JSON-RPC view (no SSE, single WSGI worker) mapping tools to those viewsets; return `validation.py` errors as tool errors. Update `/docs`, AGENTS.md.
