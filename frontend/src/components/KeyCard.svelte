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

  const curl = $derived(`curl -H "Authorization: Bearer ${key}" ${location.origin}/api/results/?fetched=false`);
</script>

<section class="card key">
  <div class="card-head"><span class="green">● api key issued</span><span>shown once</span></div>
  <div class="card-body stack">
    <p class="muted">Copy it now and keep it secret. Iris stores only a hash, so it can't be shown again. Rotate it any time.</p>
    <div class="row">
      <code>{shown}</code>
      <CopyButton text={key} label="copy key" />
    </div>
    <div>
      <div class="label">fetch new results</div>
      <div class="row">
        <code class="small">{curl}</code>
        <CopyButton text={curl} />
      </div>
    </div>
  </div>
</section>

<style>
  .key { border-color: rgba(61, 220, 132, 0.45); box-shadow: 0 0 40px rgba(61, 220, 132, 0.08); animation: rise 0.5s var(--ease) both; }
  .row { display: flex; align-items: center; gap: 8px; }
  code {
    flex: 1;
    min-width: 0;
    padding: 10px 12px;
    background: var(--bg);
    border: 1px dashed var(--border-strong);
    border-radius: 6px;
    color: var(--green);
    word-break: break-all;
  }
  .small { font-size: 12px; color: var(--text); }
</style>
