<script lang="ts">
  import { onMount } from 'svelte';
  import { fade } from 'svelte/transition';
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

<svelte:window onbeforeunload={(e) => dirty && e.preventDefault()} onkeydown={(e) => e.key === 'Escape' && (key = '')} />

{#if notice}<div class="alert alert-success toast" role="status">✓ {notice}</div>{/if}

<div class="screen">
  {#if error}<div class="alert alert-danger" role="alert">{error}</div>{/if}
  {#if plugin}
    <PluginEditor bind:draft submit="save" onsubmit={save} {dirty} {locked}>
      {#snippet head()}
        <div class="eyebrow"><a href="/plugins">plugins</a> / {plugin!.prefix ? `${plugin!.prefix}…` : 'no key'}</div>
        <h1 class="mono">{plugin!.name}<span class="cursor"></span></h1>
      {/snippet}
      {#if dirty}<button type="button" class="btn btn-ghost" onclick={() => fill(plugin!)}>discard</button>{/if}
      <ConfirmButton label="rotate key" confirm="confirm rotate" onconfirm={rotate} />
      <ConfirmButton label="delete" confirm="really delete?" danger onconfirm={remove} />
    </PluginEditor>
  {/if}
</div>

{#if key}
  <div class="overlay" transition:fade={{ duration: 150 }}>
    <div class="sheet">
      <KeyCard {key} />
      <div class="actions"><button type="button" class="btn" onclick={() => (key = '')}>done</button></div>
    </div>
  </div>
{/if}

<style>
  .eyebrow a { color: inherit; }
  .toast { position: fixed; top: 68px; left: 50%; translate: -50% 0; z-index: 20; }
  .overlay { position: fixed; inset: 0; z-index: 30; display: grid; place-items: center; padding: 16px; background: rgba(5, 8, 7, 0.8); backdrop-filter: blur(6px); }
  .sheet { width: min(720px, 100%); display: grid; gap: 12px; }
</style>
