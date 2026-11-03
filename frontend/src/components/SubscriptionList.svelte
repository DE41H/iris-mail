<script lang="ts">
  import { onMount } from 'svelte';
  import { listAll, message, type Subscription } from '../lib/api';
  import SubscriptionRow from './SubscriptionRow.svelte';

  let subs = $state<Subscription[] | null>(null);
  let error = $state('');
  const active = $derived(subs?.filter((s) => s.active).length ?? 0);

  onMount(() => listAll<Subscription>('/api/subscriptions/').then((s) => (subs = s)).catch((err) => (error = message(err))));
</script>

{#if error}
  <div class="alert alert-danger" role="alert">{error}</div>
{:else if subs}
  <section class="card reveal">
    <div class="card-head"><span>{subs.length} {subs.length === 1 ? 'plugin' : 'plugins'}</span><span class="green">{active} on</span></div>
    {#if subs.length}
      <ul>
        {#each subs as _, i (subs[i].id)}<SubscriptionRow bind:sub={subs[i]} />{/each}
      </ul>
    {:else}
      <div class="empty">No subscriptions yet. When a developer adds you to a plugin, it shows up here, turned off.</div>
    {/if}
  </section>
{:else}
  <div class="empty">loading<span class="cursor"></span></div>
{/if}

<style>
  ul { list-style: none; margin: 0; padding: 0; }
  ul :global(li:first-child) { border-top: 0; }
</style>
