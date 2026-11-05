<script lang="ts">
  import { tick } from 'svelte';
  import { flip } from 'svelte/animate';
  import { fly, slide } from 'svelte/transition';
  import { fromSchema, MAX_FIELDS, type Field } from '../lib/schema';
  import { blank, FIELD_PRESETS, KINDS } from '../lib/presets';
  import FieldCard from './FieldCard.svelte';

  let { fields = $bindable() }: { fields: Field[] } = $props();

  let list: HTMLElement;
  let importing = $state(false);
  let pasted = $state('');
  let importError = $state('');
  const full = $derived(fields.length >= MAX_FIELDS);
  const unused = $derived(FIELD_PRESETS.filter((p) => !fields.some((f) => f.name === p.name)));

  async function add(field: Field, at = fields.length) {
    if (full) return;
    fields.splice(at, 0, field);
    await tick();
    const card = list.querySelectorAll('article')[at];
    card?.querySelector<HTMLInputElement>('input[type="text"]')?.focus({ preventScroll: true });
    card?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function move(i: number, by: number) {
    const [f] = fields.splice(i, 1);
    fields.splice(i + by, 0, f);
  }

  const duplicate = (i: number) => add({ ...$state.snapshot(fields[i]), name: `${fields[i].name}_copy` }, i + 1);

  function preset(e: Event) {
    const select = e.currentTarget as HTMLSelectElement;
    const found = FIELD_PRESETS.find((p) => p.name === select.value);
    if (found) add(structuredClone(found));
    select.value = '';
  }

  function load() {
    try {
      const parsed = fromSchema(JSON.parse(pasted));
      if ('error' in parsed) throw new Error(parsed.error);
      fields = parsed.fields.slice(0, MAX_FIELDS);
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
      <div animate:flip={{ duration: 260 }} in:fly={{ y: 16, duration: 280 }} out:fly={{ x: -24, duration: 180 }}>
        <FieldCard
          bind:field={fields[i]}
          {fields}
          index={i}
          onmove={(by) => move(i, by)}
          onduplicate={() => duplicate(i)}
          onremove={() => fields.splice(i, 1)}
        />
      </div>
    {/each}
  </div>

  <div class="add" class:first={!fields.length}>
    <span class="label">{fields.length ? 'Add another question' : 'Add your first question'}</span>
    <div class="kinds">
      {#each KINDS as k}
        <button type="button" class="kind" disabled={full} onclick={() => add(blank(k.kind))}>
          <i aria-hidden="true">{k.icon}</i>
          <b>{k.label}</b>
          <span>{k.note}</span>
        </button>
      {/each}
    </div>
    <div class="more">
      <select disabled={full || !unused.length} onchange={preset} aria-label="Add a ready-made question">
        <option value="">Or pick a ready-made question…</option>
        {#each KINDS as k}
          <optgroup label={k.label}>
            {#each unused.filter((p) => p.kind === k.kind) as p}<option value={p.name}>{p.question}</option>{/each}
          </optgroup>
        {/each}
      </select>
      <button type="button" class="link" aria-expanded={importing} onclick={() => (importing = !importing)}>Paste a JSON schema</button>
    </div>
    {#if full}<span class="help warn">That is the most questions a plugin can have.</span>{/if}
    {#if importing}
      <div class="import" transition:slide={{ duration: 200 }}>
        <textarea class="mono" rows="6" bind:value={pasted} placeholder={'{ "type": "object", "properties": { … } }'} aria-label="JSON schema to import"></textarea>
        {#if importError}<div class="error">{importError}</div>{/if}
        <div class="actions">
          <span class="help">This replaces every question above.</span>
          <button type="button" class="btn btn-sm btn-primary" disabled={!pasted.trim()} onclick={load}>Import</button>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .builder, .add { display: grid; grid-template-columns: minmax(0, 1fr); gap: 14px; }
  .list { display: grid; grid-template-columns: minmax(0, 1fr); gap: 12px; }
  .list:empty { display: none; }
  .add { gap: 10px; }
  .add .label { margin: 0; }
  .kinds { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
  .kind {
    display: grid;
    grid-template-columns: auto 1fr;
    align-items: baseline;
    column-gap: 8px;
    padding: 12px 14px;
    text-align: left;
    border: 1px dashed var(--border-strong);
    border-radius: var(--radius-sm);
    background: transparent;
    color: var(--text);
    font: inherit;
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s, translate 0.3s var(--spring);
  }
  .kind i { font-style: normal; color: var(--accent); }
  .kind b { font-size: 14px; font-weight: 600; }
  .kind span { grid-column: 2; font-size: 12.5px; color: var(--muted); line-height: 1.35; }
  .kind:hover:not(:disabled) { border-style: solid; border-color: var(--accent); background: var(--accent-soft); translate: 0 -2px; }
  .kind:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .kind:disabled { opacity: 0.5; cursor: not-allowed; }
  .first .kind { padding-block: 16px; }
  .more { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
  .more select { flex: 1 1 220px; min-width: 0; width: auto; font-size: 13.5px; }
  .link { border: 0; background: none; padding: 0; font: 540 13px var(--font); color: var(--accent); cursor: pointer; }
  .link:hover { text-decoration: underline; text-underline-offset: 3px; }
  .warn { color: var(--signal-text); margin: 0; }
  .import { display: grid; gap: 8px; }
  .import .actions { justify-content: space-between; }
  @media (max-width: 640px) { .kinds { grid-template-columns: minmax(0, 1fr); } }
</style>
