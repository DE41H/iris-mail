<div align="center">

<img src="backend/static/favicon.svg" width="88" alt="Iris logo">

# Iris

**Ask inboxes questions. Get JSON back.**

Write a few questions about email. People connect Gmail and switch you on.<br>
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
  "rules": { "amount": ["$12.00"] }
}
```

## How it works

| | |
| :-- | :-- |
| **1. Write your questions** | Yes/no, a choice (one or several), a scale, a number or a date, any of which can be unknown, plus optional regex rules. You get an API key. |
| **2. People switch you on** | They sign in with Google and opt in, one plugin at a time. |
| **3. Fetch the answers** | New mail is read every 3 minutes. Pull results as JSON and acknowledge them. |

Questions are answered by an LLM (Gemini Flash models, with Claude Haiku as the last fallback). Rules pull exact text, like an amount or a tracking number, and land under `output.rules`.

## For developers

Build a plugin in the dashboard at `/plugins/new`, or start from a template:
**Spending**, **Deliveries**, **Bills**, **Travel**, **Meetings**, **Security alerts**, **Job hunt**, **Newsletters**,
**Appointments**, **Support triage**, **Inbox priority**.

Then three calls:

```bash
H=(-H "Authorization: Bearer $KEY" -H "Content-Type: application/json")

# 1. Add a user. They still switch the plugin on themselves.
curl "${H[@]}" -X POST $IRIS/api/subscriptions/ -d '{"email": "ada@example.com"}'

# 2. Read new answers
curl "${H[@]}" "$IRIS/api/results/?fetched=false"

# 3. Acknowledge them, or they come back next time
curl "${H[@]}" -X POST $IRIS/api/results/ack/ -d '{"ids": ["…"]}'
```

Adding by email always returns `202`, so accounts can't be probed. The full reference lives at `/docs`.

<details>
<summary><b>Limits</b></summary>

<br>

| | |
| :-- | :-- |
| Questions per plugin | 32 |
| Answers per choice or multi-select | 32 |
| Steps on a scale | 10 |
| Rules per plugin | 16, RE2 syntax, first capture group kept |
| API rate | 500 to 5,000 requests per hour, by tier |

</details>

## Privacy

- **No email is stored.** Developers get answers, short rule matches, and each subscriber's email and username.
- **Opt-in, per plugin.** Users turn each plugin on or off, or delete their account, which revokes Google access and
  erases everything.
- **Answers expire.** 30 days after they are acknowledged or the plugin is removed, and always after 100 days.
- **Keys and tokens are protected.** API keys are stored as SHA-256 hashes and shown once. Google tokens are encrypted.

## Self-host

```bash
cp docker/.env.example docker/.env   # add Google OAuth and the secrets
docker/deploy.sh
```

Then open `https://localhost`. Deploys roll out with no downtime and need the
[docker-rollout](https://github.com/wowu/docker-rollout) plugin.

<sub>Django · DRF · PostgreSQL · Procrastinate · Valkey · Astro · Svelte · Caddy · Docker</sub>

## Good to know

Iris is in early development.

- The LLM can be wrong. Rules are exact, so use a rule for numbers and
  bucket them yourself.
- Mail Gmail can't parse is skipped, and if the LLM fails on an email it gets no answers. Both are logged.

Contributors: start with [`AGENTS.md`](AGENTS.md) and [`TODO.md`](TODO.md).

<div align="center"><sub>Licensed under <a href="LICENSE.md">GPL-3.0</a></sub></div>
