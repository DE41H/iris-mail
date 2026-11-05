<script lang="ts">
  import { onMount } from 'svelte';
  import { listAll, message, type Subscription } from '../lib/api';
  import { session } from '../lib/session';
  import SubscriptionRow from './SubscriptionRow.svelte';

  let subs = $state<Subscription[] | null>(null);
  let error = $state('');
  const active = $derived(subs?.filter((s) => s.active).length ?? 0);

  onMount(() => listAll<Subscription>('/api/subscriptions/').then((s) => (subs = s)).catch((err) => (error = message(err))));
</script>

{#if $session && !$session.google}
  <div class="alert alert-danger" role="alert">Google access was revoked, so sharing is off. <a href="/accounts/google/login/?next=/subscriptions/">Reconnect Google</a></div>
{/if}
{#if error}
  <div class="alert alert-danger" role="alert">{error}</div>
{:else if subs}
  <section class="card reveal list">
    <div class="card-head"><span>{subs.length} {subs.length === 1 ? 'plugin' : 'plugins'}</span><span class="count" class:live={active}>{active} on</span></div>
    {#if subs.length}
      <ul class="grow scroll">
        {#each subs as sub, i (sub.id)}<SubscriptionRow bind:sub={subs[i]} onremove={() => (subs = subs!.filter((s) => s.id !== sub.id))} />{/each}
      </ul>
    {:else}
      <div class="empty">When an app built on Iris asks to read your mail, it shows up here, off until you switch it on.</div>
    {/if}
  </section>
{:else}
  <div class="card skeleton list-skel"></div>
{/if}

<style>
  .list { display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
  .list-skel { height: 240px; }
  .count { display: inline-flex; align-items: center; gap: 7px; }
  .count.live { color: var(--accent); }
  .count.live::before { content: ''; width: 7px; height: 7px; border-radius: 50%; background: currentColor; box-shadow: 0 0 0 0 currentColor; animation: ping 2s var(--ease) infinite; }
  @keyframes ping { 70%, 100% { box-shadow: 0 0 0 6px transparent; } }
  ul { list-style: none; margin: 0; padding: 0; }
  ul :global(li:first-child) { border-top: 0; }
</style>
