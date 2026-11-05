<script lang="ts">
  import { toQuestions, toSchema, type Field, type Rule } from '../lib/schema';
  import CopyButton from './CopyButton.svelte';
  import Json from './Json.svelte';

  let { fields, rules }: { fields: Field[]; rules: Rule[] } = $props();

  const TABS = ['schema', 'laya', 'result'] as const;
  let tab = $state<(typeof TABS)[number]>('schema');

  const example = (f: Field) => (f.kind === 'boolean' ? true : f.kind === 'scale' ? f.min : (f.options[0] ?? null));
  const value = $derived(
    tab === 'schema' ? toSchema(fields) : tab === 'laya' ? toQuestions(fields) : { output: { ...Object.fromEntries(fields.map((f) => [f.name, example(f)])), ...(rules.length ? { rules: Object.fromEntries(rules.map((r) => [r.name, ['…']])) } : {}) } },
  );
</script>

<section class="card preview">
  <div class="tabs" role="tablist">
    {#each TABS as t}
      <button type="button" role="tab" aria-selected={tab === t} onclick={() => (tab = t)}>{t === 'laya' ? 'Laya' : t[0].toUpperCase() + t.slice(1)}</button>
    {/each}
    <span class="live" title="Updates as you type">Live</span>
  </div>
  <Json {value} />
  <div class="foot"><CopyButton text={JSON.stringify(value, null, 2)} label="Copy JSON" /></div>
</section>

<style>
  .preview { overflow: hidden; flex: 1; display: flex; flex-direction: column; min-height: 0; }
  .tabs { display: flex; align-items: center; border-bottom: 1px solid var(--border); padding: 0 8px; }
  .tabs button {
    position: relative;
    padding: 10px;
    white-space: nowrap;
    border: 0;
    background: none;
    color: var(--muted);
    font: 540 13px var(--font);
    cursor: pointer;
    transition: color 0.2s;
  }
  .tabs button:hover { color: var(--text); }
  .tabs button[aria-selected='true'] { color: var(--accent); }
  .tabs button[aria-selected='true']::after {
    content: '';
    position: absolute;
    left: 8px;
    right: 8px;
    bottom: -1px;
    height: 2px;
    border-radius: 2px;
    background: var(--accent);
    animation: grow 0.35s var(--spring);
  }
  @keyframes grow { from { transform: scaleX(0); } }
  .live { margin-left: auto; font-size: 12px; color: var(--muted); display: inline-flex; align-items: center; gap: 6px; }
  .live::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: var(--accent); }
  .preview :global(pre) { flex: 1; min-height: 0; background: transparent; }
  .foot { display: flex; justify-content: flex-end; padding: 0 12px 12px; }
</style>
