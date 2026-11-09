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

_None._

## P3: nice to have

- **"Connect with Iris" consent flow (like Stripe Connect).** Right now users subscribe on Iris itself, and a
  developer's app can't send them there. Fix: the developer's app redirects the user to an Iris consent page
  (plugin id, `redirect_uri`, `state`). The page shows the plugin's questions and has Allow/Deny. On Allow it
  signs in with Google if needed, creates the `Subscription` and redirects back with `state`. Register
  `redirect_uri`s on `Plugin` and only accept exact matches.
