<script lang="ts">
  import { onMount } from 'svelte';
  import { loadSession, session } from '../lib/session';

  let path = $state('');
  let broken = $state(false);

  onMount(() => {
    path = location.pathname.replace(/\/$/, '');
    loadSession();
  });

  const current = (href: string) => (path === href || path.startsWith(`${href}/`) ? 'page' : undefined);
</script>

<nav aria-label="Account">
  <a href="/docs" aria-current={current('/docs')}>Docs</a>
  {#if $session}
    <a href="/plugins" aria-current={current('/plugins')}>Plugins</a>
    <a href="/subscriptions" aria-current={current('/subscriptions')}><span class="long">Subscriptions</span><span class="short">Inbox</span></a>
    <span class="account">
      <a class="face" href="/me" title={$session.email} aria-label="Your account" aria-current={current('/me')}>
        {#if $session.avatar && !broken}
          <img class="avatar" src={$session.avatar} alt="" referrerpolicy="no-referrer" onerror={() => (broken = true)} />
        {:else}
          <span class="avatar">{$session.email[0].toUpperCase()}</span>
        {/if}
      </a>
    </span>
  {:else if $session === null}
    <a class="btn btn-sm btn-primary" href="/accounts/login/">Sign in</a>
  {/if}
</nav>

<style>
  .account {
    display: flex;
    padding-left: 12px;
    border-left: 1px solid var(--border);
    margin-left: 8px;
  }
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
  /* The full nav needs ~360px; phones narrower than 400px get the short label. */
  @media (max-width: 400px) {
    .long { display: none; }
    .short { display: inline; }
  }
</style>
