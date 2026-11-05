# Iris

> Understand any inbox without ever holding onto the email.

Developers describe what they want from email (invoices, shipping updates, receipts) as a **plugin**. Users connect
Gmail and turn the plugin on. Iris turns matching mail into structured answers that the developer pulls with an API
key. Only the answers and short rule matches are stored, never the email.

## How it works

1. A developer creates a plugin in the dashboard and gets an API key (shown once, stored as a hash).
2. A user signs in with Google, granting read access to their inbox.
3. The developer adds the user with `POST /api/subscriptions/`, by email or id. By email it always answers `202`, so
   accounts can't be probed. The user turns the plugin on from the subscriptions page.
4. Every 3 minutes Iris polls new mail, and Laya answers the plugin's questions once per message.
5. The developer reads `GET /api/results/?fetched=false` and confirms receipt with `POST /api/results/ack/`.
   Anything not acknowledged is sent again.

Full API reference: `/docs`.

## Privacy

- Whole emails are never stored. Developers get only answers, short rule matches, and each subscriber's email and
  username.
- Users can turn a plugin off, remove it, or delete their account. Deleting revokes Google access and removes
  everything Iris holds about them.
- If a user revokes Google access, all their plugins turn off until they sign in again.
- Answers are deleted 30 days after being acknowledged or after the plugin is removed, and always after 100 days.
- Developers list active subscribers with `GET /api/users/` and remove one by email or id with
  `POST /api/subscriptions/remove/`.

## Running

```bash
cp docker/.env.example docker/.env    # fill in the secrets
cd docker && docker compose up -d --build
```

Stack: Django + DRF, PostgreSQL, Procrastinate, Valkey, Gmail API, Laya, Astro + Svelte, Caddy, Docker.
Contributor notes are in [`AGENTS.md`](AGENTS.md).

## Status

Early development. Everything runs in Docker, but the full flow is untested against live Google OAuth.
Open work is in [`TODO.md`](TODO.md).

## Known drawbacks

- **Laya answers are not always right.** It can misread Hindi mail and gets number ranges wrong (Rs. 52,000 and
  Rs. 1,499 both came back as `100_to_1000`). Rules are reliable: pull numbers out with a rule and bucket them
  yourself.
- **Some mail is skipped for good.** An email Gmail's parser can't read (e.g. `charset=unknown-8bit` spam) is
  skipped. If Laya fails on a batch, that plugin gets no answers for those messages. Both are logged.
- **Dashboard counts lag by up to 5 minutes.** They are cached to keep load off the database.
- **Sessions can be evicted.** Sessions live in Valkey; under memory pressure some users are logged out and sign in
  again with Google. Mail polling is unaffected.
