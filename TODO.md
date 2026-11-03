# TODO

**P0** blocks launch · **P1** bug, security or privacy gap · **P2** should do soon · **P3** nice to have.
Each item says what is wrong, where, and the fix. Remove an item when it ships.

## P0: launch blockers

- [ ] **Test the full flow against live Google OAuth.** Sign in, add a user with `POST /api/subscriptions/`,
  turn the plugin on, receive mail, read `/api/results/`. Nothing past sign-in has run for real.
- [ ] **Pass Google's restricted-scope review.** `gmail.readonly` needs OAuth verification, a CASA security
  assessment, and a privacy policy and terms page linked from the consent screen. Neither page exists.

## P1: bugs, security and privacy

- [ ] **Old mail gets shared when a plugin is turned on.** `hist_id` is set at sign-up and freezes while a
  user has no active subscription (`tasks.poll_inboxes`). Turning a plugin on later processes all mail since
  then (up to Gmail's ~1 week of history). Fix: reset `hist_id` to the current Gmail history id when a
  user goes from zero to one active subscription, or store `activated_at` and skip older messages.
- [ ] **A revoked Google token fails forever.** `google.auth.exceptions.RefreshError` is not caught in
  `process`, so the job fails 3 times every 3 minutes for good. Catch it, deactivate the user's
  subscriptions, and show "reconnect Google" in the UI.
- [ ] **One bad message stops a user's inbox for good.** Any Laya error other than `SchemaError` fails the
  whole `process` job before `hist_id` advances, so every later poll hits the same message again. Catch
  errors per message, log them, and move on.
- [ ] **OAuth tokens are stored in plain text.** `SocialToken.token_secret` (the refresh token, i.e. inbox
  access) is a plain column, and allauth's admin shows it. Encrypt it at rest with a key from env.
- [ ] **`/admin/` is public.** Caddy proxies it to the internet, and it shows tokens and results. Restrict
  it to an IP allowlist or a private port, or remove it from the Caddyfile.
- [ ] **Polls pile up.** `poll_inboxes` queues `process` for every user every 3 minutes. `lock=` only stops
  two jobs from running at once, so a slow worker builds an endless queue. Use `queueing_lock=user_id`
  and ignore `AlreadyEnqueued`.
- [ ] **Containers do not restart.** No service in `docker-compose.yml` has a `restart:` policy, so a
  crash or reboot takes the app down. Add `restart: unless-stopped`.

## P2: should do soon

<!--- [ ] **Developers must grant Gmail access.** Every sign-in asks for `gmail.readonly`, even for developers
  who only build plugins. Ask for basic scopes at sign-in and for Gmail only when a user turns a plugin on
  (incremental auth).-->
- [ ] **Any developer can probe and spam users.** `POST /api/subscriptions/` with an email returns 404 or
  201, which reveals whether that email has an account, and adds the plugin to that user's list without
  asking them. Use an invite link the user accepts, or return the same response either way.
- [ ] **HTML-only emails reach Laya with an empty body.** `process` passes `message.plain or ""`. Fall back
  to `message.html` stripped to text, and pass `sender=` to `laya.email_state`.
- [ ] **One worker answers every inbox in turn.** The worker runs with Procrastinate's default concurrency
  of 1, and calls `laya.decide` once per message per plugin. Group messages per plugin with
  `laya.decide_batch`, then size concurrency and worker memory for the models (`max_loaded`).
- [ ] **The job table grows forever.** Procrastinate keeps finished jobs, and a new one is added per user
  every 3 minutes. Schedule the built-in `remove_old_jobs` task as a periodic job.
- [ ] **Results are kept forever.** Fetched results, and results for removed subscriptions, are never
  deleted. Set a retention period (for example 30 days after ack) and delete older results on a schedule.

## P3: nice to have

- [ ] Pin image versions: `astral/uv:latest`, `node:22-alpine`, `caddy:2-alpine`.
- [ ] Pin the Laya model revision (`LAYA_REVISION`) so a Hub update cannot change answers silently.
- [ ] Raise `SECURE_HSTS_SECONDS` (3600 now) once HTTPS works in production.
<!--- [ ] Back up the `pgdata` volume.-->
- [ ] Run `clearsessions` on a schedule; expired sessions are never deleted.
- [ ] Add `prefetch_related("plugin")` to the user's subscription list (`plugin_name` is one query per row
  when the cache is cold), and a partial index on `Subscription(active=True)` for `poll_inboxes`.
- [ ] Drop `prompt: consent` for returning users; Google shows the consent screen on every sign-in.
- [ ] Version plugin schemas: editing a schema mixes old and new result shapes in `/api/results/`.
<!--- [ ] `PluginViewSet` counts all results per plugin on every request; store a counter if it gets slow.-->
<!--- [ ] Show developers their subscribers and recent results in the dashboard, not just counts.-->
- [ ] Check the dashboard at mobile widths; the one-screen layout is only tuned above 960 × 600.
<!--- [ ] Send results to developers by webhook, and use Gmail push (`users.watch`) instead of polling.-->
