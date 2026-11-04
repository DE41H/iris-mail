# TODO

**P0** blocks launch · **P1** bug, security or privacy gap · **P2** should do soon · **P3** nice to have.
Each item says what is wrong, where, and the fix. Remove an item when it ships.

## P0: launch blockers

- [ ] **Test the full flow against live Google OAuth.** Sign in, add a user with `POST /api/subscriptions/`,
  turn the plugin on, receive mail, read `/api/results/`. Nothing past sign-in has run for real.

<!--- [ ] **Pass Google's restricted-scope review.** `gmail.readonly` needs OAuth verification, a CASA security
  assessment, and a privacy policy and terms page linked from the consent screen. Neither page exists.-->

## P1: bugs, security and privacy

Found in the 2026-11-05 audit (run against Postgres + Valkey with a faked Gmail; Laya not loaded):

- [ ] **One deleted email stops a user's mail for a week.** `gmail.fetch` falls back to `get()` per id when
  any message 404s, and `get()` returns `None` for the gone one. `_extract` then does `m.id` on `None`
  (`AttributeError`), `hist_id` never moves, and every poll fails the same way until Gmail's history
  expires (~1 week). Then `reset_hist` skips that whole week for every plugin. Reproduced: 3 new messages,
  one deleted before fetch. Common in real life (spam filters, quick deletes). Fix in `gmail.py:83`:
  `return [m for m in (get(gmail, id) for id in ids) if m]`.
- [ ] **Developers cannot remove users.** `DELETE /api/subscriptions/{id}/` needs a subscription id, but an
  API key can't list subscriptions (403), `POST` by email returns no body, and `GET /api/users/` returns
  user ids. Reproduced: `DELETE /api/subscriptions/<user id>/` returns 404. The README says developers can
  remove subscriptions. Fix: add `DestroyModelMixin` to `UserViewSet` with `perform_destroy` deleting
  `Subscription(plugin=request.auth, user=instance)`, so `DELETE /api/users/{id}/` works.

<!--- [ ] **Old mail gets shared when a plugin is turned on.** Fixed: each subscription stores `hist_from`
  (the Gmail history id when it was turned on) and `process` only answers mail added after it. Not yet run
  against live Gmail (see P0).-->
<!--- [ ] **A Laya outage silently drops mail.** `extract._answer` catches every exception and falls back to
  `_decide_each`, which logs and skips each message. If Laya fails for all of them (model download fails,
  out of memory), no results are saved, `process` still moves `hist_id` forward, and that mail is never
  answered (reproduced with a mocked `_decide`). Fix: in `_answer`, if `_decide_each` answered none of
  the messages, re-raise so `hist_id` stays put and the next poll retries.-->

## P2: should do soon


- [ ] **A message that kills the worker is retried forever.** If one batch makes Laya run out of memory
  (worker `mem_limit: 4g`), the job is left stalled, `revive` retries it every 5 minutes with no limit,
  and it dies the same way, blocking that user and taking the worker down each time. Not reproduced.
  Fix: in `revive`, fail jobs whose `attempts` is already 3 or more instead of retrying them.

<!--- [ ] **Rule matches have no size limit.** `_match` stores every `findall` hit. A 20 KB email and the rule `.`
  made a 100 KB `Result.output`; a long newsletter makes megabytes per result, per user, and the API pages
  50 of them. Fix: keep the first 20 hits per rule (`found[:20]`), say so in the result `output` help text,
  and compile each rule once per plugin instead of once per message.-->
<!--- [ ] **Any developer can probe users.** Fixed: subscribing by email always returns 202 (and matches
  case-insensitively).-->
<!--- [ ] **Any developer can spam users.** `POST /api/subscriptions/` still adds the plugin (inactive) to any
  account's list without asking. Fix: a signed invite link the user accepts (`django.core.signing`).-->
<!--- [ ] **Docker build uses `astral/uv:latest`** (`docker/backend.dockerfile`). A new uv release can break or
  change the build. Pin a version.-->
<!--- [ ] **Developers must grant Gmail access.** Every sign-in asks for `gmail.readonly`, even for developers
  who only build plugins. Ask for basic scopes at sign-in and for Gmail only when a user turns a plugin on
  (incremental auth).-->

## P3: nice to have


<!--- [ ] `init_hist` has `retry=5`, but `get_hist_id` catches every error and returns `None`, so it never
  retries. Drop the option (`process` already resets a missing `hist_id`).-->
<!--- [ ] **A big history backlog loads every message at once.** `process` fetches all new messages (up to a
  week of mail after downtime) into memory before Laya runs, with 2 jobs per 4 GB worker. Work through the
  ids in chunks of ~200; deduplication already makes partial progress safe.-->
<!--- [ ] **Subscribing by email is case-sensitive.** `POST /api/subscriptions/ {"email": "U@X.com"}` returns
  404 for `u@x.com`. Use `email__iexact` in `SubscriptionSerializer.validate`.-->
<!--- [ ] **Two identical requests at once return 500.** `validate_name` and the duplicate-subscription check
  run before the insert, so the second request hits the unique constraint as an `IntegrityError`. Catch it
  and return 400.-->
<!--- [ ] **Laya only reads the first 3000 characters of a body** (`laya.email_state` default `max_chars`).
  Answers that sit lower in long emails are missed; raise `max_chars` if that shows up.-->
<!--- [ ] Set `DJANGO_HSTS_SECONDS=31536000` in production `.env` once HTTPS works (defaults to 3600).-->
<!--- [ ] Back up the `pgdata` volume.-->
<!--- [ ] Drop `prompt: consent` for returning users; Google shows the consent screen on every sign-in.-->
<!--- [ ] Show developers their subscribers and recent results in the dashboard, not just counts.-->
<!--- [ ] Send results to developers by webhook, and use Gmail push (`users.watch`) instead of polling.-->
