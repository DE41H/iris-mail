<script lang="ts">
  import { onDestroy } from 'svelte';

  // Inline two-step confirmation: the first click arms the button, a second within 4s runs it.
  let { label, confirm, danger = false, onconfirm }: { label: string; confirm: string; danger?: boolean; onconfirm: () => unknown } = $props();

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
  {busy ? 'Working…' : armed ? confirm : label}
</button>

<style>
  .btn { position: relative; overflow: hidden; }
  .armed { border-color: currentColor; animation: nudge 0.35s var(--ease); }
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
  @keyframes nudge { 30% { translate: -3px 0; } 60% { translate: 2px 0; } }
</style>
