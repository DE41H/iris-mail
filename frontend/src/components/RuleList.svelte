<script lang="ts">
  import { tick } from 'svelte';
  import { slide } from 'svelte/transition';
  import { MAX_NAME_LENGTH, MAX_RULES, MAX_PATTERN, type Rule } from '../lib/schema';
  import { ruleMatches, ruleProblems } from '../lib/rules';

  let { rules = $bindable() }: { rules: Rule[] } = $props();
  const full = $derived(rules.length >= MAX_RULES);
  let touched = $state<Rule[]>([]);
  let sample = $state('');
  let testing = $state(false);
  let rows = $state<HTMLElement>();

  async function add(rule: Rule) {
    if (full) return;
    rules.push(rule);
    await tick();
    rows?.querySelectorAll('.rule')[rules.length - 1]?.querySelector('input')?.focus();
  }
</script>

<div class="rule-list">
  {#if rules.length}
    <div class="rows" bind:this={rows}>
      <div class="row head" aria-hidden="true"><span>Saved as</span><span>Pattern</span></div>
      {#each rules as r, i}
        {@const issues = ruleProblems(r, rules)}
        {@const shown = touched.includes(r) && issues.length}
        {@const found = testing && sample ? ruleMatches(r.pattern, sample) : []}
        <div class="rule" transition:slide={{ duration: 180 }} onfocusout={() => touched.includes(r) || touched.push(r)}>
          <div class="row">
            <input class="mono" type="text" bind:value={r.name} placeholder="order_id" maxlength={MAX_NAME_LENGTH} aria-label={`Rule ${i + 1} name`} autocomplete="off" spellcheck="false" />
            <input class="mono" type="text" bind:value={r.pattern} placeholder={'Order #(\\d+)'} maxlength={MAX_PATTERN} aria-label={`Rule ${i + 1} pattern`} aria-invalid={!!shown} autocomplete="off" spellcheck="false" />
            <button type="button" class="tool" title="Remove" aria-label={`Remove rule ${r.name || i + 1}`} onclick={() => rules.splice(i, 1)}>✕</button>
          </div>
          {#if shown}<div class="error">{issues.join(' ')}</div>{/if}
          {#if testing && sample && r.pattern && !shown}
            <div class="hits" aria-live="polite">
              {#if found === null}<span class="none">Pattern does not compile.</span>
              {:else if !found.length}<span class="none">No match</span>
              {:else}{#each found as m}<code class="hit">{m}</code>{/each}{/if}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}

  {#if testing && rules.length}
    <label class="sample" transition:slide={{ duration: 200 }}>
      <span class="label">Sample email text</span>
      <textarea rows="3" bind:value={sample} placeholder="Thanks for your order #48213. Total: $42.50"></textarea>
    </label>
  {/if}
  <div class="add">
    <button type="button" class="add-pill" disabled={full} onclick={() => add({ name: '', pattern: '' })}><i aria-hidden="true">+</i>Add a rule</button>
    {#if rules.length}<button type="button" class="text-btn" aria-expanded={testing} onclick={() => (testing = !testing)}>{testing ? 'Hide tester' : 'Test on sample text'}</button>{/if}
  </div>

</div>

<style>
  .rule-list, .rows { display: grid; grid-template-columns: minmax(0, 1fr); gap: 12px; }
  .rows { gap: 8px; }
  .row { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 2fr) 28px; gap: 8px; align-items: center; }
  .head { font-size: 12.5px; color: var(--muted); font-weight: 540; }
  .rule .error { margin: 4px 0 0; }
  .hits { display: flex; flex-wrap: wrap; gap: 4px; margin: 6px 36px 0 calc((100% - 52px) / 3 + 8px); font-size: 12px; }
  .hit { padding: 1px 8px; border-radius: 6px; background: var(--signal-soft); color: var(--signal-text); font-size: 12px; }
  .none { color: var(--faint); }
  .add { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
  .label { margin: 0 4px 0 0; font-size: 13px; }
  .text-btn { margin-left: auto; }
  .sample { display: block; }
  textarea { min-height: 76px; font-size: 13.5px; }
  .tool { width: 28px; height: 28px; display: grid; place-items: center; border: 0; border-radius: 8px; background: none; color: var(--muted); font-size: 13px; cursor: pointer; transition: background 0.2s, color 0.2s; }
  .tool:hover { background: var(--danger-soft); color: var(--danger); }
  @media (max-width: 640px) {
    .head { display: none; }
    .row { grid-template-columns: minmax(0, 1fr) 28px; }
    .row input:nth-child(2) { grid-column: 1 / -1; grid-row: 2; }
    .hits { margin-left: 0; }
  }
</style>
