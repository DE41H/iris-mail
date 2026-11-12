<script lang="ts">
  import { onMount } from 'svelte';
  import { fly } from 'svelte/transition';
  import { api, listAll, message, type AgentKey, type Plugin } from '../lib/api';
  import ConfirmButton from './ConfirmButton.svelte';
  import Iris from './Iris.svelte';
  import KeyCard from './KeyCard.svelte';

  let plugins = $state<Plugin[] | null>(null);
  let agents = $state<AgentKey[] | null>(null);
  let error = $state('');
  let name = $state('');
  let creating = $state(false);
  let fresh = $state<{ key: string; path: string } | null>(null);
  let sheet = $state<HTMLDialogElement>();
  let ask = $state<HTMLDialogElement>();
  const saved = (() => { try { return localStorage.getItem('iris-keys'); } catch { return null; } })();
  let kind = $state<'plugin' | 'agent'>(saved === 'agent' ? 'agent' : 'plugin');
  $effect(() => { try { localStorage.setItem('iris-keys', kind); } catch {} });

  onMount(() => {
    listAll<Plugin>('/api/v1/plugins/').then((p) => (plugins = p)).catch((err) => (error = message(err)));
    listAll<AgentKey>('/api/v1/keys/').then((a) => (agents = a)).catch((err) => (error = message(err)));
  });

  // Keys are stored hashed, so the full key can only be copied right after it is made.
  function show(key: string, path: string) {
    fresh = { key, path };
    sheet?.showModal();
  }

  async function rotatePlugin(p: Plugin) {
    try {
      show((await api<{ key: string }>(`/api/v1/plugins/${p.id}/rotate_key/`, { method: 'POST' })).key, '/api/v1/results/?fetched=false');
      p.prefix = (await api<Plugin>(`/api/v1/plugins/${p.id}/`)).prefix;
    } catch (err) {
      error = message(err);
    }
  }

  async function rotateAgent(a: AgentKey) {
    try {
      const { key, prefix } = await api<AgentKey & { key: string }>(`/api/v1/keys/${a.id}/rotate_key/`, { method: 'POST' });
      a.prefix = prefix;
      show(key, '/api/v1/plugins/');
    } catch (err) {
      error = message(err);
    }
  }

  async function create(e: SubmitEvent) {
    e.preventDefault();
    creating = true;
    try {
      const { key, ...made } = await api<AgentKey & { key: string }>('/api/v1/keys/', { method: 'POST', body: JSON.stringify({ name: name.trim() }) });
      agents = [made, ...(agents ?? [])];
      name = '';
      ask?.close();
      kind = 'agent';
      show(key, '/api/v1/plugins/');
    } catch (err) {
      error = message(err);
    } finally {
      creating = false;
    }
  }

  async function revoke(a: AgentKey) {
    try {
      await api(`/api/v1/keys/${a.id}/`, { method: 'DELETE' });
      agents = agents!.filter((k) => k.id !== a.id);
    } catch (err) {
      error = message(err);
    }
  }
</script>

<div class="page-head reveal">
  <div><h1>Your API keys</h1></div>
  <div class="tools">
    {#if kind === 'agent'}
      <button type="button" class="btn btn-primary plus" onclick={() => ask?.showModal()} aria-label="Create agent key" title="Create agent key" transition:fly={{ x: 16, duration: 280 }}>
        <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 3.5v9M3.5 8h9" /></svg>
      </button>
    {/if}
    <div class="kind" class:agent={kind === 'agent'} role="radiogroup" aria-label="Key type">
      <label><input type="radio" bind:group={kind} value="plugin" />Plugin</label>
      <label><input type="radio" bind:group={kind} value="agent" />Agent</label>
    </div>
  </div>
</div>

{#if error}<div class="alert alert-danger" role="alert">{error}</div>{/if}

{#if !plugins || !agents}
  {#if !error}<section class="card list">{@render bones(4)}</section>{/if}
{:else if (kind === 'plugin' ? plugins : agents).length}
  <section class="card list reveal d1" aria-label="API keys">
    <ul class="grow scroll">
      {#if kind === 'plugin'}
      {#each plugins as p (p.id)}
        <li class="row">
          <div class="info">
            <a class="name" href={`/plugins/detail?id=${p.id}`}>{p.name}</a>
            {@render prefix(p.prefix)}
          </div>
          <ConfirmButton label={p.prefix ? 'Rotate' : 'Create key'} onconfirm={() => rotatePlugin(p)} />
        </li>
      {/each}
      {:else}
      {#each agents as a (a.id)}
        <li class="row">
          <div class="info">
            <span class="name">{a.name}</span>
            {@render prefix(a.prefix)}
          </div>
          <ConfirmButton label="Rotate" onconfirm={() => rotateAgent(a)} />
          <ConfirmButton label="Revoke" danger onconfirm={() => revoke(a)} />
        </li>
      {/each}
      {/if}
    </ul>
  </section>
{:else}
  <div class="empty reveal">
    <Iris breathe />
    {#if kind === 'plugin'}
      <h2>No plugin keys yet</h2>
      <p>Each plugin gets its own key to read its results.</p>
      <a class="btn btn-primary" href="/plugins/new">Create a plugin</a>
    {:else}
      <h2>No agent keys yet</h2>
      <p>Agent keys let an agent build plugins for you.</p>
      <button type="button" class="btn btn-primary" onclick={() => ask?.showModal()}>Create agent key</button>
    {/if}
  </div>
{/if}

<dialog class="ask" bind:this={ask} aria-label="New agent key" onclose={() => (name = '')}>
  <form class="card card-body sheet" onsubmit={create}>
    <h2>Name the agent key</h2>
    <input bind:value={name} placeholder="e.g. iris-agent-key" aria-label="Agent key name" maxlength="256" required />
    <div class="actions">
      <button type="button" class="btn btn-ghost" onclick={() => ask?.close()}>Cancel</button>
      <button class="btn btn-primary" disabled={creating || !name.trim()}>{creating ? 'Creating…' : 'Create'}</button>
    </div>
  </form>
</dialog>

<!-- The key is shown once, so only "Done" closes this. Chrome still closes on a second Escape, so reopen right after. -->
<dialog bind:this={sheet} oncancel={(e) => (e.preventDefault(), setTimeout(() => fresh && !sheet?.open && sheet?.showModal()))} aria-label="New API key">
  {#if fresh}
    <div class="sheet">
      {#key fresh.key}<KeyCard key={fresh.key} path={fresh.path} />{/key}
      <div class="actions"><button type="button" class="btn btn-primary" onclick={() => (sheet?.close(), (fresh = null))}>Done</button></div>
    </div>
  {/if}
</dialog>

{#snippet prefix(p: string | null)}
  {#if p}
    <code class="prefix" title="Only the start of the key is kept">{p}<span aria-hidden="true">••••••••</span></code>
  {:else}
    <span class="faint">No key yet</span>
  {/if}
{/snippet}

{#snippet bones(n: number)}
  <div class="skel" role="status" aria-label="Loading keys">
    {#each { length: n } as _}
      <div class="row"><div class="info"><span class="bone sk-name"></span><span class="bone sk-code"></span></div><span class="bone sk-btn"></span></div>
    {/each}
  </div>
{/snippet}

<style>
  .list { display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
  ul { list-style: none; margin: 0; padding: 0; }

  .row { display: flex; align-items: center; gap: 16px; padding: 16px 20px; border-top: 1px solid var(--border); }
  ul .row:first-child, .skel .row:first-child { border-top: 0; }
  .plus { width: 32px; height: 32px; padding: 0; border-radius: 50%; corner-shape: round; display: grid; place-items: center; }
  .plus svg { width: 14px; height: 14px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; }
  .tools { display: flex; align-items: center; justify-content: flex-end; gap: 12px; flex-wrap: wrap; margin-left: auto; }
  /* Two-way switch: the thumb slides under the picked label. */
  .kind { position: relative; display: grid; grid-template-columns: 1fr 1fr; padding: 3px; border-radius: 999px; background: var(--surface-2); border: 1px solid var(--border); }
  .kind::before { content: ''; position: absolute; inset: 3px auto 3px 3px; width: calc(50% - 3px); border-radius: 999px; background: var(--surface); box-shadow: var(--shadow); transition: translate 0.45s var(--spring); }
  .kind.agent::before { translate: 100% 0; }
  .kind label { position: relative; padding: 6px 16px; text-align: center; font-size: 13px; font-weight: 560; color: var(--muted); cursor: pointer; transition: color 0.25s; }
  .kind label:has(:checked) { color: var(--text); }
  .kind label:has(:focus-visible) { outline: 2px solid var(--accent); outline-offset: 1px; border-radius: 999px; }
  .kind input { position: absolute; opacity: 0; pointer-events: none; }
  .info { flex: 1; min-width: 0; display: grid; gap: 4px; }
  .name { font-size: 16px; font-weight: 640; font-stretch: 108%; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  a.name:hover { color: var(--accent); }
  .prefix { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; color: var(--accent); }
  .prefix span { color: var(--faint); letter-spacing: 0.05em; }
  .faint { font-size: 13px; color: var(--faint); }

  .empty { display: grid; gap: 12px; justify-items: center; text-align: center; }
  .empty h2 { color: var(--text); font-size: 20px; }
  .empty p { max-width: 44ch; }

  .sk-name { width: 40%; height: 13px; }
  .sk-code { width: 60%; }
  .sk-btn { width: 76px; height: 36px; border-radius: var(--radius-btn); corner-shape: squircle; }

  .sheet { display: grid; gap: 12px; }
  .ask { width: min(400px, calc(100% - 32px)); }
  .sheet h2 { color: var(--text); font-size: 17px; }

  @media (max-width: 480px) {
    .row { flex-wrap: wrap; justify-content: flex-end; gap: 12px; padding: 14px 16px; }
    .info { flex-basis: 100%; }
  }
</style>
