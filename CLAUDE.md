# CLAUDE.md

@AGENTS.md

## Notes for Claude

- Read `TODO.md` before starting work; pick up and update the matching item.
- Check UI changes in a real browser against the built site (`npm run build`), not only `npm run dev`:
  the CSP is enforced only in production.
- Changes to `backend/static/iris.css` reach Docker only after rebuilding the backend image
  (`collectstatic` runs at startup). Frontend changes need the caddy image rebuilt.

## Keep in sync

This file imports `AGENTS.md`. Put shared project rules there, and only Claude-specific notes here.
When you change either file, check the other still agrees in the same change.
