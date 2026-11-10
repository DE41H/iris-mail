<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { api, type Plugin } from '../lib/api';
  import { toBody, type Draft } from '../lib/schema';
  import { TEMPLATES, type Template } from '../lib/presets';
  import KeyCard from './KeyCard.svelte';
  import type Editor from './PluginEditor.svelte';

  // The editor (with re2js) is most of this page's code; the templates show while it loads.
  let PluginEditor = $state<typeof Editor>();
  import('./PluginEditor.svelte').then((m) => (PluginEditor = m.default));

  let draft = $state<Draft | null>(null);
  let created = $state<(Plugin & { key: string }) | null>(null);

  function start(t: Template) {
    draft = structuredClone({ name: t.name, desc: t.desc, redirect: '', fields: t.fields, rules: t.rules });
    scrollTo({ top: 0, behavior: 'smooth' });
  }

  async function create() {
    if (draft) created = await api<Plugin & { key: string }>('/api/v1/plugins/', { method: 'POST', body: toBody(draft) });
  }
</script>

{#if created}
  <div class="screen done" in:fly={{ y: 20, duration: 400 }}>
    <div class="page-head">
      <div>
        <div class="eyebrow">Plugin created</div>
        <h1>{created.name}</h1>
      </div>
    </div>
    <KeyCard key={created.key} />
    <div class="actions">
      <a class="btn" href="/plugins">All plugins</a>
      <a class="btn btn-primary" href={`/plugins/detail?id=${created.id}`}>Open plugin</a>
    </div>
  </div>
{:else if draft && PluginEditor}
  <div class="screen" in:fade={{ duration: 200 }}>
    <PluginEditor bind:draft submit="Create plugin" onsubmit={create}>
      {#snippet head()}
        <div class="eyebrow"><button type="button" class="back" onclick={() => (draft = null)}>Templates</button> <span aria-hidden="true">/</span> new</div>
        <h1>New plugin</h1>
      {/snippet}
      <a class="btn btn-ghost" href="/plugins">Cancel</a>
    </PluginEditor>
  </div>
{:else}
  <div class="screen">
    <div class="page-head reveal">
      <div>
        <div class="eyebrow"><a href="/plugins">Plugins</a> <span aria-hidden="true">/</span> new</div>
        <h1>Start from a template</h1>
      </div>
    </div>
    <div class="templates grow scroll">
      {#each TEMPLATES as t, i}
        <button type="button" class="card tpl reveal" style:--i={i + 1} onclick={() => start(t)}>
          <span class="title">{t.title}</span>
          <span class="muted">{t.blurb}</span>
          <span class="kinds">
            {#each t.fields as f}<span class="chip">{f.name}</span>{/each}
            {#each t.rules as r}<span class="chip rule" title="Rule">{r.name}</span>{/each}
          </span>
          <span class="go">Use this template</span>
        </button>
      {/each}
    </div>
  </div>
{/if}

<style>
  .templates { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(240px, 100%), 1fr)); grid-auto-rows: max-content; align-content: start; gap: 14px; padding: 4px; margin: -4px; }
  .tpl {
    display: grid;
    align-content: start;
    gap: 8px;
    padding: 18px;
    text-align: left;
    color: inherit;
    font: inherit;
    cursor: pointer;
    transition: border-color 0.25s, translate 0.35s var(--ease), box-shadow 0.35s var(--ease);
  }
  .tpl:hover, .tpl:focus-visible { border-color: color-mix(in oklab, var(--accent) 45%, var(--border)); translate: 0 -3px; box-shadow: var(--shadow-lift); }
  .tpl:active { translate: 0 -1px; }
  .title { font-size: 17px; font-weight: 640; font-stretch: 110%; }
  .kinds { display: flex; flex-wrap: wrap; gap: 4px; }
  .rule { color: var(--signal-text); background: var(--signal-soft); border-color: transparent; }
  .go { margin-top: 4px; font-size: 13px; font-weight: 560; color: var(--accent); opacity: 0; translate: -6px 0; transition: opacity 0.25s, translate 0.35s var(--spring); }
  .tpl:hover .go, .tpl:focus-visible .go { opacity: 1; translate: 0; }
  @media (hover: none) { .go { opacity: 1; translate: 0; } }
  .done { width: 100%; max-width: 760px; margin-inline: auto; justify-content: center; }
  .back { background: none; border: 0; padding: 0; font: inherit; color: inherit; cursor: pointer; text-decoration: underline; text-underline-offset: 3px; }
</style>
