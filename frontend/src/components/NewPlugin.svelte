<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { api, type Plugin } from '../lib/api';
  import { toSchema, type Draft } from '../lib/schema';
  import { clone, TEMPLATES, type Template } from '../lib/presets';
  import KeyCard from './KeyCard.svelte';
  import PluginEditor from './PluginEditor.svelte';

  let draft = $state<Draft | null>(null);
  let created = $state<(Plugin & { key: string }) | null>(null);

  function start(t: Template) {
    draft = clone({ name: t.name, desc: t.desc, hint: t.hint, fields: t.fields });
    scrollTo({ top: 0, behavior: 'smooth' });
  }

  async function create() {
    if (!draft) return;
    const { fields, ...rest } = draft;
    created = await api<Plugin & { key: string }>('/api/plugins/', {
      method: 'POST',
      body: JSON.stringify({ ...rest, schema: toSchema(fields) }),
    });
  }
</script>

{#if created}
  <div class="screen done" in:fly={{ y: 20, duration: 400 }}>
    <div class="page-head">
      <div>
        <div class="eyebrow">plugin created</div>
        <h1 class="mono">{created.name}<span class="cursor"></span></h1>
      </div>
    </div>
    <KeyCard key={created.key} />
    <div class="actions">
      <a class="btn" href="/plugins">all plugins</a>
      <a class="btn btn-primary" href={`/plugins/detail?id=${created.id}`}>open plugin →</a>
    </div>
  </div>
{:else if draft}
  <div class="screen" in:fade={{ duration: 200 }}>
    <PluginEditor bind:draft submit="create" onsubmit={create}>
      {#snippet head()}
        <div class="eyebrow"><button type="button" class="back" onclick={() => (draft = null)}>templates</button> / new</div>
        <h1>New plugin<span class="cursor"></span></h1>
      {/snippet}
      <a class="btn btn-ghost" href="/plugins">cancel</a>
    </PluginEditor>
  </div>
{:else}
  <div class="screen">
    <div class="page-head reveal">
      <div>
        <div class="eyebrow">plugins / new</div>
        <h1>Pick a template<span class="cursor"></span></h1>
      </div>
    </div>
    <div class="templates grow scroll">
      {#each TEMPLATES as t, i}
        <button type="button" class="card tpl reveal" style:--i={i + 1} onclick={() => start(t)}>
          <span class="title">{t.title}</span>
          <span class="muted">{t.blurb}</span>
          <span class="kinds">
            {#each t.fields as f}<span class="chip">{f.name}</span>{/each}
          </span>
          <span class="go">use →</span>
        </button>
      {/each}
    </div>
  </div>
{/if}

<style>
  .templates { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); align-content: start; gap: 14px; padding: 4px; margin: -4px; }
  .tpl {
    display: grid;
    align-content: start;
    gap: 8px;
    padding: 18px;
    text-align: left;
    color: inherit;
    font: inherit;
    cursor: pointer;
    transition: border-color 0.25s, transform 0.25s var(--ease), box-shadow 0.25s;
  }
  .tpl:hover, .tpl:focus-visible { border-color: var(--green); transform: translateY(-3px); box-shadow: 0 12px 32px rgba(61, 220, 132, 0.08); }
  .title { font: 600 15px var(--mono); }
  .kinds { display: flex; flex-wrap: wrap; gap: 4px; }
  .go { font: 12px var(--mono); color: var(--green); opacity: 0; transform: translateX(-6px); transition: 0.25s var(--ease); }
  .tpl:hover .go, .tpl:focus-visible .go { opacity: 1; transform: none; }
  .done { max-width: 760px; justify-content: center; }
  .back { background: none; border: 0; padding: 0; font: inherit; color: inherit; cursor: pointer; text-decoration: underline; text-underline-offset: 3px; }
</style>
