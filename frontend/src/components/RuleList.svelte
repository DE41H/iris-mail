<script lang="ts">
  import { MAX_RULES, MAX_PATTERN, ruleProblems, type Rule } from '../lib/schema';

  let { rules = $bindable() }: { rules: Rule[] } = $props();
  const full = $derived(rules.length >= MAX_RULES);
</script>

<div class="rule-list">
  <div class="toolbar">
    <span class="label">rules</span>
    <span class="help">Every match is saved as a list under <code>rules</code>; a group's text if the pattern has one.</span>
    <button type="button" class="btn btn-sm" disabled={full} onclick={() => rules.push({ name: '', pattern: '' })}>+ Rule</button>
    <span class="count" class:full>{rules.length}/{MAX_RULES}</span>
  </div>
  {#each rules as r, i}
    {@const issues = ruleProblems(r, rules)}
    <div class="row">
      <input class="mono" type="text" bind:value={r.name} placeholder="order_id" aria-label={`Rule ${i + 1} name`} autocomplete="off" spellcheck="false" />
      <input class="mono" type="text" bind:value={r.pattern} placeholder={'#(\\d+)'} maxlength={MAX_PATTERN} aria-label={`Rule ${i + 1} pattern`} aria-invalid={!!issues.length && !!r.pattern} autocomplete="off" spellcheck="false" />
      <button type="button" class="btn btn-sm btn-ghost" aria-label={`Remove rule ${r.name || i + 1}`} onclick={() => rules.splice(i, 1)}>×</button>
    </div>
  {/each}
</div>

<style>
  .rule-list { display: grid; gap: 8px; }
  .toolbar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  .help { font-size: 12px; color: var(--muted); }
  .count { margin-left: auto; font: 12px var(--mono); color: var(--muted); }
  .count.full { color: var(--amber); }
  .row { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 2fr) auto; gap: 8px; }
  @media (max-width: 640px) { .row { grid-template-columns: minmax(0, 1fr) auto; } .row input:nth-child(2) { grid-column: 1 / -1; grid-row: 2; } }
</style>
