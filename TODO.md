# TODO

**P0** blocks launch · **P1** bug, security or privacy gap · **P2** should do soon · **P3** nice to have.
Each item says what is wrong, where, and the fix. Remove an item when it ships.

## P0: launch blockers

## P1: bugs, security and privacy


## P2: should do soon

## P3: nice to have

- Plugin card to detail page: add a cross-document view transition that morphs the card name into the page heading. It needs the detail
  heading rendered before first paint (it is `client:only` today), so the morph has nothing to land on. Fix: render the name in the
  `.astro` page from the query string, or hold render with `<link rel="expect" blocking="render">`.
- Dark mode consent panel (`SubscriptionRow.svelte` `.consent`) reads brownish: saffron over indigo. Try an accent-tinted panel with a saffron edge.
- Chrome lets a second Escape close a `<dialog>` even when `cancel` is prevented. The key dialog in `PluginDetail.svelte` can still be
  dismissed that way; the key is then gone and has to be rotated again.

