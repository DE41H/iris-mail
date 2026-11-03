<script lang="ts">
  import { toQuestions, toSchema, type Field } from '../lib/schema';
  import CopyButton from './CopyButton.svelte';
  import Json from './Json.svelte';

  let { fields }: { fields: Field[] } = $props();

  const TABS = [
    ['schema', 'schema.json', 'Saved with the plugin. Laya reads it as a flat JSON Schema.'],
    ['laya', 'laya questions', 'How Laya turns each property into a question.'],
    ['result', 'result shape', 'What one result looks like when you fetch it.'],
  ] as const;
  let tab = $state<(typeof TABS)[number][0]>('schema');

  const example = (f: Field) => (f.kind === 'boolean' ? true : f.kind === 'scale' ? f.min : (f.options[0] ?? null));
  const value = $derived(
    tab === 'schema' ? toSchema(fields) : tab === 'laya' ? toQuestions(fields) : { output: Object.fromEntries(fields.map((f) => [f.name, example(f)])) },
  );
</script>

<section class="card preview">
  <div class="tabs" role="tablist">
    {#each TABS as [key, label]}
      <button type="button" role="tab" aria-selected={tab === key} onclick={() => (tab = key)}>{label}</button>
    {/each}
    <span class="live" title="Updates as you type">live</span>
  </div>
  <p class="help">{TABS.find((t) => t[0] === tab)![2]}</p>
  <Json {value} />
  <div class="foot"><CopyButton text={JSON.stringify(value, null, 2)} label="copy json" /></div>
</section>

<style>
  .preview { overflow: hidden; }
  .tabs { display: flex; align-items: center; border-bottom: 1px solid var(--border); padding: 0 8px; }
  .tabs button {
    position: relative;
    padding: 10px;
    white-space: nowrap;
    border: 0;
    background: none;
    color: var(--muted);
    font: 12px var(--mono);
    cursor: pointer;
    transition: color 0.2s;
  }
  .tabs button:hover { color: var(--text); }
  .tabs button[aria-selected='true'] { color: var(--green); }
  .tabs button[aria-selected='true']::after {
    content: '';
    position: absolute;
    left: 8px;
    right: 8px;
    bottom: -1px;
    height: 2px;
    background: var(--green);
    box-shadow: 0 0 8px var(--green-glow);
    animation: grow 0.25s var(--ease);
  }
  @keyframes grow { from { transform: scaleX(0); } }
  .live { margin-left: auto; font: 11px var(--mono); color: var(--green); display: inline-flex; align-items: center; gap: 6px; }
  .live::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: var(--green); animation: pulse 1.6s infinite; }
  .help { margin: 0; padding: 10px 16px 0; }
  .preview :global(pre) { max-height: 60vh; background: transparent; }
  .foot { display: flex; justify-content: flex-end; padding: 0 12px 12px; }
</style>
