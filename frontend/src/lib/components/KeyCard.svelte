<script lang="ts">
  import type { Snippet } from 'svelte';

  // Shows a freshly issued key. The server returns it once, so this card is the only place it lives.
  let { key, children }: { key: string; children?: Snippet } = $props();

  let copied = $state(false);

  const copy = async () => {
    await navigator.clipboard.writeText(key);
    copied = true;
    setTimeout(() => (copied = false), 1500);
  };
</script>

<section class="card key-card">
  <h2>Your API key</h2>
  <p class="muted">Copy it now. It will not be shown again.</p>
  <code class="mono">{key}</code>
  <div class="actions">
    <button type="button" class="btn btn-sm" onclick={copy}>{copied ? 'Copied' : 'Copy key'}</button>
    {@render children?.()}
  </div>
</section>
