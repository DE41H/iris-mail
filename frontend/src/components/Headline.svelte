<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { api } from '../lib/api';

  // Shows this week's total while the demo lens is shut and the pitch while it is open.
  const intro = ['Ask inboxes questions.', 'Get JSON back.'];
  const ease = 'cubic-bezier(0.22, 1, 0.36, 1)';
  const rest = { transform: 'none', opacity: 1, filter: 'blur(0)' };
  const above = { transform: 'translateY(-0.45em)', opacity: 0, filter: 'blur(4px)' };
  const below = { transform: 'translateY(0.45em)', opacity: 0, filter: 'blur(4px)' };
  let stats = $state<string[] | null>(null);
  let lines = $state(intro);
  let live: HTMLElement;
  let paused = false;

  onMount(() => {
    let showing = 'intro';
    let queue = Promise.resolve();

    // Old lines roll up and out, new ones roll in from below.
    async function roll(to: string[]) {
      const opts = { duration: 380, easing: ease, fill: 'both' } as const;
      await live.animate([rest, above], opts).finished;
      lines = to;
      await tick();
      live.getAnimations().forEach((a) => a.cancel());
      await live.animate([below, rest], opts).finished;
    }

    // Lens phases: 'drop' shuts the aperture, 'read' opens it. The pitch shows first, so the first shut is the first flip.
    const onLens = (e: Event) => {
      const want = { drop: 'stats', read: 'intro' }[(e as CustomEvent<string>).detail];
      if (!stats || paused || !want || want === showing) return;
      showing = want;
      const to = want === 'stats' ? stats : intro;
      queue = queue.then(() => roll(to));
    };
    addEventListener('iris:lens', onLens);

    api<{ week: number }>('/api/v1/usage/stats/').then((s) => {
      if (s.week > 0) stats = [`${s.week.toLocaleString()} questions`, 'answered this week'];
    }, () => {});
    return () => removeEventListener('iris:lens', onLens);
  });
</script>

<!-- Hovering holds the current text. Readers get both texts once; a live region would announce every flip. -->
<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<h1 onpointerenter={() => (paused = true)} onpointerleave={() => (paused = false)}>
  <span class="sr-only">{[...intro, ...(stats ?? [])].join(' ')}</span>
  <!-- Hidden copies of both texts hold the taller one's height, so flips never shift the page. -->
  <span class="stack" aria-hidden="true">
    <span bind:this={live}>{lines[0]}<br />{lines[1]}</span>
    <span class="ghost">{intro[0]}<br />{intro[1]}</span>
    {#if stats}<span class="ghost">{stats[0]}<br />{stats[1]}</span>{/if}
  </span>
</h1>

<style>
  /* The one load moment: the headline pulls into focus, narrow and light to wide and heavy. */
  h1 {
    grid-column: 1 / -1;
    font-size: clamp(38px, 6.4vw, 80px);
    line-height: 1;
    letter-spacing: -0.035em;
    font-weight: 720;
    font-stretch: 118%;
    animation: focus 1.4s var(--ease) both;
  }
  @keyframes focus {
    from { font-stretch: 75%; font-weight: 250; letter-spacing: 0.02em; filter: blur(10px); opacity: 0; }
    60% { filter: blur(0); opacity: 1; }
  }
  @media (min-width: 861px) { span { white-space: nowrap; } }
  .stack { display: grid; }
  .stack > * { grid-area: 1 / 1; }
  .ghost { visibility: hidden; }
</style>
