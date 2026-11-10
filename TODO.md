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

_None._

## P2: should do soon

- **`revive` can run two `process` jobs for one user.** Retrying a stalled job frees its lock while a hung worker may
  still run it: double LLM calls and usage (results dedupe). Accept, or check `hist_id` before `_guess`.

## P3: nice to have

_None._
