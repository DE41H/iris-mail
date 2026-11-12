<script lang="ts">
  let { text, label = 'Copy', icon = false }: { text: string; label?: string; icon?: boolean } = $props();
  let status = $state<'idle' | 'copied' | 'failed'>('idle');

  // The clipboard API is missing on plain http and can be refused, so say so instead of failing silently.
  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      status = 'copied';
    } catch {
      status = 'failed';
    }
    setTimeout(() => (status = 'idle'), 1800);
  }
</script>

<button type="button" class="btn btn-sm {status}" class:icon onclick={copy} aria-live="polite" aria-label={icon && status === 'idle' ? label : undefined} title={icon ? label : undefined}>
  {#key status}
    {#if icon && status === 'idle'}
      <svg class="txt" viewBox="0 0 16 16" aria-hidden="true"><rect x="5.5" y="5.5" width="8" height="8" rx="1.5" /><path d="M10.5 3.5v-.5A1.5 1.5 0 0 0 9 1.5H4A1.5 1.5 0 0 0 2.5 3v5A1.5 1.5 0 0 0 4 9.5h.5" /></svg>
    {:else}
      <span class="txt">{status === 'copied' ? (icon ? '' : 'Copied') : status === 'failed' ? 'Copy failed, select it' : label}</span>
    {/if}
  {/key}
</button>

<style>
  .txt { display: inline-block; animation: swap 0.3s var(--spring); }
  @keyframes swap { from { opacity: 0; translate: 0 6px; } }
  .copied { color: var(--accent); border-color: var(--accent); background: var(--accent-soft); }
  .copied .txt::before { content: '✓ '; }
  .icon { min-width: 30px; padding-inline: 7px; justify-content: center; }
  .icon svg { width: 15px; height: 15px; fill: none; stroke: currentColor; stroke-width: 1.4; stroke-linejoin: round; }
  .failed { color: var(--danger); border-color: var(--danger); }
</style>
