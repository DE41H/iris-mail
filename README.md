# Iris

> Understand any inbox without ever holding onto the email.

Developers describe the information they want from email (invoices, shipping updates, receipts) as a
plugin. Users connect Gmail and turn the plugin on. Iris turns matching mail into structured answers
that the developer pulls with an API key. The email is never stored, only the answer and short rule matches.

## How it works

1. A developer creates a plugin in the dashboard and gets an API key (shown once, stored as a hash).
2. A user signs in with Google, granting read access to their inbox.
3. The developer adds the user by email or id with `POST /api/subscriptions/` (by email it always answers 202, so
   accounts can't be probed). The user turns it on
   from the subscriptions page.
4. Every three minutes Iris polls new mail. Laya answers the plugin's questions once per message.
5. The developer reads `GET /api/results/?fetched=false` and confirms receipt with
   `POST /api/results/ack/`. Anything not acknowledged is sent again.

The full API reference is at `/docs`.

## Privacy

- Whole emails are never stored. Developers get only the answers and short rule matches, plus each subscriber's email and username.
- Users can turn a plugin off, remove it, or delete their account. Deleting revokes Google access
  and removes everything Iris holds about them.
- If a user revokes Google access, Iris turns all their plugins off until they sign in again.
- Answers older than 30 days are deleted once acknowledged, or once the plugin is removed. Every answer
  is deleted after 100 days, acknowledged or not.
- Developers can remove a user by email or id with `POST /api/subscriptions/remove/` and list active
  subscribers with `GET /api/users/`.

## Stack

Django + DRF, PostgreSQL, Procrastinate, Valkey, Gmail API, Laya, Astro + Svelte, Caddy, Docker.
Contributor notes are in `AGENTS.md`.

## Running

    cp docker/.env.example docker/.env    # fill in the secrets
    cd docker && docker compose up -d --build

## Status

Early development. Everything runs in Docker, but the full flow has not yet been tested against live
Google OAuth. See `TODO.md`.
