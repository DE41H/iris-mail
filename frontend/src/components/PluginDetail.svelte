<script lang="ts">
  import { onMount } from 'svelte';
  import { api, message, type Plugin } from '../lib/api';
  import { fromRules, fromSchema, toRules, toSchema, type Draft } from '../lib/schema';
  import ConfirmButton from './ConfirmButton.svelte';
  import KeyCard from './KeyCard.svelte';
  import PluginEditor from './PluginEditor.svelte';

  const id = new URLSearchParams(location.search).get('id');
  let plugin = $state<Plugin | null>(null);
  let draft = $state<Draft>({ name: '', desc: '', fields: [], rules: [] });
  let locked = $state('');
  let saved = $state('');
  let key = $state('');
  let error = $state('');
  let notice = $state('');
  let sheet = $state<HTMLDialogElement>();

  const snapshot = () => JSON.stringify(draft);
  const dirty = $derived(snapshot() !== saved);

  function fill(p: Plugin) {
    plugin = p;
    const parsed = fromSchema(p.schema);
    locked = 'error' in parsed ? parsed.error : '';
    draft = { name: p.name, desc: p.desc, fields: 'fields' in parsed ? parsed.fields : [], rules: fromRules(p.rules) };
    saved = snapshot();
  }

  onMount(() => {
    if (!id) location.href = '/plugins';
    else api<Plugin>(`/api/plugins/${id}/`).then(fill).catch((err) => (error = message(err)));
  });

  async function save() {
    const { fields, rules, ...rest } = draft;
    const body = { ...rest, schema: toSchema(fields), rules: toRules(rules) };
    const p = await api<Plugin>(`/api/plugins/${id}/`, { method: 'PATCH', body: JSON.stringify(body) });
    plugin = p;
    saved = snapshot();
    notice = 'Changes saved.';
    setTimeout(() => (notice = ''), 2500);
  }

  async function rotate() {
    try {
      key = (await api<{ key: string }>(`/api/plugins/${id}/rotate_key/`, { method: 'POST' })).key;
      sheet?.showModal();
      const fresh = await api<Plugin>(`/api/plugins/${id}/`);
      if (plugin) plugin.prefix = fresh.prefix;
    } catch (err) {
      error = message(err);
    }
  }

  async function remove() {
    try {
      await api(`/api/plugins/${id}/`, { method: 'DELETE' });
      saved = snapshot(); // the plugin is gone, so there is nothing left to warn about
      location.href = '/plugins';
    } catch (err) {
      error = message(err);
    }
  }
</script>

<svelte:window onbeforeunload={(e) => dirty && e.preventDefault()} />

{#if notice}<div class="alert alert-success toast" role="status">{notice}</div>{/if}

<div class="screen">
  {#if error}<div class="alert alert-danger" role="alert">{error}</div>{/if}
  {#if plugin}
    <PluginEditor bind:draft submit="Save changes" onsubmit={save} {dirty} {locked}>
      {#snippet head()}
        <div class="eyebrow"><a href="/plugins">Plugins</a> <span aria-hidden="true">/</span> version {plugin!.version}{#if plugin!.prefix} <span aria-hidden="true">/</span> key <code>{plugin!.prefix}…</code>{/if}</div>
        <h1>{plugin!.name}</h1>
      {/snippet}
      {#if dirty}<button type="button" class="btn btn-ghost" onclick={() => fill(plugin!)}>Discard</button>{/if}
      <ConfirmButton label="New key" confirm="Replace the key?" onconfirm={rotate} />
      <ConfirmButton label="Delete" confirm="Delete for good?" danger onconfirm={remove} />
    </PluginEditor>
  {/if}
</div>

<!-- Escape is ignored: the key is shown once, so only "Done" closes it. -->
<dialog bind:this={sheet} oncancel={(e) => e.preventDefault()} onclose={() => (key = '')} aria-label="New API key">
  {#if key}
    <div class="sheet">
      <KeyCard {key} />
      <form method="dialog" class="actions"><button class="btn btn-primary">Done, I copied it</button></form>
    </div>
  {/if}
</dialog>

<style>
  .toast { position: fixed; top: 72px; left: 50%; translate: -50% 0; z-index: 20; animation: pop 0.45s var(--spring) both; }
  .sheet { display: grid; gap: 12px; }
</style>
