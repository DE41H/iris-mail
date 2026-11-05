# TODO

**P0** blocks launch · **P1** bug, security or privacy gap · **P2** should do soon · **P3** nice to have.
Each item says what is wrong, where, and the fix. Remove an item when it ships.

## P0: launch blockers


## P1: bugs, security and privacy

- [ ] **Consent copy says "Never the emails" but rules store email text.** Rule matches (`_match`,
  `plugins/tasks/extract.py`) are cut to `MAX_MATCH_LENGTH` (200) but still store up to 16 × 20 snippets per
  mail. Fix: say "answers and short matched snippets" (`SubscriptionRow.svelte`, `subscriptions.astro`) and
  reword the "never store email bodies" invariant in AGENTS.md.
- [ ] **Mail right after turning a plugin on can be skipped.** `process` starts history from `user.hist_id`,
  set at sign-up and only advanced while a plugin is on. Sign up, wait over a week, turn a plugin on and
  send a test mail: the first poll gets a 404, `reset_hist` jumps to now and returns, and the test mail is
  never answered (same when `hist_id` is `None`). Fix: load active subscriptions before `get_hist` and start
  from `max(user.hist_id or 0, min(hist_from of subs that have one))`; only `reset_hist` when both are missing.
- [ ] **Dashboard counts are stale for up to 15 minutes.** `PluginViewSet.get_queryset` annotates
  `subscriber_count` and `result_count` with `Coalesce(Subquery(...))`. cacheops only tracks bare `Subquery`
  annotations (`cacheops/tree.py`) and `Result` is not cached, so turning a plugin on does not refresh the
  developer's count. Fix: `.nocache()` on that queryset. Reproduced live: after turning sharing off,
  `/api/plugins/` still showed 1 subscriber while the database had 0.


## P2: should do soon

- [ ] **Deleting a plugin mid-run throws away other plugins' answers.** `_extract` saves all plugins'
  results in one `bulk_create` in `finally`; a plugin (or account) deleted meanwhile makes the insert fail on
  the foreign key (`ignore_conflicts` does not cover it), so the next poll calls Laya again for the others.
  Fix: save each plugin's results right after its `_guess`, inside `suppress(IntegrityError)`, and drop the
  `try/finally`.



## P3: nice to have

- [ ] **One deleted message refetches the whole chunk one by one** (`gmail.fetch` 404 fallback). Fine for
  now; retry only the failed ids if it shows up in logs.
- [ ] **Revoked token with expired history loops.** `reset_hist` uses `get_hist_id`, which swallows
  `RefreshError`, so such a user is reset every 3 minutes and never disconnected. Mostly gone once the
  P1 "mail skipped" fix lands.
