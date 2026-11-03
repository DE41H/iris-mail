# TODO

Priorities: **P0** blocks a real launch · **P1** bug or privacy gap · **P2** should do soon · **P3** nice to have.
Remove an item when it ships; add new findings here instead of in AGENTS.md.

## P0 — launch blockers

- [ ] **Run the full flow against live Google OAuth.** Sign in, add a user with `POST /api/subscriptions/`,
  turn the plugin on, receive mail, fetch `/api/results/`. Nothing past sign-in has run for real.
- [ ] **Google restricted-scope review.** `gmail.readonly` is a restricted scope: public use needs Google's
  OAuth verification plus a CASA security assessment, and a privacy policy and terms page linked from
  the consent screen. Neither page exists yet.
- [ ] **Users cannot find their own user ID.** Developers add users by UUID (`POST /api/subscriptions/`),
  but the UI never shows it, and `/api/users/` lists only users who are already subscribed. Show the ID
  with a copy button on `/subscriptions` (from `/api/me/`), or let developers invite by email.

## P1 — bugs and privacy

- [ ] **A deleted message wipes out a whole poll** (`tasks.process`). `_get_msgs` fetches each message
  inside the same `try`. A message deleted between the history entry and the fetch raises `HttpError`
  404, which is read as "history expired": `hist_id` is reset and every other new message in that batch
  is skipped. Catch the 404 per message and skip only that message; keep the reset for a 404 on
  `history().list`.
- [ ] **Mail received while sharing was off gets shared later** (`tasks.poll_inboxes`, `process`).
  Polling stops when a user has no active subscription, so `hist_id` freezes. Turning a plugin back on
  then processes every message since the freeze. Fix: when `set_active(True)` leaves the user with
  exactly one active subscription, reset `hist_id` to the current Gmail history ID. Or store an
  `activated_at` per subscription and skip messages older than it.
- [ ] **`process` holds a transaction and row lock across network calls and inference.** It is
  `@atomic` with `select_for_update`, then calls Gmail and Laya for every message. A slow batch keeps
  a DB connection and lock open for minutes, and any failure rolls back finished Laya work, so the retry
  runs Laya again (against "no duplicate Laya calls"). Fetch and infer outside the transaction, then
  write results and `hist_id` in a short atomic block, using `bulk_create(ignore_conflicts=True)`.
- [ ] **Polls pile up.** `poll_inboxes` defers `process` for every user every 3 minutes, even if the
  last job is still queued or running. Use `process.configure(queueing_lock=user_id).defer(...)` and
  ignore `AlreadyEnqueued`.
- [ ] **A revoked Google token retries forever.** `google.auth.exceptions.RefreshError` is not caught,
  so the job fails with 3 retries every 3 minutes for good. Catch it, deactivate that user's
  subscriptions (or flag the account), and show "reconnect Google" in the UI.
- [ ] **OAuth tokens are stored in plain text.** `SocialToken.token` and `token_secret` (the refresh
  token, i.e. read access to the inbox) are plain DB columns. Encrypt them at rest with a key from env,
  or at least restrict DB access and backups.
- [ ] **Results are marked fetched before the developer receives them** (`ResultViewSet.paginate_queryset`).
  If the response is lost, those results never show up under `?fetched=false` again. Add an explicit ack
  (`POST /api/results/ack/` with IDs), or mark them on the next request with a cursor.

## P2 — should do soon

- [ ] **The unfetched index does not match the query.** Pagination orders by `-id`, but the partial
  index is `(plugin, -time) WHERE fetched = false`. uuid7 IDs are time-ordered, so change the index to
  `(plugin, -id) WHERE fetched = false`, plus a migration.
- [ ] **HTML-only emails reach Laya with an empty body.** `process` passes `message.plain or ""`. Fall
  back to `message.html` stripped to text, and pass `sender=` to `laya.email_state`.
- [ ] **Batch inference.** Each message is answered one plugin at a time with `laya.decide`. Group the
  messages per plugin and use `laya.decide_batch`.
- [ ] **Laya model weights.** Check whether `laya.Router()` downloads weights on first use; if it does,
  mount a cache volume for the worker or bake the weights into the image, so a restart does not fetch
  them again.
- [ ] **Users cannot leave or delete.** There is no way to remove a subscription, disconnect Gmail
  (revoke the token), or delete the account and its results. Google's user-data policy expects this.
- [ ] **Developer dashboard gaps.** Plugin pages show no subscriber count, no recent results and no API
  reference. Add a short docs page for `POST /api/subscriptions/`, `GET /api/results/` and
  `GET /api/users/`.
- [ ] **Local dev against Docker.** `npm run dev` proxies to `:8000`, but compose does not publish the
  backend port. Add a `docker/*.local.yml` override that publishes 8000, or document running the
  backend with `uv`.
- [ ] **Logging and errors.** There is no `LOGGING` config and no error tracking; task failures only
  reach worker stdout.

## P3 — nice to have

- [ ] Pin `astral/uv` and `node` image versions instead of `latest` / `22-alpine`.
- [ ] Move `django-stubs` to a dev dependency group; replace the placeholder `description` in
  `pyproject.toml`.
- [ ] Raise `SECURE_HSTS_SECONDS` once HTTPS is confirmed in production (it is 3600 now).
- [ ] Add a favicon and an Astro `404.astro`, with Caddy `handle_errors` serving it.
- [ ] Check the dashboard on mobile widths: the one-screen layout only applies above 960 × 600.
- [ ] Filter `/api/results/` by user, and send results to developers by webhook instead of polling.
- [ ] Use Gmail push notifications (`users.watch` + Pub/Sub) instead of polling every inbox every 3 minutes.
- [ ] Postgres backups for the `pgdata` volume.
