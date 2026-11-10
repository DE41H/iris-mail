<div align="center">

<img src="backend/static/favicon.svg" width="88" alt="Iris logo">

# Iris

**Ask inboxes questions. Get JSON back.**

Write a few questions about email. People connect Gmail and accept your plugin.<br>
Every new message is read and answered. You get the answers, never the email.

[How it works](#how-it-works) · [For developers](#for-developers) · [Privacy](#privacy) · [Self-host](#self-host)

</div>

---

## What it looks like

A receipt lands in someone's inbox:

```text
From:    receipts@northwind.example
Subject: Your receipt from Northwind

Pro plan, billed monthly. Renews on the 5th.
Total charged: $12.00
```

Your **Spending** plugin gets this, and the email is dropped:

```json
{
  "receipt": true,
  "spend_category": "software",
  "subscription": true,
  "total": 12,
  "rules": { "amount": ["$12.00"] }
}
```

## How it works

| | |
| :-- | :-- |
| **1. Write your questions** | Yes/no, a choice (one or several), a scale, a count, a number, short text, or a date, time, email, URL and other formats, any of which can be unknown, plus optional regex rules. You get an API key. |
| **2. Send people a connect link** | They sign in with Google, see your questions, and accept or deny. Then they land back on your site. |
| **3. Fetch the answers** | New inbox mail is read every 3 minutes (Spam is skipped). Pull results as JSON and acknowledge them. |

Questions are answered by an LLM (Gemini Flash models, with Claude Haiku as the last fallback). Only the sender, subject and first 4,000 characters are sent. Rules pull exact text, like an amount or a tracking number, and land under `output.rules`.

## For developers

Build a plugin in the dashboard at `/plugins/new`, or start from a template:
**Spending**, **Deliveries**, **Bills**, **Travel**, **Meetings**, **Security alerts**, **Job hunt**, **Newsletters**,
**Appointments**, **Support triage**, **Inbox priority**.

Set a redirect URL (https) on the plugin, then:

```bash
H=(-H "Authorization: Bearer $KEY" -H "Content-Type: application/json")

# 1. Make a connect link and send the user to "url" within 3 minutes.
#    They come back to your redirect URL with ?code=…&status=accepted|denied
curl "${H[@]}" -X POST $IRIS/api/v1/codes/

# 2. See who accepted: {"status": "accepted", "user": "…", "email": "…"}
curl "${H[@]}" $IRIS/api/v1/codes/$CODE/

# 3. Read new answers
curl "${H[@]}" "$IRIS/api/v1/results/?fetched=false"

# 4. Acknowledge them, or they come back next time
curl "${H[@]}" -X POST $IRIS/api/v1/results/ack/ -d '{"ids": ["…"]}'
```

List users with `GET /api/v1/users/` and remove one with `POST /api/v1/subscriptions/remove/` (`user` or `email`,
always `204`, so accounts can't be probed). The full reference lives at `/docs`.

<details>
<summary><b>Limits</b></summary>

<br>

| | |
| :-- | :-- |
| Questions per plugin | 16 |
| Answers per choice or multi-select | 16, up to 50 characters each |
| Steps on a scale | 10 |
| Rules per plugin | 16, RE2 syntax, first capture group kept, 20 matches of 200 characters per email |
| API rate | 1,000 requests per hour per developer |
| Daily answers (emails × questions) | 200, 1,000, 5,000 or 25,000 by tier; mail over the quota is skipped |

</details>

## Privacy

- **No email is stored.** Developers get answers, short rule matches, and each subscriber's email and username.
- **Opt-in, per plugin.** Users accept each plugin, can turn it off at any time, or delete their account, which
  revokes Google access and erases everything.
- **Answers expire.** 30 days after they are acknowledged or the plugin is removed, and always after 100 days.
- **Keys and tokens are protected.** API keys are stored as SHA-256 hashes and shown once. Google tokens are encrypted.

## Self-host

```bash
cp docker/.env.example docker/.env   # add Google OAuth, LLM keys and the secrets
docker/deploy.sh
docker compose -f docker/docker-compose.yml exec backend python manage.py mk_admin   # optional: admin + TOTP QR
```

Then open `https://localhost` (or your `SITE_ADDRESS`). The admin needs a password and a TOTP code. Deploys roll out with no downtime and need the
[docker-rollout](https://github.com/wowu/docker-rollout) plugin.

<sub>Django · DRF · PostgreSQL · Procrastinate · Valkey · LiteLLM · Granian · Astro · Svelte · Caddy · Docker</sub>

## Good to know

Iris is in early development.

- The LLM can be wrong. Rules are exact, so use a rule for numbers and
  bucket them yourself.
- Mail that can't be parsed is skipped, and if the LLM fails on an email it gets no answers. Neither is retried; both
  are logged.

Contributors: start with [`AGENTS.md`](AGENTS.md) and [`TODO.md`](TODO.md).

<div align="center"><sub>Licensed under <a href="LICENSE.md">GPL-3.0</a></sub></div>
