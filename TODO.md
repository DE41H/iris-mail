# TODO

**P0** blocks launch · **P1** bug, security or privacy gap · **P2** should do soon · **P3** nice to have.
Each item says what is wrong, where, and the fix. Remove an item when it ships.

## P0: launch blockers

## P1: bugs, security and privacy

- **One bad message stalls a user's mail forever.** Any exception while fetching or answering a single message fails
  the whole `process` job (`plugins/tasks/extract.py`, `plugins/gmail.py:get`). `hist_id` does not move, so every poll
  re-fetches the same batch and fails again, and no newer mail for that user is ever processed. Reproduced:
  simplegmail's `_evaluate_message_payload` raises `LookupError` for `charset=unknown-8bit` (seen in real spam). Laya
  errors other than `SchemaError` would do the same. Fix: in `get`, catch non-`HttpError` exceptions, log the message
  id and skip it; in `_guess`, catch Laya failures per plugin so one plugin can't block the others.

## P2: should do soon

- **Dashboard plugin counts are stale for up to 5 minutes.** cacheops caches the `PluginViewSet.get_queryset`
  query, and its `subscriber_count`/`result_count` subqueries on `Subscription`/`Result` don't invalidate it.
  Reproduced: a plugin with 1 active subscriber and 3 results showed 0/0. Fix: add `.nocache()` there.
- **A permanent Gmail API error fails every poll forever.** In `process`, any `HttpError` other than 404 is re-raised
  (`get_hist`, and `fetch` for non-404). A 401/403 (Gmail API disabled for the project, scope removed) then fails
  every 3 minutes with no disconnect and no message to the user. Not reproduced. Fix: treat 401/403 like a
  non-retryable `RefreshError` and call `disconnect(user)`.

## P3: nice to have

- **Wasted work on already-answered mail.** `_extract` calls Laya even when `todo` is empty (`decide_batch` with
  0 states, which may load the model), and `process` re-fetches messages that already have results. Fix: return
  early in `_guess` when `msgs` is empty; skip ids already in `Result` before `fetch`.
- **Check Laya answer quality.** In the e2e run, rules matched every time but Laya answers were often wrong:
  HTML and Hindi order emails gave `is_order: false`, and Rs. 52,000 and Rs. 1,499 both came back as `100_to_1000`.
  Not a code bug, but plugin answers can't be trusted yet.
- **Misleading error for an empty subscription create.** Sending neither `user` nor `email` to
  `POST /api/subscriptions/` returns "Send either user or email, not both."
  (`SubscriptionSerializer.validate`). Fix: say "Send `user` or `email`."
- **Sessions can be evicted.** Sessions live in Valkey (`SESSION_ENGINE` cache) with `maxmemory-policy volatile-lru`
  (`docker/docker-compose.yml`), so under memory pressure users are logged out. Fix: `cached_db` sessions or more
  headroom.
