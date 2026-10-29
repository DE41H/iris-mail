<script lang="ts">
  import { onMount } from 'svelte';
  import { loadSession, session } from '#lib/session';

  let { children } = $props();

  onMount(loadSession);
</script>

<header class="topbar">
  <a class="brand mono" href="/plugins/"><span class="brand-mark">✳</span> iris<span class="brand-dot">.</span></a>
  <nav class="account" aria-label="Account">
    {#if $session === null}
      <a class="btn btn-primary btn-sm" href="/accounts/login/">Sign in</a>
    {:else if $session}
      <a href="/plugins/">Plugins</a>
      <a href="/subscriptions/">Subscriptions</a>
      <span class="account-email mono muted">{$session.email}</span>
      <a class="btn btn-sm" href="/accounts/logout/">Sign out</a>
    {/if}
  </nav>
</header>
<main class="container">
  {@render children()}
</main>
