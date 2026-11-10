# TODO

Each item says what is wrong, where, and the fix. Remove it when it ships.

| Priority | Meaning                       |
| -------- | ----------------------------- |
| **P0**   | blocks launch                 |
| **P1**   | bug, security or privacy gap  |
| **P2**   | should do soon                |
| **P3**   | nice to have                  |

## P0: launch blockers

_None._

## P1: bugs, security and privacy

- **`process` crashes forever when the Google token is gone.** `gmail.client` raises `SocialToken.DoesNotExist`,
  which nothing catches. This happens when `SocialAdapter.pre_social_login` deletes the token and the user leaves the
  consent page, or when `Code.accept` turns a sub on with no token (it skips the check in `set_active`). `poll_hist`
  keys on `SocialAccount`, so it fails every 3 min. Fix: treat `DoesNotExist` in `process` like a revoke (`disconnect`).
- **Stale subs during a long `process` run.** `subs` is loaded once. A sub turned off or removed mid-run still gets
  LLM calls, usage charges and `Result` rows (until the 30-day cleanup). Fix: re-read active sub ids per chunk.

## P2: should do soon

- **`disconnect` can delete a fresh token.** If the user signs in again between the failed Gmail call and
  `disconnect`, the new token is deleted and all plugins turn off. Fix: delete only the token row `client` loaded (by pk).
- **`revive` can run two `process` jobs for one user.** Retrying a stalled job frees its lock while a hung worker may
  still run it: double LLM calls and usage (results dedupe). Accept, or check `hist_id` before `_guess`.
- **Plugin version bump is read-modify-write** (`PluginSerializer.update`). Two edits at once get the same version
  for different schemas. Fix: `F("version") % 32767 + 1`.
- **Name check then insert** (`PluginSerializer.validate_name`): a concurrent
  duplicate hits the unique constraint and returns 500. `PluginViewSet.create` doesn't catch `IntegrityError`, and
  `create` + `rot_key` aren't atomic. Fix: catch `IntegrityError` → 400, wrap create in `atomic`.
- **`Result.user` has no index.** Deleting an account cascades `DELETE … WHERE user_id = …`, a scan of the largest
  table. Fix: `Index(fields=("user",))` (no index has `user` first).

## P3: nice to have

_None._
