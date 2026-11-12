<script lang="ts">
  import { onDestroy } from 'svelte';

  // Inline two-step confirmation: the first click arms the button, a second within 4s runs it.
  let { label, danger = false, onconfirm }: { label: string; danger?: boolean; onconfirm: () => unknown } = $props();

  let armed = $state(false);
  let busy = $state(false);
  let timer: ReturnType<typeof setTimeout>;
  onDestroy(() => clearTimeout(timer));

  async function click() {
    if (busy) return;
    if (!armed) {
      armed = true;
      timer = setTimeout(() => (armed = false), 4000);
      return;
    }
    clearTimeout(timer);
    armed = false;
    busy = true;
    try {
      await onconfirm();
    } finally {
      busy = false;
    }
  }
</script>

<button type="button" class="btn" class:btn-danger={danger} class:armed disabled={busy} onclick={click} onblur={() => armed && (clearTimeout(timer), (armed = false))}>
  {busy ? 'Working…' : label}{#if armed}<span class="sr-only">, click again to confirm</span>{/if}
</button>

<style>
  .btn { position: relative; overflow: hidden; }
  /* Armed: the label stays; the button shakes harder as the 4s window runs out. */
  @property --amp { syntax: '<length>'; inherits: false; initial-value: 1px; }
  .armed { border-color: currentColor; animation: shake 0.3s linear infinite, grow 4s linear both; }
  /* The bar drains over the 4s window, so it is clear how long the second click stays open. */
  .armed::after {
    content: '';
    position: absolute;
    inset: auto 0 0;
    height: 2px;
    background: currentColor;
    transform-origin: left;
    animation: drain 4s linear both;
  }
  @keyframes drain { to { scale: 0 1; } }
  @keyframes grow { to { --amp: 3px; } }
  @keyframes shake { 25% { translate: calc(var(--amp) * -1) 0; } 75% { translate: var(--amp) 0; } }
</style>
