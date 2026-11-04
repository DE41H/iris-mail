# TODO

**P0** blocks launch · **P1** bug, security or privacy gap · **P2** should do soon · **P3** nice to have.
Each item says what is wrong, where, and the fix. Remove an item when it ships.

## P0: launch blockers

- [ ] **Test the full flow against live Google OAuth.** Ran locally on 2026-11-05 with live Gmail: add/remove
  by id and email, turn on, poll, Laya answer (`receipt: true, spend_category: shopping`), results filters,
  `ack`, no duplicates on a replayed history, plugin keys isolated from each other. Still to run: the
  `/subscriptions` on/off switch in a real browser (it was driven from a test client), and a backlog over
  250 messages (chunking).

<!--- [ ] **Pass Google's restricted-scope review.** `gmail.readonly` needs OAuth verification, a CASA security
  assessment, and a privacy policy and terms page linked from the consent screen. Neither page exists.-->

## P1: bugs, security and privacy

- [ ] **A rule can copy whole emails to the developer.** `_match` (`plugins/tasks/extract.py`) stores each
  match in full, and `RuleValidator` accepts any pattern, so the rule `(?s).+` returns the whole subject and
  body (reproduced). Breaks "never store email bodies" and the consent copy "Never the emails."
  (`SubscriptionRow.svelte`, `subscriptions.astro`). Fix: cut each stored match to ~200 characters
  (`m[:200]`) and say "answers and short matched snippets" in the consent copy.
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

<!--- [ ] **Developers cannot remove users.** Fixed: `POST /api/subscriptions/remove/` takes `user` or `email`
  like adding does, and always returns 204. Not yet run against a live database.-->
<!--- [ ] **Old mail gets shared when a plugin is turned on.** Fixed: each subscription stores `hist_from`
  (the Gmail history id when it was turned on) and `process` only answers mail added after it. Not yet run
  against live Gmail (see P0).-->
<!--- [ ] **A Laya outage silently drops mail.** `extract._answer` catches every exception and falls back to
  `_decide_each`, which logs and skips each message. If Laya fails for all of them (model download fails,
  out of memory), no results are saved, `process` still moves `hist_id` forward, and that mail is never
  answered (reproduced with a mocked `_decide`). Fix: in `_answer`, if `_decide_each` answered none of
  the messages, re-raise so `hist_id` stays put and the next poll retries.-->

## P2: should do soon

- [ ] **The Google token is refreshed on every poll.** `save_token` runs only inside the fetch loop of
  `process`, so with no new mail the token refreshed during `get_hist` is never saved: after the first hour
  every poll (480 a day per user) refreshes again. Fix: call `save_token(user, gmail)` once right after
  `get_hist` and drop it from the loop.
- [ ] **Deleting a plugin mid-run throws away other plugins' answers.** `_extract` saves all plugins'
  results in one `bulk_create` in `finally`; a plugin (or account) deleted meanwhile makes the insert fail on
  the foreign key (`ignore_conflicts` does not cover it), so the next poll calls Laya again for the others.
  Fix: save each plugin's results right after its `_guess`, inside `suppress(IntegrityError)`, and drop the
  `try/finally`.
- [ ] **Bad keys from one IP lock out valid keys from that IP.** `PluginKeyAuthentication` checks the
  per-IP fail counter before the key, so 10 bad keys from a shared IP (cloud NAT, serverless) block every
  developer behind it for an hour. Fix: check the key first; only on failure count and raise `Throttled`.
- [ ] **`process` logs nothing about its work.** A run that answers mail and one that skips it look the same
  in the worker log (only procrastinate's "job succeeded"). In the live test one mail went to Spam and was
  skipped, and only a manual Gmail history call showed why. Fix: one `logger.info` at the end of `process`
  with `user_id`, messages seen, messages fetched and results saved (counts only).
- [ ] **Open items are hidden in HTML comments here.** Several `<!-- -->` items are still open in code
  (incremental Gmail auth, invite links, Google review). Uncomment what is open, delete what shipped. Also
  pin uv in `docker/backend.dockerfile` (still `astral/uv:latest`): a new uv release can break the build.

<!--- [ ] **Chunked processing is untested.** `process` now fetches and answers mail 200 messages at a time and
  moves `hist_id` to just before the next chunk, so a backlog no longer loads into memory at once. Run it
  against live Gmail with a backlog over 200 (see P0) and watch `docker stats` on the worker.-->
<!--- [ ] **Rule matches have no size limit.** `_match` stores every `findall` hit. A 20 KB email and the rule `.`
  made a 100 KB `Result.output`; a long newsletter makes megabytes per result, per user, and the API pages
  50 of them. Fix: keep the first 20 hits per rule (`found[:20]`), say so in the result `output` help text,
  and compile each rule once per plugin instead of once per message.-->
<!--- [ ] **Any developer can probe users.** Fixed: subscribing by email always returns 202 (and matches
  case-insensitively).-->
<!--- [ ] **Any developer can spam users.** `POST /api/subscriptions/` still adds the plugin (inactive) to any
  account's list without asking. Fix: a signed invite link the user accepts (`django.core.signing`).-->
<!--- [ ] **Developers must grant Gmail access.** Every sign-in asks for `gmail.readonly`, even for developers
  who only build plugins. Ask for basic scopes at sign-in and for Gmail only when a user turns a plugin on
  (incremental auth).-->

## P3: nice to have

- [ ] **Two identical "add user" requests at once return 500.** The duplicate check in
  `SubscriptionSerializer.validate` runs before the insert, so the second hits the unique constraint as an
  `IntegrityError`. Catch it in `perform_create` and return 400.
- [ ] **Rules are compiled for every message.** `_match` calls `re2.compile` per rule per message and builds
  the full `findall` list before keeping 20 (the rule `.` on a big newsletter makes ~1M strings). Compile once
  per plugin per chunk.
- [ ] **One deleted message refetches the whole chunk one by one** (`gmail.fetch` 404 fallback). Fine for
  now; retry only the failed ids if it shows up in logs.
- [ ] **Revoked token with expired history loops.** `reset_hist` uses `get_hist_id`, which swallows
  `RefreshError`, so such a user is reset every 3 minutes and never disconnected. Mostly gone once the
  P1 "mail skipped" fix lands.
- [ ] `POST /api/subscriptions/remove/` returns 400 for an unknown user id, though the docs say always 204.
- [ ] **Some 400s do not name the field.** `?version=abc`, `?user=x` and `set_active {"active": "yes"}` return
  a bare list (`["A valid integer is required."]`), while `?fetched=maybe` returns `{"fetched": ...}`.
  Raise `ValidationError({"version": ...})` etc. so clients and the dashboard know which input failed.
- [ ] **Adding a user by id is not logged.** `SubscriptionViewSet.create` logs "Subscription added" only on
  the email path; the `user` path (`perform_create`) logs nothing. Add the same log line there.
- [ ] **`ack` counts already-acknowledged results.** Acking the same id twice returns `acknowledged: 1` both
  times. Filter `fetched=False` in the update if the count should mean "newly acknowledged", or reword the
  help text.
- [ ] **Mail in Spam is never read, even if moved to the inbox later.** `get_hist` only sees `messageAdded`
  with label INBOX; a message rescued from Spam is a `labelAdded` event. Fine as a choice; say so in the
  docs, or also read `labelAdded` INBOX events.
- [ ] **The Laya model downloads on the first mail.** The first `process` took 26 s and warned about
  unauthenticated Hugging Face requests. Download the model at worker start (or at image build into the
  `models` volume) and set `HF_TOKEN` in `.env` if downloads get rate-limited.
- [ ] Lean: move `retry` from `plugins/tasks/base.py` into `cleanup.py`; call `structuredClone` directly
  instead of `presets.clone`; delete the empty `frontend/src/routes/` and `frontend/src/lib/components/`.

<!--- [ ] `init_hist` has `retry=5`, but `get_hist_id` catches every error and returns `None`, so it never
  retries. Drop the option (`process` already resets a missing `hist_id`).-->
<!--- [ ] **Subscribing by email is case-sensitive.** `POST /api/subscriptions/ {"email": "U@X.com"}` returns
  404 for `u@x.com`. Use `email__iexact` in `SubscriptionSerializer.validate`.-->
<!--- [ ] **Laya only reads the first 3000 characters of a body** (`laya.email_state` default `max_chars`).
  Answers that sit lower in long emails are missed; raise `max_chars` if that shows up.-->
<!--- [ ] Set `DJANGO_HSTS_SECONDS=31536000` in production `.env` once HTTPS works (defaults to 3600).-->
<!--- [ ] Back up the `pgdata` volume.-->
<!--- [ ] Drop `prompt: consent` for returning users; Google shows the consent screen on every sign-in.-->
<!--- [ ] Show developers their subscribers and recent results in the dashboard, not just counts.-->
<!--- [ ] Send results to developers by webhook, and use Gmail push (`users.watch`) instead of polling.-->
