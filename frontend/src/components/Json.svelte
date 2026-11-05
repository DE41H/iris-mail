<script lang="ts">
  let { value }: { value: unknown } = $props();

  const escape = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const highlight = (json: string) =>
    escape(json).replace(/("(?:\\.|[^"\\])*")(\s*:)?|\b(true|false|null)\b|-?\d+/g, (m, str, colon, lit) =>
      str ? `<span class=${colon ? 'k' : 's'}>${str}</span>${colon ?? ''}` : `<span class=${lit ? 'l' : 'n'}>${m}</span>`,
    );

  const html = $derived(highlight(JSON.stringify(value, null, 2)));
</script>

<pre>{@html html}</pre>

<style>
  pre {
    margin: 0;
    padding: 16px;
    overflow: auto;
    font-size: 12px;
    line-height: 1.6;
    color: var(--faint);
    background: var(--surface-2);
    border-radius: var(--radius-sm);
  }
  pre :global(.k) { color: var(--accent); }
  pre :global(.s) { color: var(--text); }
  pre :global(.n) { color: var(--signal-text); }
  pre :global(.l) { color: var(--signal-text); }
</style>
