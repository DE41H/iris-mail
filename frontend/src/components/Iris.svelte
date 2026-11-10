<script lang="ts">
  // The home page aperture in the plugin's own colour (--h). It opens while its link is hovered or focused.
  let { breathe = false, open = false }: { breathe?: boolean; open?: boolean } = $props();
  const id = $props.id();
</script>

<svg class="iris" class:breathe class:open viewBox="-64 -64 128 128" aria-hidden="true">
  <defs>
    <clipPath id={`${id}-lens`}><circle r="56" /></clipPath>
    <radialGradient id={`${id}-pupil`}>
      <stop offset="0" class="s0" />
      <stop offset="0.55" class="s1" />
      <stop offset="1" class="s2" />
    </radialGradient>
  </defs>
  <circle r="61" class="halo" />
  <g clip-path={`url(#${id}-lens)`}>
    <circle r="56" fill={`url(#${id}-pupil)`} />
    <g class="blades">
      {#each { length: 6 } as _, i}
        <g transform={`rotate(${i * 60})`}><path class="blade" style:--i={i} d="M0,-80 A80,80 0 0 1 69.28,-40 L0,0 Z" /></g>
      {/each}
    </g>
  </g>
  <circle r="56" class="rim" />
</svg>

<style>
  .iris {
    --tint: oklch(0.58 0.19 var(--h, 262));
    --tint-strong: oklch(0.42 0.19 calc(var(--h, 262) + 20));
    flex-shrink: 0;
    width: 44px;
    height: 44px;
    overflow: visible;
    filter: drop-shadow(0 5px 10px color-mix(in oklab, var(--tint) 35%, transparent));
  }
  .s0 { stop-color: var(--signal); }
  .s1 { stop-color: color-mix(in oklab, var(--signal) 70%, var(--tint)); }
  .s2 { stop-color: var(--tint-strong); }
  .halo { fill: none; stroke: color-mix(in oklab, var(--tint) 16%, transparent); stroke-width: 6; transition: stroke 0.6s, stroke-width 0.6s var(--ease); }
  .rim { fill: none; stroke: var(--tint-strong); stroke-width: 3; }
  .blades { transition: rotate 1.4s var(--ease); }
  .blade {
    transform-box: fill-box;
    transform-origin: 0 0;
    fill: color-mix(in oklab, var(--tint) calc(58% + var(--i) * 7%), var(--tint-strong));
    stroke: color-mix(in oklab, var(--tint-strong) 60%, black);
    stroke-width: 1.2;
    rotate: -5deg;
    transition: rotate 0.9s var(--spring);
    transition-delay: calc(var(--i) * 30ms);
  }

  /* Open: the blades swing back on their rim pivots and the saffron pupil shows. */
  .open .halo, :global(:is(a, button):is(:hover, :focus-visible)) .halo { stroke: color-mix(in oklab, var(--tint) 26%, transparent); stroke-width: 12; }
  .open .blades, :global(:is(a, button):is(:hover, :focus-visible)) .blades { rotate: 60deg; }
  .open .blade, :global(:is(a, button):is(:hover, :focus-visible)) .blade { rotate: -34deg; }

  .breathe { width: 76px; height: 76px; }
  .breathe .blades { animation: turn 7s var(--ease) infinite alternate; }
  .breathe .blade { animation: open 7s var(--ease) calc(var(--i) * 40ms) infinite alternate; }
  @keyframes turn { to { rotate: 60deg; } }
  @keyframes open { to { rotate: -34deg; } }
</style>
