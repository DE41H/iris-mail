<script lang="ts">
  import { onMount } from 'svelte';
  import { loadSession, session } from '../lib/session';

  let path = $state('');
  onMount(() => {
    path = location.pathname.replace(/\/$/, '');
    loadSession();
  });

  const current = (href: string) => (path === href || path.startsWith(`${href}/`) ? 'page' : undefined);
</script>

<nav aria-label="Account">
  <a href="/docs" aria-current={current('/docs')}>docs</a>
  {#if $session}
    <a href="/plugins" aria-current={current('/plugins')}>plugins</a>
    <a href="/subscriptions" aria-current={current('/subscriptions')}><span class="long">subscriptions</span><span class="short">inbox</span></a>
    <span class="who" title={$session.email}>{$session.email}</span>
    <a class="btn btn-sm" href="/accounts/logout/">sign out</a>
  {:else if $session === null}
    <a class="btn btn-sm btn-primary" href="/accounts/login/">sign in</a>
  {/if}
</nav>

<style>
  .who {
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--muted);
    padding: 0 8px;
    border-left: 1px solid var(--border);
    margin-left: 8px;
  }
  .short { display: none; }
  @media (max-width: 640px) {
    .who { display: none; }
  }
  /* The full nav needs ~360px; phones narrower than 400px get the short label. */
  @media (max-width: 400px) {
    .long { display: none; }
    .short { display: inline; }
  }
</style>
