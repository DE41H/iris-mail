<script lang="ts">
  let { text, label = 'Copy' }: { text: string; label?: string } = $props();
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

<button type="button" class="btn btn-sm {status}" onclick={copy} aria-live="polite">
  {#key status}<span class="txt">{status === 'copied' ? 'Copied' : status === 'failed' ? 'Copy failed, select it' : label}</span>{/key}
</button>

<style>
  .txt { display: inline-block; animation: swap 0.3s var(--spring); }
  @keyframes swap { from { opacity: 0; translate: 0 6px; } }
  .copied { color: var(--accent); border-color: var(--accent); background: var(--accent-soft); }
  .copied .txt::before { content: '✓ '; }
  .failed { color: var(--danger); border-color: var(--danger); }
</style>
