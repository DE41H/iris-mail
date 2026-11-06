<script lang="ts">
  import { onMount } from 'svelte';
  import { loadSession, session } from '../lib/session';
  import DeleteAccount from './DeleteAccount.svelte';

  let path = $state('');
  let broken = $state(false);
  let open = $state(false);
  let account: HTMLElement;

  onMount(() => {
    path = location.pathname.replace(/\/$/, '');
    loadSession();
  });

  const current = (href: string) => (path === href || path.startsWith(`${href}/`) ? 'page' : undefined);

  // Close on a click or tab outside; iOS doesn't focus tapped buttons, so focusout alone misses taps.
  const outside = (e: Event) => open && !account?.contains(e.target as Node) && (open = false);
  const leave = (e: FocusEvent) => e.relatedTarget && !account.contains(e.relatedTarget as Node) && (open = false);
  const key = (e: KeyboardEvent) => {
    if (e.key !== 'Escape' || !open) return;
    open = false;
    account.querySelector('button')?.focus();
  };
</script>

<svelte:window onclick={outside} />

<nav aria-label="Account">
  <a href="/docs" aria-current={current('/docs')}>Docs</a>
  {#if $session}
    <a href="/plugins" aria-current={current('/plugins')}>Plugins</a>
    <a href="/subscriptions" aria-current={current('/subscriptions')}><span class="long">Subscriptions</span><span class="short">Inbox</span></a>
    <div class="account" bind:this={account} onfocusout={leave} onkeydown={key} role="presentation">
      <button type="button" class="face" aria-label="Account" aria-haspopup="true" aria-expanded={open} onclick={() => (open = !open)}>
        {#if $session.avatar && !broken}
          <img class="avatar" src={$session.avatar} alt="" referrerpolicy="no-referrer" onerror={() => (broken = true)} />
        {:else}
          <span class="avatar">{$session.email[0].toUpperCase()}</span>
        {/if}
      </button>
      <div class="menu" class:open inert={!open}>
        <div class="who">
          <span class="email" title={$session.email}>{$session.email}</span>
          <span class="chip on">{$session.tier_name} tier</span>
        </div>
        <a class="item" href="/accounts/logout/">Sign out</a>
        <DeleteAccount />
      </div>
    </div>
  {:else if $session === null}
    <a class="btn btn-sm btn-primary" href="/accounts/login/">Sign in</a>
  {/if}
</nav>

<style>
  .account {
    position: relative;
    display: flex;
    padding-left: 12px;
    border-left: 1px solid var(--border);
    margin-left: 8px;
  }
  .face {
    padding: 0;
    border: 0;
    background: none;
    cursor: pointer;
    border-radius: 30%;
  }
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
  .face:hover .avatar,
  .face[aria-expanded='true'] .avatar { box-shadow: 0 0 0 3px var(--accent-soft); }
  @supports (corner-shape: squircle) {
    .avatar, .face { border-radius: 50%; corner-shape: squircle; }
  }

  .menu {
    position: absolute;
    top: calc(100% + 12px);
    right: 0;
    width: 240px;
    padding: 6px;
    display: grid;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    box-shadow: var(--shadow-lift);
    transform-origin: top right;
    opacity: 0;
    visibility: hidden;
    translate: 0 -6px;
    scale: 0.96;
    transition: opacity 0.18s var(--ease), translate 0.28s var(--ease), scale 0.28s var(--ease), visibility 0s 0.28s;
  }
  .menu.open { opacity: 1; visibility: visible; translate: 0; scale: 1; transition-delay: 0s; }

  .who {
    display: grid;
    gap: 6px;
    justify-items: start;
    padding: 8px 10px 12px;
    margin-bottom: 4px;
    border-bottom: 1px solid var(--border);
  }
  .email {
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--muted);
    font-size: 13px;
  }

  .item,
  .menu :global(.btn) {
    display: block;
    width: 100%;
    padding: 8px 10px;
    border: 0;
    border-radius: 6px;
    background: none;
    color: var(--text);
    font: inherit;
    font-size: 14px;
    text-align: left;
    text-decoration: none;
    transition: background 0.15s;
  }
  .item:hover { background: var(--accent-soft); }
  .menu :global(.btn-danger) { color: var(--danger); }
  .menu :global(.btn-danger:hover) { background: var(--danger-soft); }
  .menu :global(.leave) { justify-items: stretch; }
  .menu :global(.alert) { margin: 4px; font-size: 13px; }

  .short { display: none; }
  /* The full nav needs ~360px; phones narrower than 400px get the short label. */
  @media (max-width: 400px) {
    .long { display: none; }
    .short { display: inline; }
  }
</style>
