<script lang="ts">
  import { onMount } from 'svelte';
  import { listAll, message, type Subscription } from '../lib/api';
  import { session } from '../lib/session';
  import Iris from './Iris.svelte';
  import SubscriptionRow from './SubscriptionRow.svelte';

  let subs = $state<Subscription[] | null>(null);
  let error = $state('');

  onMount(() => listAll<Subscription>('/api/v1/subscriptions/').then((s) => (subs = s)).catch((err) => (error = message(err))));
</script>

{#if $session && !$session.google}
  <div class="alert alert-danger" role="alert">Google access was revoked, so sharing is off. <a href="/accounts/google/login/?next=/subscriptions/">Reconnect Google</a></div>
{/if}
{#if error}
  <div class="alert alert-danger" role="alert">{error}</div>
{:else if subs?.length}
  <section class="card reveal list">
    <ul class="grow scroll">
      {#each subs as sub, i (sub.id)}<SubscriptionRow bind:sub={subs[i]} onremove={() => (subs = subs!.filter((s) => s.id !== sub.id))} />{/each}
    </ul>
  </section>
{:else if subs}
  <div class="empty reveal">
    <Iris breathe />
    <h2>Nothing reads your inbox</h2>
    <p>When an app built on Iris asks to read your mail, it shows up here, off until you switch it on.</p>
  </div>
{:else}
  <section class="card list skel" role="status" aria-label="Loading subscriptions">
    {#each { length: 3 } as _}
      <div class="sk-row">
        <div class="sk-info"><span class="bone sk-name"></span><span class="bone sk-desc"></span></div>
        <span class="bone sk-switch"></span>
        <span class="bone sk-btn"></span>
      </div>
    {/each}
  </section>
{/if}

<style>
  .list { display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
  .sk-row { display: flex; align-items: center; gap: 16px; padding: 18px 20px; border-top: 1px solid var(--border); }
  .sk-row:first-child { border-top: 0; }
  .sk-info { flex: 1; display: grid; gap: 8px; }
  .sk-name { width: 30%; height: 13px; }
  .sk-desc { width: 65%; }
  .sk-switch { width: 44px; height: 26px; border-radius: 999px; }
  .sk-btn { width: 78px; height: 34px; border-radius: var(--radius-btn); corner-shape: squircle; }
  .empty { display: grid; gap: 12px; justify-items: center; }
  .empty h2 { color: var(--text); font-size: 20px; }
  .empty p { max-width: 44ch; }
  ul { list-style: none; margin: 0; padding: 0; }
  ul :global(li:first-child) { border-top: 0; }
</style>
