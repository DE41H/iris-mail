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
    color: var(--muted);
    background: var(--bg);
    border-radius: 6px;
  }
  pre :global(.k) { color: var(--green); }
  pre :global(.s) { color: #c9d8cf; }
  pre :global(.n) { color: var(--amber); }
  pre :global(.l) { color: #8ab4ff; }
</style>
