<script lang="ts">
  import { onMount } from 'svelte';
  import { listAll, type Subscription } from '#lib/api';
  import SubscriptionRow from '#lib/components/SubscriptionRow.svelte';

  let subs = $state<Subscription[] | null>(null);
  let error = $state('');

  const replace = (updated: Subscription) => {
    subs = subs?.map((s) => (s.id === updated.id ? updated : s)) ?? null;
  };

  onMount(() => {
    listAll<Subscription>('/api/subscriptions/')
      .then((items) => (subs = items))
      .catch((err) => (error = err.message));
  });
</script>

<svelte:head><title>Subscriptions · Iris</title></svelte:head>

<div class="page-head">
  <div>
    <div class="eyebrow">YOUR INBOX, ON YOUR TERMS <span class="live-dot"></span></div>
    <h1>Subscriptions</h1>
    <p class="muted">Choose the signals you want your inbox to notice.</p>
  </div>
</div>

<ul class="card list subscription-list">
  {#if error}
    <li class="empty">{error}</li>
  {:else if subs === null}
    <li class="empty">Loading…</li>
  {:else if !subs.length}
    <li class="empty">No subscriptions yet. Plugins that a developer adds to your account appear here.</li>
  {:else}
    {#each subs as sub (sub.id)}
      <SubscriptionRow {sub} onupdate={replace} />
    {/each}
  {/if}
</ul>
