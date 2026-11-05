<script lang="ts">
  import { onMount } from 'svelte';
  import { api, message, type Plugin } from '../lib/api';
  import { fromRules, fromSchema, toBody, type Draft } from '../lib/schema';
  import ConfirmButton from './ConfirmButton.svelte';
  import KeyCard from './KeyCard.svelte';
  import PluginEditor from './PluginEditor.svelte';

  const id = new URLSearchParams(location.search).get('id');
  let plugin = $state<Plugin | null>(null);
  let draft = $state<Draft>({ name: '', desc: '', fields: [], rules: [] });
  let locked = $state('');
  let saved = $state('');
  let shape = $state(''); // questions and rules as saved: changing them starts a new version
  let key = $state('');
  let error = $state('');
  let notice = $state('');
  let sheet = $state<HTMLDialogElement>();

  const snapshot = () => JSON.stringify(draft);
  const shapeOf = () => JSON.stringify([draft.fields, draft.rules]);
  const dirty = $derived(snapshot() !== saved);
  const bumps = $derived(shapeOf() !== shape);
  const next = $derived(plugin ? (plugin.version % 32767) + 1 : 0); // same wrap as PluginSerializer.update

  function fill(p: Plugin) {
    plugin = p;
    const parsed = fromSchema(p.schema);
    locked = 'error' in parsed ? parsed.error : '';
    draft = { name: p.name, desc: p.desc, fields: 'fields' in parsed ? parsed.fields : [], rules: fromRules(p.rules) };
    saved = snapshot();
    shape = shapeOf();
  }

  onMount(() => {
    if (!id) location.href = '/plugins';
    else api<Plugin>(`/api/plugins/${id}/`).then(fill).catch((err) => (error = message(err)));
  });

  async function save() {
    const p = await api<Plugin>(`/api/plugins/${id}/`, { method: 'PATCH', body: toBody(draft) });
    notice = p.version !== plugin?.version ? `Saved as version ${p.version}.` : 'Changes saved.';
    plugin = { ...plugin, ...p };
    saved = snapshot();
    shape = shapeOf();
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
    <PluginEditor bind:draft submit="Save changes" onsubmit={save} {dirty} {locked} steps={false}>
      {#snippet head()}
        <div class="eyebrow"><a href="/plugins">Plugins</a> <span aria-hidden="true">/</span> {plugin!.name}</div>
        <h1>{plugin!.name}</h1>
      {/snippet}
      {#snippet tools()}
        <ConfirmButton label="Delete plugin" confirm="Delete for good?" danger onconfirm={remove} />
      {/snippet}
      {#snippet aside()}
        <section class="card meta">
          <div class="key">
            <div class="key-text">
              <h2>API key</h2>
              {#if plugin!.prefix}
                <code class="prefix" title="Only the start of the key is kept">{plugin!.prefix}<span aria-hidden="true">••••••••••••</span></code>
              {:else}
                <span class="muted">No key yet</span>
              {/if}
            </div>
            <ConfirmButton label={plugin!.prefix ? 'Rotate' : 'Create key'} confirm={plugin!.prefix ? 'Old key stops. Sure?' : 'Create?'} onconfirm={rotate} />
          </div>
          <dl class="stats">
            <div>
              <dt>Version</dt>
              <dd>{plugin!.version}{#if bumps && !locked}<span class="next" title="Saving changed questions or rules starts a new version">→ {next}</span>{/if}</dd>
            </div>
            <div><dt>Users</dt><dd>{plugin!.subscriber_count ?? 0}</dd></div>
            <div><dt>Results</dt><dd>{plugin!.result_count ?? 0}</dd></div>
          </dl>
          {#if bumps && !locked}<p class="help bump">Saving starts version {next}.</p>{/if}
        </section>
      {/snippet}
      {#if dirty}<button type="button" class="btn btn-ghost" onclick={() => fill(plugin!)}>Discard</button>{/if}
    </PluginEditor>
  {/if}
</div>

<!-- The key is shown once, so only "Done" closes this. Chrome still closes on a second Escape, so reopen right after. -->
<dialog bind:this={sheet} oncancel={(e) => (e.preventDefault(), setTimeout(() => key && !sheet?.open && sheet?.showModal()))} aria-label="New API key">
  {#if key}
    <div class="sheet">
      <KeyCard {key} />
      <div class="actions"><button type="button" class="btn btn-primary" onclick={() => (sheet?.close(), (key = ''))}>Done, I copied it</button></div>
    </div>
  {/if}
</dialog>

<style>
  .toast { position: fixed; top: 72px; left: 50%; translate: -50% 0; z-index: 20; animation: pop 0.45s var(--spring) both; }
  .sheet { display: grid; gap: 12px; }

  .meta { display: grid; gap: 12px; padding: 16px 18px; }
  .key { display: flex; align-items: center; gap: 12px; }
  .key-text { flex: 1; min-width: 0; display: grid; gap: 6px; }
  .key h2 { font-size: 15px; color: var(--text); }
  .prefix { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13.5px; color: var(--accent); }
  .prefix span { color: var(--faint); letter-spacing: 0.05em; }
  .help { margin: 0; font-size: 12.5px; line-height: 1.45; }
  .stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); margin: 0; padding-top: 12px; border-top: 1px solid var(--border); }
  .stats div + div { padding-left: 12px; border-left: 1px solid var(--border); }
  .stats dt { font-size: 12.5px; color: var(--muted); }
  .stats dd { display: flex; align-items: baseline; gap: 6px; margin: 2px 0 0; font-size: 20px; font-weight: 640; font-stretch: 110%; font-variant-numeric: tabular-nums; }
  .next { font-size: 13px; font-weight: 600; color: var(--signal-text); animation: pop 0.35s var(--spring); }
  .bump { color: var(--signal-text); }
</style>
