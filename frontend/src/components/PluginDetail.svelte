<script lang="ts">
  import { onMount } from 'svelte';
  import { api, message, type Plugin } from '../lib/api';
  import { fromSchema, toSchema, type Draft } from '../lib/schema';
  import ConfirmButton from './ConfirmButton.svelte';
  import KeyCard from './KeyCard.svelte';
  import PluginEditor from './PluginEditor.svelte';

  const id = new URLSearchParams(location.search).get('id');
  let plugin = $state<Plugin | null>(null);
  let draft = $state<Draft>({ name: '', desc: '', hint: '', fields: [] });
  let locked = $state('');
  let saved = $state('');
  let key = $state('');
  let error = $state('');
  let notice = $state('');

  const snapshot = () => JSON.stringify(draft);
  const dirty = $derived(snapshot() !== saved);

  function fill(p: Plugin) {
    plugin = p;
    const parsed = fromSchema(p.schema);
    locked = 'error' in parsed ? parsed.error : '';
    draft = { name: p.name, desc: p.desc, hint: p.hint, fields: 'fields' in parsed ? parsed.fields : [] };
    saved = snapshot();
  }

  onMount(() => {
    if (!id) location.href = '/plugins';
    else api<Plugin>(`/api/plugins/${id}/`).then(fill).catch((err) => (error = message(err)));
  });

  async function save() {
    const { fields, ...rest } = draft;
    const p = await api<Plugin>(`/api/plugins/${id}/`, { method: 'PATCH', body: JSON.stringify({ ...rest, schema: toSchema(fields) }) });
    plugin = p;
    saved = snapshot();
    notice = 'Changes saved.';
    setTimeout(() => (notice = ''), 2500);
  }

  async function rotate() {
    try {
      key = (await api<{ key: string }>(`/api/plugins/${id}/rotate_key/`, { method: 'POST' })).key;
      const fresh = await api<Plugin>(`/api/plugins/${id}/`);
      if (plugin) plugin.prefix = fresh.prefix;
    } catch (err) {
      error = message(err);
    }
  }

  async function remove() {
    try {
      await api(`/api/plugins/${id}/`, { method: 'DELETE' });
      location.href = '/plugins';
    } catch (err) {
      error = message(err);
    }
  }
</script>

<svelte:window onbeforeunload={(e) => dirty && e.preventDefault()} />

<div class="page-head reveal">
  <div>
    <div class="eyebrow"><a href="/plugins">plugins</a> / {plugin?.name ?? '…'}</div>
    <h1 class="mono">{plugin?.name ?? 'loading'}<span class="cursor"></span></h1>
    <p>Edit the questions, rotate the key, or delete the plugin.</p>
  </div>
  {#if notice}<div class="alert alert-success" role="status">✓ {notice}</div>{/if}
</div>

{#if error}<div class="alert alert-danger" role="alert">{error}</div>{/if}

{#if plugin}
  <div class="stack">
    <PluginEditor bind:draft submit="save changes" onsubmit={save} {dirty} {locked}>
      {#if dirty}<button type="button" class="btn btn-ghost" onclick={() => fill(plugin!)}>discard</button>{/if}
    </PluginEditor>

    <div class="grid-2 lower">
      <section class="card reveal" style:--i={4}>
        <div class="card-head"><span>03 / access</span><span class="mono">{plugin.prefix ? `${plugin.prefix}…` : 'no key'}</span></div>
        <div class="card-body stack">
          <p class="muted">Rotating issues a new key. The current one stops working immediately.</p>
          <div><ConfirmButton label="rotate key" confirm="confirm rotate" onconfirm={rotate} /></div>
        </div>
      </section>
      <section class="card danger reveal" style:--i={5}>
        <div class="card-head"><span>04 / danger zone</span></div>
        <div class="card-body stack">
          <p class="muted">Deletes the plugin, its subscriptions and its results. This cannot be undone.</p>
          <div><ConfirmButton label="delete plugin" confirm="really delete?" danger onconfirm={remove} /></div>
        </div>
      </section>
    </div>
    {#if key}<KeyCard {key} />{/if}
  </div>
{/if}

<style>
  .lower { align-items: stretch; }
  .eyebrow a { color: inherit; }
</style>
