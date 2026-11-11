<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../lib/api';
  import Count from './Count.svelte';

  // Questions answered across Iris today; hidden until there is a number worth showing.
  let today = $state(0);
  onMount(() => {
    api<{ today: number }>('/api/v1/usage/total/').then((s) => (today = s.today), () => {});
  });
</script>

{#if today > 0}
  <p><b><Count value={today} /></b> questions answered today</p>
{/if}

<style>
  p { margin: 0; font-size: 13px; color: var(--muted); }
  b { color: var(--text); font-weight: 640; font-variant-numeric: tabular-nums; }
</style>
