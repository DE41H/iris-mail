<script lang="ts">
  import { onMount } from 'svelte';
  import { loadSession, session } from '../lib/session';

  let path = $state('');
  let broken = $state(false);
  let dark = $state(false);

  onMount(() => {
    path = location.pathname.replace(/\/$/, '');
    dark = document.documentElement.dataset.theme === 'dark';
    loadSession();
  });

  function flip() {
    dark = !dark;
    const theme = dark ? 'dark' : 'light';
    document.documentElement.dataset.theme = theme;
    try { localStorage.theme = theme; } catch {}
  }

  const current = (href: string) => (path === href || path.startsWith(`${href}/`) ? 'page' : undefined);
</script>

<nav aria-label="Main">
  <a href="/docs" aria-current={current('/docs')}>Docs</a>
  {#if $session}
    <a href="/plugins" aria-current={current('/plugins')}>Plugins</a>
    <a href="/keys" aria-current={current('/keys')}>Keys</a>
    <a href="/subscriptions" aria-current={current('/subscriptions')}><span class="long">Subscriptions</span><span class="short">Inbox</span></a>
    <span class="account">
      {@render toggle()}
      <a class="face" href="/me" title={$session.email} aria-label="Your account" aria-current={current('/me')}>
        {#if $session.avatar && !broken}
          <img class="avatar" src={$session.avatar} alt="" referrerpolicy="no-referrer" onerror={() => (broken = true)} />
        {:else}
          <span class="avatar">{$session.email[0].toUpperCase()}</span>
        {/if}
      </a>
    </span>
  {:else if $session === null}
    <span class="account">{@render toggle()}<a class="btn btn-sm btn-primary" href="/accounts/login/">Sign in</a></span>
  {/if}
</nav>

{#snippet toggle()}
  <button class="theme" class:dark type="button" onclick={flip} aria-label={dark ? 'Use light theme' : 'Use dark theme'} title={dark ? 'Light theme' : 'Dark theme'}>
    <!-- The sun's rays fold away and a bite slides over its core, leaving a moon. -->
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <mask id="bite">
        <rect width="24" height="24" fill="white" />
        <circle class="bite" cx="12" cy="12" r="4" fill="black" />
      </mask>
      <circle class="core" cx="12" cy="12" r="5" mask="url(#bite)" />
      <g class="rays">
        {#each [0, 45, 90, 135, 180, 225, 270, 315] as a}
          <line x1="12" y1="2.5" x2="12" y2="4.5" transform="rotate({a} 12 12)" />
        {/each}
      </g>
    </svg>
  </button>
  <span class="sep" aria-hidden="true"></span>
{/snippet}

<style>
  .account {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-left: 16px;
  }
  .sep { width: 1px; height: 20px; background: var(--border); }

  .theme {
    width: 32px;
    height: 32px;
    display: grid;
    place-items: center;
    padding: 0;
    border: 1px solid transparent;
    border-radius: 50%;
    background: none;
    color: var(--muted);
    cursor: pointer;
    transition: color 0.2s, background 0.2s, border-color 0.2s, box-shadow 0.25s, translate 0.25s var(--ease), scale 0.15s var(--ease);
  }
  .theme:hover { color: var(--signal-text); background: var(--surface); border-color: var(--border); translate: 0 -1px; box-shadow: var(--shadow); }
  .theme.dark:hover { color: var(--accent); }
  .theme:active { scale: 0.92; translate: 0; }
  .theme:focus-visible { border-radius: 50%; }

  svg { width: 20px; height: 20px; overflow: visible; transition: rotate 0.7s var(--spring); }
  .core { fill: currentColor; transform-origin: 12px 12px; transition: scale 0.6s var(--spring); }
  .bite { transform-origin: 12px 12px; translate: 12px -12px; transition: translate 0.6s var(--ease); }
  .rays { stroke: currentColor; stroke-width: 2; stroke-linecap: round; transform-origin: 12px 12px; transition: rotate 0.6s var(--ease), scale 0.5s var(--ease), opacity 0.3s; }
  .theme:hover .rays { rotate: 22.5deg; }

  /* Moon: the whole mark turns, the rays spin in, the core swells and the bite slides over it. */
  .dark svg { rotate: -270deg; }
  .dark .core { scale: 1.7; }
  .dark .bite { translate: 3.5px -3.5px; }
  .dark .rays { rotate: 90deg; scale: 0.4; opacity: 0; }
  .face { display: block; border-radius: 30%; }
  .avatar {
    width: 30px;
    height: 30px;
    border-radius: 30%;
    object-fit: cover;
    display: grid;
    place-items: center;
    background: var(--accent-soft);
    color: var(--accent);
    font-size: 13px;
    font-weight: 600;
    transition: box-shadow 0.2s var(--ease);
  }
  .face:hover .avatar { box-shadow: 0 0 0 3px var(--accent-soft); }
  .face[aria-current='page'] .avatar { box-shadow: 0 0 0 2px var(--accent); }
  @supports (corner-shape: squircle) {
    .avatar, .face { border-radius: 50%; corner-shape: squircle; }
  }

  .short { display: none; }
  /* The full nav needs ~400px; narrower phones get the short label and tighter spacing. */
  @media (max-width: 400px) {
    .long { display: none; }
    .short { display: inline; }
    .account { gap: 6px; padding-left: 8px; }
  }
</style>
