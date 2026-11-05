# TODO

**P0** blocks launch · **P1** bug, security or privacy gap · **P2** should do soon · **P3** nice to have.
Each item says what is wrong, where, and the fix. Remove an item when it ships.

## P0: launch blockers

## P1: bugs, security and privacy

- [ ] **Mail right after turning a plugin on can be skipped.** `process` starts history from `user.hist_id`,
  set at sign-up and only advanced while a plugin is on. Sign up, wait over a week, turn a plugin on and
  send a test mail: the first poll gets a 404, `reset_hist` jumps to now and returns, and the test mail is
  never answered (same when `hist_id` is `None`). Fix: load active subscriptions before `get_hist` and start
  from `max(user.hist_id or 0, min(hist_from of subs that have one))`; only `reset_hist` when both are missing.

## P2: should do soon

## P3: nice to have

