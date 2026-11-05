# TODO

**P0** blocks launch · **P1** bug, security or privacy gap · **P2** should do soon · **P3** nice to have.
Each item says what is wrong, where, and the fix. Remove an item when it ships.

## P0: launch blockers

## P1: bugs, security and privacy

- **One bad message stalls a user's mail forever.** Any exception while fetching or answering a single message fails
  the whole `process` job (`plugins/tasks/extract.py`, `plugins/gmail.py:get`). `hist_id` does not move, so every poll
  re-fetches the same batch and fails again, and no newer mail for that user is ever processed. Reproduced:
  simplegmail's `_evaluate_message_payload` raises `LookupError` for `charset=unknown-8bit` (seen in real spam). Laya
  errors other than `SchemaError` would do the same. Fix: in `get`, catch non-`HttpError` exceptions, log the message
  id and skip it; in `_guess`, catch Laya failures per plugin so one plugin can't block the others.

## P2: should do soon

- **A permanent Gmail API error fails every poll forever.** In `process`, any `HttpError` other than 404 is re-raised
  (`get_hist`, and `fetch` for non-404). A 401/403 (Gmail API disabled for the project, scope removed) then fails
  every 3 minutes with no disconnect and no message to the user. Not reproduced. Fix: treat 401/403 like a
  non-retryable `RefreshError` and call `disconnect(user)`.

## P3: nice to have
