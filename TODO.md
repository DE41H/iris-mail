# TODO

**P0** blocks launch · **P1** bug, security or privacy gap · **P2** should do soon · **P3** nice to have.
Each item says what is wrong, where, and the fix. Remove an item when it ships.

## P0: launch blockers

- [ ] **Test the full flow against live Google OAuth.** Sign in, add a user with `POST /api/subscriptions/`,
  turn the plugin on, receive mail, read `/api/results/`. Nothing past sign-in has run for real.

<!--- [ ] **Pass Google's restricted-scope review.** `gmail.readonly` needs OAuth verification, a CASA security
  assessment, and a privacy policy and terms page linked from the consent screen. Neither page exists.-->

## P1: bugs, security and privacy

- [ ] **Old mail gets shared when a plugin is turned on.** `hist_id` is set at sign-up and freezes while a
  user has no active subscription (`tasks.poll_hist`). Turning a plugin on later processes all mail since
  then (up to Gmail's ~1 week of history). Fix: reset `hist_id` to the current Gmail history id when a
  user goes from zero to one active subscription, or store `activated_at` and skip older messages.
  Same after "Reconnect Google": a revoked user's `hist_id` stays at the revoke point, so mail from the
  disconnected days is processed once they turn plugins back on.
- [ ] **A Laya outage silently drops mail.** `extract._answer` catches every exception and falls back to
  `_decide_each`, which logs and skips each message. If Laya fails for all of them (model download fails,
  out of memory), no results are saved, `process` still moves `hist_id` forward, and that mail is never
  answered (reproduced with a mocked `_decide`). Fix: in `_answer`, if `_decide_each` answered none of
  the messages, re-raise so `hist_id` stays put and the next poll retries.
- [ ] **A failed `init_hist` means the user is never polled.** `init_hist` retries 5 times, then gives up
  with `hist_id = None`. `process` returns early on `None` every 3 minutes, so the user's plugins show
  "on" but nothing is extracted, and nothing logs it. Fix: in `process`, when `hist_id` is `None`, set the
  baseline with `_reset_history(user)` instead of returning.

## P2: should do soon

- [ ] **Any developer can probe and spam users.** `POST /api/subscriptions/` with an email returns 404 or
  201, which reveals whether that email has an account, and adds the plugin to that user's list without
  asking them. Use an invite link the user accepts, or return the same response either way.
- [ ] **Plugins can only extract with Laya questions.** Add `Plugin.regexes`, a JSON object of
  `{name: pattern}`. `process` runs each pattern over subject + plain body and stores every match as a
  list under `output.extra`. Make `extra` a reserved key in the schema. A plugin needs questions, regexes
  or both, and regex-only plugins skip Laya. Validate in `validation.py` and `schema.ts`, run patterns with
  `regex` and a timeout against ReDoS, bump `version` when regexes change, and add a regex section to the
  plugin editor. Full plan: `~/.claude/plans/i-want-to-add-transient-liskov.md`.

<!--- [ ] **Docker build uses `astral/uv:latest`** (`docker/backend.dockerfile`). A new uv release can break or
  change the build. Pin a version.-->
<!--- [ ] **Developers must grant Gmail access.** Every sign-in asks for `gmail.readonly`, even for developers
  who only build plugins. Ask for basic scopes at sign-in and for Gmail only when a user turns a plugin on
  (incremental auth).-->

## P3: nice to have

- [ ] **A big history backlog loads every message at once.** `process` fetches all new messages (up to a
  week of mail after downtime) into memory before Laya runs, with 2 jobs per 4 GB worker. Work through the
  ids in chunks of ~200; deduplication already makes partial progress safe.
- [ ] **`_laya()` can build two routers.** `functools.cache` doesn't lock, and the worker runs 2 sync jobs
  in threads, so two first-time calls can each load the model. Guard it with a `threading.Lock`.

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
<!--- [ ] `PluginViewSet` counts all results per plugin on every request; store a counter if it gets slow.-->
<!--- [ ] Show developers their subscribers and recent results in the dashboard, not just counts.-->
<!--- [ ] Send results to developers by webhook, and use Gmail push (`users.watch`) instead of polling.-->
