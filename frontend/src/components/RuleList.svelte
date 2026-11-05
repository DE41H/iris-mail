<script lang="ts">
  import { slide } from 'svelte/transition';
  import { MAX_NAME_LENGTH, MAX_RULES, MAX_PATTERN, ruleProblems, type Rule } from '../lib/schema';
  import { RULE_PRESETS } from '../lib/presets';

  let { rules = $bindable() }: { rules: Rule[] } = $props();
  const full = $derived(rules.length >= MAX_RULES);
  const unused = $derived(RULE_PRESETS.filter((p) => !rules.some((r) => r.name === p.name)));
  let touched = $state<Rule[]>([]);

  function preset(e: Event) {
    const select = e.currentTarget as HTMLSelectElement;
    const found = RULE_PRESETS.find((p) => p.name === select.value);
    if (found && !full) rules.push({ ...found });
    select.value = '';
  }
</script>

<div class="rule-list">
  {#if rules.length}
    <div class="rows">
      <div class="row head" aria-hidden="true"><span>Saved as</span><span>Pattern (RE2 regex, the first group is kept)</span></div>
      {#each rules as r, i}
        {@const issues = ruleProblems(r, rules)}
        {@const shown = touched.includes(r) && issues.length}
        <div class="rule" transition:slide={{ duration: 180 }} onfocusout={() => touched.includes(r) || touched.push(r)}>
          <div class="row">
            <input class="mono" type="text" bind:value={r.name} placeholder="order_id" maxlength={MAX_NAME_LENGTH} aria-label={`Rule ${i + 1} name`} autocomplete="off" spellcheck="false" />
            <input class="mono" type="text" bind:value={r.pattern} placeholder={'Order #(\\d+)'} maxlength={MAX_PATTERN} aria-label={`Rule ${i + 1} pattern`} aria-invalid={!!shown} autocomplete="off" spellcheck="false" />
            <button type="button" class="tool" title="Remove" aria-label={`Remove rule ${r.name || i + 1}`} onclick={() => rules.splice(i, 1)}>✕</button>
          </div>
          {#if shown}<div class="error">{issues.join(' ')}</div>{/if}
        </div>
      {/each}
    </div>
  {/if}

  <div class="more">
    <button type="button" class="btn btn-sm" disabled={full} onclick={() => rules.push({ name: '', pattern: '' })}>+ Add a rule</button>
    <select disabled={full || !unused.length} onchange={preset} aria-label="Add a common pattern">
      <option value="">Or start from a common pattern…</option>
      {#each unused as p}<option value={p.name}>{p.name.replaceAll('_', ' ')}</option>{/each}
    </select>
  </div>
  <p class="help">Matches land in the output under <code>rules</code>, as a list per rule.</p>
</div>

<style>
  .rule-list, .rows { display: grid; grid-template-columns: minmax(0, 1fr); gap: 12px; }
  .rows { gap: 8px; }
  .row { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 2fr) 28px; gap: 8px; align-items: center; }
  .head { font-size: 12.5px; color: var(--muted); font-weight: 540; }
  .rule .error { margin: 4px 0 0; }
  .more { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
  .more select { flex: 1 1 220px; min-width: 0; width: auto; font-size: 13.5px; }
  .help { margin: 0; }
  .tool { width: 28px; height: 28px; display: grid; place-items: center; border: 0; border-radius: 8px; background: none; color: var(--muted); font-size: 13px; cursor: pointer; transition: background 0.2s, color 0.2s; }
  .tool:hover { background: var(--danger-soft); color: var(--danger); }
  @media (max-width: 640px) {
    .head { display: none; }
    .row { grid-template-columns: minmax(0, 1fr) 28px; }
    .row input:nth-child(2) { grid-column: 1 / -1; grid-row: 2; }
  }
</style>
