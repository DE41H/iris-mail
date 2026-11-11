<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../lib/api';
  import Count from './Count.svelte';

  // Hidden until there is a number worth showing.
  let week = $state(0);
  onMount(() => {
    api<{ week: number }>('/api/v1/usage/stats/').then((s) => (week = s.week), () => {});
  });
</script>

{#if week > 0}
  <p><b><Count value={week} /></b> questions answered this week</p>
{/if}

<style>
  p { margin: 0; font-size: 13px; color: var(--muted); }
  b { color: var(--text); font-weight: 640; font-variant-numeric: tabular-nums; }
</style>
