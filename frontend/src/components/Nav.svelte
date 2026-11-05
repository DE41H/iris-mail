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
  <a href="/docs" aria-current={current('/docs')}>Docs</a>
  {#if $session}
    <a href="/plugins" aria-current={current('/plugins')}>Plugins</a>
    <a href="/subscriptions" aria-current={current('/subscriptions')}><span class="long">Subscriptions</span><span class="short">Inbox</span></a>
    <span class="who" title={$session.email}>{$session.email}</span>
    <a class="btn btn-sm" href="/accounts/logout/">Sign out</a>
  {:else if $session === null}
    <a class="btn btn-sm btn-primary" href="/accounts/login/">Sign in</a>
  {/if}
</nav>

<style>
  .who {
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--faint);
    font-size: 13px;
    padding: 0 10px 0 14px;
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
