<script lang="ts">
  let { text, label = 'copy' }: { text: string; label?: string } = $props();
  let copied = $state(false);

  async function copy() {
    await navigator.clipboard.writeText(text);
    copied = true;
    setTimeout(() => (copied = false), 1500);
  }
</script>

<button type="button" class="btn btn-sm" class:copied onclick={copy}>{copied ? '✓ copied' : label}</button>

<style>
  .copied { color: var(--green); border-color: var(--green); }
</style>
