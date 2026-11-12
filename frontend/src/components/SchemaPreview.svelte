<script lang="ts">
  import { toSchema, type Field, type Rule } from '../lib/schema';
  import CopyButton from './CopyButton.svelte';
  import Json from './Json.svelte';

  let { fields, rules }: { fields: Field[]; rules: Rule[] } = $props();

  const TABS = { schema: 'Schema', result: 'Result' } as const;
  let tab = $state<keyof typeof TABS>('schema');

  const EXAMPLES = {
    boolean: true,
    number: 42.5,
    count: 3,
    text: 'snippet from the email',
    date: '2026-03-14',
    datetime: '2026-03-14T09:30:00+00:00',
    time: '09:30:00',
    email: 'someone@example.com',
    uri: 'https://example.com/page',
    hostname: 'mail.example.com',
    ipv4: '203.0.113.7',
    ipv6: '2001:db8::7',
    uuid: '0190a2b1-7c3e-7000-8000-4f2a9b6c1d3e',
  };
  const example = (f: Field) =>
    f.kind === 'scale' || f.kind === 'range' ? f.min : f.kind === 'choice' ? (f.options[0] ?? null) : f.kind === 'multi' ? f.options.slice(0, 2) : EXAMPLES[f.kind];
  const value = $derived(
    tab === 'schema' ? toSchema(fields) : { output: { ...Object.fromEntries(fields.map((f) => [f.name, example(f)])), ...(rules.length ? { rules: Object.fromEntries(rules.map((r) => [r.name, ['matched text']])) } : {}) } },
  );
</script>

<div class="preview">
  <div class="tabs" role="tablist">
    {#each Object.entries(TABS) as [t, label]}
      <button type="button" role="tab" aria-selected={tab === t} onclick={() => (tab = t as keyof typeof TABS)}>{label}</button>
    {/each}
  </div>
  <div class="code" role="tabpanel">
    <Json {value} />
    <div class="copy"><CopyButton text={JSON.stringify(value, null, 2)} label="Copy JSON" icon /></div>
  </div>
</div>

<style>
  .preview { display: flex; flex-direction: column; flex: 1; min-height: 0; }
  .tabs { display: flex; gap: 2px; padding: 10px 14px 0; border-bottom: 1px solid var(--border); }
  .tabs button {
    flex: 1;
    position: relative;
    padding: 8px 8px 10px;
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
  .code { position: relative; flex: 1; min-height: 0; display: flex; }
  .code :global(pre) { flex: 1; min-height: 120px; background: transparent; border-radius: 0; }
  .copy { position: absolute; top: 10px; right: 12px; }
</style>
