<script lang="ts">
  import { tick } from 'svelte';

  let { versions, value = $bindable() }: { versions: string[]; value: string } = $props();

  const id = $props.id();
  let open = $state(false);
  let active = $state(0);
  let root: HTMLDivElement;
  let button: HTMLButtonElement;
  let list: HTMLUListElement;

  async function show() {
    active = Math.max(0, versions.indexOf(value));
    open = true;
    await tick();
    list.focus();
  }

  function close(refocus = true) {
    open = false;
    if (refocus) button.focus();
  }

  function pick(i: number) {
    value = versions[i];
    close();
  }

  // Listbox keys per the WAI-ARIA select-only combobox pattern.
  function onkey(e: KeyboardEvent) {
    const last = versions.length - 1;
    const moves: Record<string, number> = { ArrowDown: Math.min(active + 1, last), ArrowUp: Math.max(active - 1, 0), Home: 0, End: last };
    if (e.key in moves) active = moves[e.key];
    else if (e.key === 'Enter' || e.key === ' ') pick(active);
    else if (e.key === 'Escape') close();
    else if (e.key === 'Tab') return close(false);
    else return;
    e.preventDefault();
  }

  const openKeys = (e: KeyboardEvent) => {
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
    e.preventDefault();
    show();
  };
</script>

<div class="picker" bind:this={root} onfocusout={(e) => open && !root.contains(e.relatedTarget as Node) && close(false)}>
  <button
    bind:this={button}
    type="button"
    class="trigger"
    aria-haspopup="listbox"
    aria-expanded={open}
    aria-controls="{id}-list"
    aria-label="API version {value}"
    onclick={() => (open ? close() : show())}
    onkeydown={openKeys}
  >
    <span>{value}</span>
    <svg class="chev" width="10" height="6" viewBox="0 0 10 6" aria-hidden="true"><path d="M1 1l4 4 4-4" /></svg>
  </button>
  <ul
    bind:this={list}
    id="{id}-list"
    role="listbox"
    tabindex="-1"
    aria-label="API version"
    aria-activedescendant={open ? `${id}-${active}` : undefined}
    class:open
    onkeydown={onkey}
  >
    {#each versions as v, i (v)}
      <!-- svelte-ignore a11y_click_events_have_key_events (keys are handled on the listbox) -->
      <li
        id="{id}-{i}"
        role="option"
        aria-selected={v === value}
        class:active={i === active}
        style:--i={i}
        onpointermove={() => (active = i)}
        onclick={() => pick(i)}
      >
        {v}
      </li>
    {/each}
  </ul>
</div>

<style>
  /* Sits in .page-head, whose `> div` rule would stretch it; stay content-sized and centred on the heading. */
  .picker { position: relative; flex: none; min-width: 0; align-self: center; }

  .trigger {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    height: 40px;
    padding: 0 14px 0 16px;
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-btn);
    corner-shape: squircle;
    background: var(--surface);
    color: var(--text);
    font: 500 14px/1 var(--mono);
    box-shadow: var(--shadow);
    cursor: pointer;
    transition: border-color 0.2s, box-shadow 0.2s, scale 0.2s var(--ease);
    animation: bud 0.7s var(--spring) 0.2s both;
  }
  .trigger:hover { border-color: color-mix(in oklab, var(--accent) 40%, var(--border-strong)); }
  .trigger:active { scale: 0.97; }
  .trigger:focus-visible { outline: none; border-color: var(--accent); box-shadow: 0 0 0 4px var(--accent-soft); }
  .trigger[aria-expanded='true'] { border-color: var(--accent); box-shadow: var(--shadow-lift); }

  .chev { fill: none; stroke: var(--muted); stroke-width: 1.5; transition: rotate 0.4s var(--spring), stroke 0.2s; }
  .trigger[aria-expanded='true'] .chev { rotate: 180deg; stroke: var(--accent); }

  ul {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    z-index: 20;
    min-width: max(100%, 176px);
    margin: 0;
    padding: 6px;
    list-style: none;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    box-shadow: var(--shadow-lift);
    transform-origin: top right;
    opacity: 0;
    visibility: hidden;
    translate: 0 -6px;
    scale: 0.92 0.8;
    transition: opacity 0.16s ease, translate 0.16s var(--ease), scale 0.16s var(--ease), visibility 0s 0.16s;
  }
  ul.open {
    opacity: 1;
    visibility: visible;
    translate: 0;
    scale: 1;
    transition: opacity 0.2s ease, translate 0.45s var(--spring), scale 0.45s var(--spring), visibility 0s;
  }
  ul:focus { outline: none; }
  ul:focus-visible li.active { outline: 2px solid var(--accent); outline-offset: -2px; }

  li {
    padding: 9px 10px;
    border-radius: 7px;
    color: var(--muted);
    font: 500 14px/1.2 var(--mono);
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
  }
  .open li { animation: rise 0.4s var(--ease) both; animation-delay: calc(60ms + var(--i) * 45ms); }
  li[aria-selected='true'] { color: var(--text); }
  li.active { background: var(--accent-soft); color: var(--accent); }

  @keyframes bud { from { opacity: 0; translate: 0 -10px; scale: 0.85; } }
</style>
