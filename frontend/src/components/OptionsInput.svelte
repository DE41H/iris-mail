<script lang="ts">
  import { flip } from 'svelte/animate';
  import { scale } from 'svelte/transition';
  import { MAX_OPTIONS } from '../lib/schema';
  import { OPTION_SETS } from '../lib/presets';

  let { options = $bindable(), label }: { options: string[]; label: string } = $props();
  let draft = $state('');

  // Enter, comma or a pasted list all add answers; spaces become underscores so values stay clean.
  function add(text: string) {
    const fresh = text.split(/[,\n]/).map((t) => t.trim().toLowerCase().replace(/\s+/g, '_')).filter((t) => t && !options.includes(t));
    options = [...options, ...new Set(fresh)].slice(0, MAX_OPTIONS);
    draft = '';
  }

  function keydown(e: KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      add(draft);
    } else if (e.key === 'Backspace' && !draft && options.length) {
      options = options.slice(0, -1);
    }
  }

  function paste(e: ClipboardEvent) {
    const text = e.clipboardData?.getData('text') ?? '';
    if (/[,\n]/.test(text)) {
      e.preventDefault();
      add(draft + text);
    }
  }

  function useSet(e: Event) {
    const select = e.currentTarget as HTMLSelectElement;
    if (select.value) options = [...OPTION_SETS[select.value]];
    select.value = '';
  }
</script>

<div class="wrap">
  <div class="box">
    {#each options as option, i (option)}
      <span class="tag" animate:flip={{ duration: 200 }} transition:scale={{ duration: 150, start: 0.7 }}>
        {option}
        <button type="button" aria-label={`Remove answer ${option}`} onclick={() => (options = options.filter((_, j) => j !== i))}>×</button>
      </span>
    {/each}
    <input
      class="mono"
      type="text"
      bind:value={draft}
      onkeydown={keydown}
      onpaste={paste}
      onblur={() => draft && add(draft)}
      placeholder={options.length ? 'add…' : 'answers, comma separated'}
      aria-label={label}
      autocomplete="off"
      spellcheck="false"
    />
  </div>
  <select onchange={useSet} aria-label="Fill answers from a common set">
    <option value="">Use a set…</option>
    {#each Object.entries(OPTION_SETS) as [name, values]}
      <option value={name}>{name} · {values.length}</option>
    {/each}
  </select>
</div>

<style>
  .wrap { display: grid; grid-template-columns: 1fr auto; gap: 8px; align-items: start; }
  .box {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    padding: 3px;
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-sm);
    background: var(--surface);
    transition: border-color 0.2s, box-shadow 0.2s;
  }
  .box:focus-within { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
  .box input { flex: 1 0 120px; border: 0; padding: 3px 6px; background: none; box-shadow: none; }
  .tag {
    display: inline-flex;
    align-items: center;
    gap: 2px;
    padding: 2px 4px 2px 10px;
    border: 1px solid color-mix(in oklab, var(--accent) 35%, transparent);
    border-radius: 999px;
    background: var(--accent-soft);
    color: var(--accent);
    font: 12px/1.6 var(--mono);
  }
  .tag button { border: 0; background: none; color: inherit; cursor: pointer; padding: 0 6px; border-radius: 999px; font-size: 14px; line-height: 1; }
  .tag button:hover { background: var(--accent); color: var(--on-accent); }
  select { width: auto; }
  @media (max-width: 640px) { .wrap { grid-template-columns: 1fr; } }
</style>
