<script lang="ts">
  import { tick } from 'svelte';
  import { KINDS, type Field } from '../lib/schema';

  interface Props {
    value: Field['kind'];
    label: string;
    onchange: (kind: Field['kind']) => void;
  }

  let { value, label, onchange }: Props = $props();

  // A native popover: light dismiss, top layer (never clipped by the scrolling editor), anchored to its button.
  const id = $props.id();
  const anchor = `--kind-${id}`;
  let trigger = $state<HTMLButtonElement>();
  let list = $state<HTMLElement>();
  let open = $state(false);
  let active = $state(0);
  let typed = '';
  let typedAt = 0;

  const current = $derived(KINDS.find((k) => k.kind === value) ?? KINDS[0]);
  const groups = [...new Set(KINDS.map((k) => k.group))].map((name) => ({
    name,
    items: KINDS.map((k, i) => ({ ...k, i })).filter((k) => k.group === name),
  }));

  async function toggled(e: ToggleEvent) {
    open = e.newState === 'open';
    if (!open) return;
    active = KINDS.indexOf(current);
    await tick();
    list?.focus();
    list?.querySelector('[data-active]')?.scrollIntoView({ block: 'nearest' });
  }

  function close() {
    list?.hidePopover();
    trigger?.focus();
  }

  function pick(i: number) {
    if (KINDS[i].kind !== value) onchange(KINDS[i].kind);
    close();
  }

  async function move(i: number) {
    active = Math.max(0, Math.min(KINDS.length - 1, i));
    await tick();
    list?.querySelector('[data-active]')?.scrollIntoView({ block: 'nearest' });
  }

  // Type-ahead: letters typed within half a second build one prefix, like a native select.
  function seek(char: string) {
    const now = performance.now();
    typed = now - typedAt < 500 ? typed + char : char;
    typedAt = now;
    const from = typed.length > 1 ? active : active + 1;
    const order = [...KINDS.keys()].map((n) => (from + n) % KINDS.length);
    const hit = order.find((n) => KINDS[n].label.toLowerCase().startsWith(typed.toLowerCase()));
    if (hit !== undefined) move(hit);
  }

  function keys(e: KeyboardEvent) {
    const actions: Record<string, () => void> = {
      ArrowDown: () => move(active + 1),
      ArrowUp: () => move(active - 1),
      Home: () => move(0),
      End: () => move(KINDS.length - 1),
      PageDown: () => move(active + 5),
      PageUp: () => move(active - 5),
      Enter: () => pick(active),
      ' ': () => (typed && performance.now() - typedAt < 500 ? seek(' ') : pick(active)),
      Escape: close,
      Tab: close,
    };
    if (actions[e.key]) {
      if (e.key !== 'Tab') e.preventDefault();
      actions[e.key]();
    } else if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
      seek(e.key);
    }
  }

  // Arrow keys on the closed button open the list, as they do on a native select.
  function triggerKeys(e: KeyboardEvent) {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      list?.showPopover();
    }
  }
</script>

<div class="picker">
  <button
    bind:this={trigger}
    type="button"
    class="trigger"
    style:anchor-name={anchor}
    popovertarget={`${id}-list`}
    aria-haspopup="listbox"
    aria-expanded={open}
    aria-label={`${label}: ${current.label}`}
    onkeydown={triggerKeys}
  >
    <i aria-hidden="true">{current.icon}</i>
    <span>{current.label}</span>
    <svg class="caret" class:up={open} viewBox="0 0 10 6" aria-hidden="true"><path d="M1 1l4 4 4-4" /></svg>
  </button>
  <span class="note">{current.note}</span>

  <div
    bind:this={list}
    id={`${id}-list`}
    class="list"
    style:position-anchor={anchor}
    popover="auto"
    role="listbox"
    tabindex="-1"
    aria-label={label}
    aria-activedescendant={`${id}-${active}`}
    ontoggle={toggled}
    onkeydown={keys}
  >
    {#each groups as group}
      <div class="group" role="group" aria-labelledby={`${id}-${group.name}`}>
        <div class="heading" id={`${id}-${group.name}`}>{group.name}</div>
        {#each group.items as k (k.kind)}
          <!-- Keyboard is handled on the listbox through aria-activedescendant, as the ARIA listbox pattern does. -->
          <!-- svelte-ignore a11y_click_events_have_key_events -->
          <div
            id={`${id}-${k.i}`}
            class="option"
            role="option"
            tabindex="-1"
            aria-selected={k.kind === value}
            data-active={k.i === active || undefined}
            onclick={() => pick(k.i)}
            onpointermove={() => (active = k.i)}
          >
            <i aria-hidden="true">{k.icon}</i>
            <b>{k.label}</b>
            <span>{k.note}</span>
            <svg class="check" viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7" /></svg>
          </div>
        {/each}
      </div>
    {/each}
  </div>
</div>

<style>
  .picker { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; min-width: 0; }

  .trigger {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 5px 10px 5px 12px;
    border: 1px solid color-mix(in oklab, var(--accent) 22%, var(--border));
    border-radius: 999px;
    background: var(--accent-soft);
    color: var(--accent);
    font: 560 13.5px var(--font);
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s;
  }
  .trigger:hover, .trigger[aria-expanded='true'] { border-color: var(--accent); background: color-mix(in oklab, var(--accent) 14%, transparent); }
  .trigger:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .trigger i { width: 14px; font-style: normal; text-align: center; }
  .caret { width: 10px; height: 6px; margin-left: 2px; fill: none; stroke: currentColor; stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; transition: rotate 0.3s var(--spring); }
  .caret.up { rotate: 180deg; }
  .note { min-width: 0; font-size: 13px; color: var(--muted); }

  .list {
    position-area: block-end span-inline-end;
    position-try-fallbacks: flip-block, flip-inline, flip-block flip-inline;
    inset: auto;
    margin: 6px 0;
    width: min(360px, calc(100vw - 32px));
    max-height: min(400px, 60dvh);
    overflow: auto;
    overscroll-behavior: contain;
    padding: 6px;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--surface);
    color: var(--text);
    box-shadow: var(--shadow-lift);
    opacity: 1;
    translate: 0 0;
    transition: opacity 0.15s, translate 0.25s var(--ease), display 0.25s allow-discrete, overlay 0.25s allow-discrete;
  }
  .list:not(:popover-open) { opacity: 0; translate: 0 -4px; }
  @starting-style {
    .list:popover-open { opacity: 0; translate: 0 -4px; }
  }
  .list:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  /* Without anchor positioning, centre the list like a dialog instead of pinning it to the corner. */
  @supports not (anchor-name: --a) {
    .list { inset: 0; margin: auto; height: fit-content; }
  }

  .group + .group { margin-top: 4px; padding-top: 4px; border-top: 1px solid var(--border); }
  .heading { padding: 6px 10px 4px; font-size: 12px; font-weight: 600; color: var(--faint); }

  .option {
    display: grid;
    grid-template-columns: 20px auto minmax(0, 1fr) 14px;
    align-items: baseline;
    gap: 8px;
    padding: 7px 10px;
    border-radius: 8px;
    font-size: 13.5px;
    cursor: pointer;
  }
  .option[data-active] { background: var(--accent-soft); }
  .option i { font-style: normal; text-align: center; color: var(--accent); }
  .option b { font-weight: 560; white-space: nowrap; }
  .option span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 12.5px; color: var(--muted); }
  .check { align-self: center; width: 14px; height: 14px; fill: none; stroke: var(--accent); stroke-width: 2.2; stroke-linecap: round; stroke-linejoin: round; visibility: hidden; }
  .option[aria-selected='true'] b { color: var(--accent); }
  .option[aria-selected='true'] .check { visibility: visible; }

  @media (forced-colors: active) {
    .option[data-active] { outline: 2px solid Highlight; }
  }
</style>
