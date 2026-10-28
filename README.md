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

1. A developer creates a plugin and defines the fields it should extract. Each
   field is a choice, a yes/no, or a scale, and the builder writes the schema
   Laya expects.
2. Iris issues an API key for that plugin — shown once, stored only as a hash.
3. A user signs in with Google and grants read access to their inbox via OAuth.
4. Once a user has signed in, the developer adds them to the plugin. The
   subscription starts off; the user turns it on from the subscriptions page,
   after a prompt warning that extracted data goes to the developer.
5. Iris checks each subscribed user's inbox for new mail every three minutes.
6. A message already stored for that user and plugin is skipped, so Laya never
   runs twice on it.
7. A background worker hands the message to Laya, which extracts the fields
   described by the plugin's schema.
8. The structured result is stored. The email is discarded.
9. The developer reads the results with their API key. Results are marked as
   fetched once they are read.

## Made for developers

- **Schema, not parsing.** Declare the fields you want; Laya handles the
  messy reality of email.
- **One key per plugin.** Keys are revocable and rotatable at any time.
- **Results, not mailboxes.** Your integration never touches raw email.
- **Any use case.** Finance, logistics, travel, recruiting — the schema
  decides what matters.

## Private by design

- Email contents are never stored.
- Developers see the email address and username of each user subscribed to
  their plugin, so they can find the user they want to add. Extracted results
  are the only mail-derived data they receive.
- Inbox access is granted through OAuth and can be revoked by the user.
- API keys exist in plaintext only once, at creation.
- Users see exactly which plugins are enabled and can turn any of them off.

## Built to keep up

- Each result is unique per user, message and plugin, so a duplicate message
  is never extracted twice.
- Procrastinate keeps ingestion asynchronous and absorbs bursts.
- Postgres stores only results, with indexes tuned for "what's new".
- The whole path — poll to result — is designed to scale horizontally.

## Stack

| Layer | Technology |
| --- | --- |
| Deployment | Docker |
| API & dashboard | Django, Django REST Framework |
| Storage | PostgreSQL |
| Background tasks | Procrastinate |
| Cache | Valkey |
| Inbox polling | Gmail API (history) |
| Frontend | Astro, TypeScript |
| Authorization | Google OAuth |
| Extraction | Laya |

## Status

Iris is in early development. The plugin API and dashboard, the subscriptions
page, and the ingestion pipeline are in place. The Docker files are written but
have not been run end to end. Still to do: server-side schema validation and
finding users by email or username.
