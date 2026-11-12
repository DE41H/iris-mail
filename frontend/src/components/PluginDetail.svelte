<script lang="ts">
  import { onMount } from 'svelte';
  import { api, message, type Plugin } from '../lib/api';
  import { fromRules, fromSchema, toBody, type Draft } from '../lib/schema';
  import ConfirmButton from './ConfirmButton.svelte';
  import type Editor from './PluginEditor.svelte';

  // Loads beside the plugin fetch, so the skeleton paints before the editor's code arrives.
  let PluginEditor = $state<typeof Editor>();
  import('./PluginEditor.svelte').then((m) => (PluginEditor = m.default));

  const id = new URLSearchParams(location.search).get('id');
  let plugin = $state<Plugin | null>(null);
  let draft = $state<Draft>({ name: '', desc: '', redirect: '', fields: [], rules: [] });
  let locked = $state('');
  let saved = $state('');
  let shape = $state(''); // questions and rules as saved: changing them starts a new version
  let error = $state('');
  let notice = $state('');

  const snapshot = () => JSON.stringify(draft);
  const shapeOf = () => JSON.stringify([draft.fields, draft.rules]);
  const dirty = $derived(snapshot() !== saved);
  const bumps = $derived(shapeOf() !== shape);
  const next = $derived(plugin ? (plugin.version % 32767) + 1 : 0); // same wrap as PluginSerializer.update

  function fill(p: Plugin) {
    plugin = p;
    const parsed = fromSchema(p.schema);
    locked = 'error' in parsed ? parsed.error : '';
    draft = { name: p.name, desc: p.desc, redirect: p.redirect, fields: 'fields' in parsed ? parsed.fields : [], rules: fromRules(p.rules) };
    saved = snapshot();
    shape = shapeOf();
  }

  onMount(() => {
    if (!id) location.href = '/plugins';
    else api<Plugin>(`/api/v1/plugins/${id}/`).then(fill).catch((err) => (error = message(err)));
  });

  async function save() {
    const p = await api<Plugin>(`/api/v1/plugins/${id}/`, { method: 'PATCH', body: toBody(draft) });
    notice = p.version !== plugin?.version ? `Saved as version ${p.version}.` : 'Changes saved.';
    plugin = { ...plugin, ...p };
    saved = snapshot();
    shape = shapeOf();
    setTimeout(() => (notice = ''), 2500);
  }

  async function remove() {
    try {
      await api(`/api/v1/plugins/${id}/`, { method: 'DELETE' });
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
  {#if plugin && PluginEditor}
    <PluginEditor bind:draft submit="Save" onsubmit={save} {dirty} {locked} steps={false}>
      {#snippet head()}
        <div class="eyebrow"><a href="/plugins">Plugins</a> <span aria-hidden="true">/</span> {plugin!.name}</div>
        <h1>{plugin!.name}</h1>
      {/snippet}
      {#snippet tools()}
        <ConfirmButton label="Delete" danger onconfirm={remove} />
      {/snippet}
      {#snippet aside()}
        <section class="card meta">
          <dl class="stats">
            <div>
              <dt>Version</dt>
              <dd>{plugin!.version}{#if bumps && !locked}<span class="next" title="Saving changed questions or rules starts a new version">→ {next}</span>{/if}</dd>
            </div>
            <div><dt>People</dt><dd>{(plugin!.subscriber_count ?? 0).toLocaleString()}</dd></div>
            <div><dt>Answers</dt><dd>{(plugin!.result_count ?? 0).toLocaleString()}</dd></div>
          </dl>
        </section>
      {/snippet}
      {#if dirty}<button type="button" class="btn btn-ghost" onclick={() => fill(plugin!)}>Discard</button>{/if}
    </PluginEditor>
  {:else if !error}
    <div class="skel sk" role="status" aria-label="Loading plugin">
      <div class="sk-head"><span class="bone" style:width="140px"></span><span class="bone sk-title"></span></div>
      <div class="sk-cols">
        <div class="sk-main">
          {#each [2, 3] as n}
            <div class="card sk-card">
              <span class="bone sk-h2"></span>
              {#each { length: n } as _}<span class="bone sk-field"></span>{/each}
            </div>
          {/each}
        </div>
        <div class="sk-main">
          <div class="card sk-card sk-stats">{#each { length: 3 } as _}<span class="bone sk-stat"></span>{/each}</div>
          <div class="card sk-card sk-out"><span class="bone sk-h2"></span>{#each [80, 55, 65, 40] as w}<span class="bone" style:width={`${w}%`}></span>{/each}</div>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .toast { position: fixed; top: 72px; inset-inline: 0; width: fit-content; margin-inline: auto; z-index: 20; animation: pop 0.45s var(--spring) both; }

  .sk { display: grid; gap: 18px; }
  .sk-head { display: grid; gap: 12px; }
  .sk-title { width: 240px; height: 34px; border-radius: 10px; }
  .sk-cols { display: grid; grid-template-columns: minmax(0, 1fr) minmax(300px, 380px); gap: 16px; align-items: start; }
  .sk-main { display: grid; gap: 16px; }
  .sk-card { display: grid; gap: 14px; padding: 20px 22px; }
  .sk-h2 { width: 110px; height: 15px; margin-bottom: 4px; }
  .sk-field { height: 40px; border-radius: var(--radius-sm); }
  .sk-stats { grid-template-columns: repeat(3, 1fr); padding: 16px 18px; }
  .sk-stat { height: 44px; }
  .sk-out { min-height: 220px; align-content: start; }
  @media (max-width: 960px) { .sk-cols { grid-template-columns: minmax(0, 1fr); } }

  .meta { display: grid; gap: 12px; padding: 16px 18px; }
  .stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); margin: 0; }
  .stats div + div { padding-left: 12px; border-left: 1px solid var(--border); }
  .stats dt { font-size: 12.5px; color: var(--muted); }
  .stats dd { display: flex; align-items: baseline; gap: 6px; margin: 2px 0 0; font-size: 20px; font-weight: 640; font-stretch: 110%; font-variant-numeric: tabular-nums; }
  .next { font-size: 13px; font-weight: 600; color: var(--signal-text); animation: pop 0.35s var(--spring); }
</style>
