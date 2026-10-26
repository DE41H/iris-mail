# Iris

> Understand any inbox — without ever holding onto the email.

Iris is infrastructure for developers who want to build on top of their users'
inboxes. Instead of asking for mailbox access and then parsing months of mail
yourself, you describe what you're looking for once, and Iris delivers it as
clean, structured data.

---

## The idea

A developer describes the information they need — invoices, shipping updates,
receipts, travel confirmations — as a plugin schema. A user signs in, connects
their inbox, and enables that plugin from their dashboard.

From then on, matching mail is quietly turned into structured results that the
developer pulls with an API key.

The email never stays with Iris. Only the answer does.

## How it works

1. A developer creates a plugin and defines the fields it should extract.
2. Iris issues an API key for that plugin — shown once, stored only as a hash.
3. A user signs in with Google and grants read access to their inbox via OAuth.
4. The user enables the plugin from their dashboard.
5. New mail arrives through Google Pub/Sub.
6. Duplicate messages are dropped before any work is done.
7. A background worker hands the message to Laya, which extracts the fields
   described by the plugin's schema.
8. The structured result is stored. The email is discarded.
9. The developer reads the results with their API key.

## Made for developers

- **Schema, not parsing.** Declare the fields you want; Laya handles the
  messy reality of email.
- **One key per plugin.** Keys are revocable and rotatable at any time.
- **Results, not mailboxes.** Your integration never touches raw email.
- **Any use case.** Finance, logistics, travel, recruiting — the schema
  decides what matters.

## Private by design

- Email contents are never stored.
- Inbox access is granted through OAuth and can be revoked by the user.
- API keys exist in plaintext only once, at creation.
- Users see exactly which plugins are enabled and can turn any of them off.

## Built to keep up

- Emails are deduplicated in Dragonfly before they cost any processing time.
- RabbitMQ and Celery keep ingestion asynchronous and absorb bursts.
- Postgres stores only results, with indexes tuned for "what's new".
- The whole path — Pub/Sub to result — is designed to scale horizontally.

## Stack

| Layer | Technology |
| --- | --- |
| API & dashboard | Django, Django REST Framework |
| Storage | PostgreSQL |
| Queue | RabbitMQ, Celery |
| Deduplication | Dragonfly |
| Inbox events | Google Pub/Sub |
| Authorization | Google OAuth |
| Extraction | Laya |

## Status

Iris is in early development. The data model and plugin authentication are in
place; the ingestion pipeline and public API are being built.
