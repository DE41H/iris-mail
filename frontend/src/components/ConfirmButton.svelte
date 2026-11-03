<script lang="ts">
  // Inline two-step confirmation: the first click arms the button, a second within 4s runs it.
  let { label, confirm, danger = false, onconfirm }: { label: string; confirm: string; danger?: boolean; onconfirm: () => unknown } = $props();

  let armed = $state(false);
  let busy = $state(false);
  let timer: ReturnType<typeof setTimeout>;

  async function click() {
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

<button type="button" class="btn" class:btn-danger={danger} class:armed disabled={busy} onclick={click}>
  {busy ? 'working…' : armed ? confirm : label}
</button>

<style>
  .armed { animation: shake 0.35s; border-color: currentColor; }
  .armed::before { content: '!'; }
  @keyframes shake {
    25% { transform: translateX(-3px); }
    75% { transform: translateX(3px); }
  }
</style>
