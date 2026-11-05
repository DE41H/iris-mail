<script lang="ts">
  import { cubicOut } from 'svelte/easing';
  import { untrack } from 'svelte';
  import { Tween } from 'svelte/motion';

  // Counts up to the value; jumps straight there when motion is reduced.
  let { value, delay = 0 }: { value: number; delay?: number } = $props();
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const n = new Tween(0, { duration: reduced ? 0 : 1100, delay: reduced ? 0 : untrack(() => delay), easing: cubicOut });
  $effect(() => {
    n.target = value;
  });
</script>

{Math.round(n.current).toLocaleString()}
