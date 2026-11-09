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

- **Replace local Laya with hosted LLMs behind a LiteLLM router.** The 322M Laya model runs on CPU in the worker
  (`tasks/extract.py`, `mem_limit: 4g`), so it is slow and needs a bigger server than the rest of the stack. Fix:
  in `_decide`, call a LiteLLM `Router` (library, no proxy) whose `model_list` is built from `CLAUDE_KEYS` and
  `GEMINI_KEYS` (comma lists in env): pool `claude` (`claude-haiku-5-5`, low effort) with fallback to pool
  `gemini`, plugin schema as JSON-schema output. Cut bodies to a fixed length to bound cost. Replace
  `plan_from_json_schema` in `validation.py` (and `schema.ts`) with checks for the schema subset both providers
  accept. Drop `laya`/torch, the model preload, the `models` volume and `mem_limit`. Add the env vars to
  `.env.example` and update AGENTS.md. Only paid-tier keys (Gmail Limited Use forbids providers that train on mail),
  never multiple free accounts. Message Batches (50% off, up to 24h) later, only if cost matters.

## P3: nice to have

- **"Connect with Iris" consent flow (like Stripe Connect).** Right now users subscribe on Iris itself, and a
  developer's app can't send them there. Fix: the developer's app redirects the user to an Iris consent page
  (plugin id, `redirect_uri`, `state`). The page shows the plugin's questions and has Allow/Deny. On Allow it
  signs in with Google if needed, creates the `Subscription` and redirects back with `state`. Register
  `redirect_uri`s on `Plugin` and only accept exact matches.
