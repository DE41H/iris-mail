<script lang="ts">
  import { tick } from 'svelte';
  import { flip } from 'svelte/animate';
  import { fly, slide } from 'svelte/transition';
  import { fromSchema, MAX_FIELDS, type Field } from '../lib/schema';
  import { blank, KINDS } from '../lib/presets';
  import FieldCard from './FieldCard.svelte';

  let { fields = $bindable() }: { fields: Field[] } = $props();

  let list: HTMLElement;
  let importing = $state(false);
  let pasted = $state('');
  let importError = $state('');
  // Only one question is open for editing; the rest stay one line each so the list is easy to scan.
  // An empty list starts nothing open; a new or clicked question opens.
  let active = $state<Field | null>(null);
  const full = $derived(fields.length >= MAX_FIELDS);

  async function add(field: Field, at = fields.length) {
    if (full) return;
    fields.splice(at, 0, field);
    active = fields[at];
    await tick();
    const card = list.querySelectorAll('article')[at];
    card?.querySelector<HTMLInputElement>('input[type="text"]')?.focus({ preventScroll: true });
    card?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function move(i: number, by: number) {
    const [f] = fields.splice(i, 1);
    fields.splice(i + by, 0, f);
  }

  const duplicate = (i: number) => add({ ...$state.snapshot(fields[i]), name: `${fields[i].name}_copy` }, i + 1);

  function load() {
    try {
      const parsed = fromSchema(JSON.parse(pasted));
      if ('error' in parsed) throw new Error(parsed.error);
      fields = parsed.fields.slice(0, MAX_FIELDS);
      active = null;
      importing = false;
      pasted = importError = '';
    } catch (err) {
      importError = err instanceof SyntaxError ? 'That is not valid JSON.' : (err as Error).message;
    }
  }
</script>

<div class="builder">
  <div class="list" bind:this={list}>
    {#each fields as field, i (field)}
      <div animate:flip={{ duration: 260 }} in:fly={{ y: 12, duration: 240 }} out:fly={{ x: -24, duration: 180 }}>
        <FieldCard
          bind:field={fields[i]}
          {fields}
          index={i}
          open={active === field}
          onopen={() => (active = field)}
          onmove={(by) => move(i, by)}
          onduplicate={() => duplicate(i)}
          onremove={() => fields.splice(i, 1)}
        />
      </div>
    {/each}
  </div>

  <div class="add" class:first={!fields.length}>
    <div class="kinds" role="group" aria-label="Add a question">
      <span class="label">{fields.length ? 'Add' : 'Add your first question'}</span>
      {#each KINDS as k}
        <button type="button" class="add-pill" disabled={full} title={k.note} onclick={() => add(blank(k.kind))}>
          <i aria-hidden="true">{k.icon}</i>{k.label}
        </button>
      {/each}
      <button type="button" class="text-btn paste" aria-expanded={importing} title="Paste JSON schema" aria-label="Paste JSON schema" onclick={() => (importing = !importing)}><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="4" width="14" height="17" rx="2" /><path d="M9 4V3h6v1M9 10h6M9 14h6" /></svg></button>
    </div>


    {#if full}<span class="help warn">That is the most questions a plugin can have.</span>{/if}
    {#if importing}
      <div class="import" transition:slide={{ duration: 200 }}>
        <textarea class="mono" rows="6" bind:value={pasted} placeholder={'{ "type": "object", "properties": { … } }'} aria-label="JSON schema to import"></textarea>
        {#if importError}<div class="error">{importError}</div>{/if}
        <div class="actions">
          <button type="button" class="btn btn-sm btn-primary" disabled={!pasted.trim()} onclick={load}>Import</button>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .builder { display: grid; grid-template-columns: minmax(0, 1fr); gap: 14px; }
  .list { container-type: inline-size; display: grid; grid-template-columns: minmax(0, 1fr); gap: 2px; margin: 0 -10px; }
  .list:empty { display: none; }
  .add { display: grid; gap: 10px; }
  .label { margin: 0 4px 0 0; font-size: 13px; }
  .kinds { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
  .first .add-pill { padding: 9px 18px; }
  .text-btn { margin-left: auto; }
  .warn { color: var(--signal-text); margin: 0; }
  .import { display: grid; gap: 8px; }
  .import textarea { min-height: 140px; }
  .import .actions { justify-content: flex-end; }
  .paste { display: grid; place-items: center; padding: 4px; }
  .paste svg { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
</style>
