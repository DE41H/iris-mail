<script lang="ts">
  import { onMount } from 'svelte';
  import { listAll } from '#lib/api';

  interface Plugin {
    id: string;
    name: string;
    desc: string;
    hint: string;
    prefix: string | null;
  }

  let plugins = $state<Plugin[] | null>(null);
  let error = $state('');

  onMount(() => {
    listAll<Plugin>('/api/plugins/')
      .then((items) => (plugins = items))
      .catch((err) => (error = err.message));
  });
</script>

<svelte:head><title>Plugins · Iris</title></svelte:head>

<div class="page-head">
  <div>
    <div class="eyebrow">YOUR WORKSPACE <span class="live-dot"></span></div>
    <h1>Plugins</h1>
    <p class="muted">Small, focused agents that turn email into useful data.</p>
  </div>
  <a class="btn btn-primary" href="/plugins/new/"><span>＋</span> Create plugin</a>
</div>

<ul class="card list plugin-list">
  {#if error}
    <li class="empty">{error}</li>
  {:else if plugins === null}
    <li class="empty">Loading…</li>
  {:else if !plugins.length}
    <li class="empty">No plugins yet. Create one to get an API key.</li>
  {:else}
    {#each plugins as plugin (plugin.id)}
      <li class="row plugin-row">
        <div class="grow">
          <span class="row-kicker">EMAIL AGENT</span>
          <a class="title mono" href="/plugins/detail/?id={plugin.id}">{plugin.name}</a>
          <div class="muted">{plugin.desc || plugin.hint || 'No description yet'}</div>
        </div>
        {#if plugin.prefix}<span class="mono muted">{plugin.prefix}…</span>{/if}
      </li>
    {/each}
  {/if}
</ul>
