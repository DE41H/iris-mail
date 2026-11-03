<script lang="ts">
  import { tick } from 'svelte';
  import { flip } from 'svelte/animate';
  import { fly, slide } from 'svelte/transition';
  import { fromSchema, MAX_FIELDS, type Field } from '../lib/schema';
  import { blank, clone, FIELD_PRESETS, KINDS } from '../lib/presets';
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
    if (found) add(clone(found));
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
  <div class="toolbar">
    {#each KINDS as k}
      <button type="button" class="btn btn-sm" disabled={full} title={k.note} onclick={() => add(blank(k.kind))}>+ {k.label}</button>
    {/each}
    <select class="mono" disabled={full || !unused.length} onchange={preset} aria-label="Insert a ready-made question">
      <option value="">insert ready-made…</option>
      {#each KINDS as k}
        <optgroup label={k.label}>
          {#each unused.filter((p) => p.kind === k.kind) as p}<option value={p.name}>{p.question}</option>{/each}
        </optgroup>
      {/each}
    </select>
    <button type="button" class="btn btn-sm btn-ghost" aria-expanded={importing} onclick={() => (importing = !importing)}>{'{ }'} paste schema</button>
    <span class="count" class:full>{fields.length}/{MAX_FIELDS}</span>
  </div>

  {#if importing}
    <div class="import" transition:slide={{ duration: 200 }}>
      <textarea class="mono" rows="6" bind:value={pasted} placeholder={'{ "type": "object", "properties": { … } }'} aria-label="JSON schema to import"></textarea>
      {#if importError}<div class="error">{importError}</div>{/if}
      <div class="actions">
        <span class="help">Replaces all questions.</span>
        <button type="button" class="btn btn-sm btn-primary" disabled={!pasted.trim()} onclick={load}>import</button>
      </div>
    </div>
  {/if}

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
    {:else}
      <div class="empty">No questions yet. Add one above.</div>
    {/each}
  </div>
</div>

<style>
  .builder { display: flex; flex-direction: column; gap: 10px; flex: 1; min-height: 0; }
  .toolbar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  .toolbar select { width: auto; max-width: 260px; padding-top: 4px; padding-bottom: 4px; font-size: 12px; }
  .count { margin-left: auto; font: 12px var(--mono); color: var(--muted); }
  .count.full { color: var(--amber); }
  .import { display: grid; gap: 8px; }
  .import .actions { justify-content: space-between; }
  .list { display: grid; align-content: start; gap: 10px; flex: 1; min-height: 0; overflow: auto; padding-right: 2px; }
  .empty { border: 1px dashed var(--border-strong); border-radius: var(--radius); }
</style>
