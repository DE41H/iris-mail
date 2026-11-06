<script lang="ts">
  import { onMount } from 'svelte';
  import CopyButton from './CopyButton.svelte';

  // The server returns a key once, so this card is the only place it lives.
  let { key }: { key: string } = $props();

  const GLYPHS = 'abcdefghijklmnopqrstuvwxyz0123456789#$%&';
  let shown = $state('');

  onMount(() => {
    let frame = 0;
    const tick = setInterval(() => {
      frame++;
      shown = [...key].map((c, i) => (i < frame * 1.5 ? c : GLYPHS[Math.floor(Math.random() * GLYPHS.length)])).join('');
      if (frame * 1.5 >= key.length) clearInterval(tick);
    }, 30);
    return () => clearInterval(tick);
  });

  const curl = $derived(`curl -H "Authorization: Bearer ${key}" ${location.origin}/api/v1/results/?fetched=false`);
</script>

<section class="card key">
  <div class="card-head"><h2>Your API key</h2><span class="once">Shown once. Copy it now.</span></div>
  <div class="card-body stack">
    <div class="row">
      <code>{shown}</code>
      <CopyButton text={key} label="Copy key" />
    </div>
    <div>
      <div class="label">Fetch new results</div>
      <div class="row">
        <code class="small">{curl}</code>
        <CopyButton text={curl} />
      </div>
    </div>
  </div>
</section>

<style>
  .key { border-color: color-mix(in oklab, var(--accent) 40%, var(--border)); box-shadow: var(--shadow-lift); animation: rise 0.5s var(--ease) both; }
  h2 { color: var(--text); }
  .once { display: inline-flex; align-items: center; gap: 6px; padding: 2px 10px; border-radius: 999px; background: var(--signal-soft); color: var(--signal-text); font-weight: 560; }
  .row { display: flex; align-items: center; gap: 8px; }
  code {
    flex: 1;
    min-width: 0;
    padding: 10px 12px;
    background: var(--surface-2);
    border: 1px dashed var(--border-strong);
    border-radius: var(--radius-sm);
    color: var(--accent);
    font-size: 14px;
    word-break: break-all;
  }
  .small { font-size: 12.5px; color: var(--text); }
</style>
