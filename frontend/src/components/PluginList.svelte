<script lang="ts">
  import { onMount } from 'svelte';
  import { listAll, message, type Plugin } from '../lib/api';
  import { fromSchema } from '../lib/schema';
  import { KINDS } from '../lib/presets';

  let plugins = $state<Plugin[] | null>(null);
  let error = $state('');

  onMount(() => listAll<Plugin>('/api/plugins/').then((p) => (plugins = p)).catch((err) => (error = message(err))));

  const questions = (p: Plugin) => {
    const parsed = fromSchema(p.schema);
    return 'fields' in parsed ? parsed.fields : [];
  };
  const icon = (kind: string) => KINDS.find((k) => k.kind === kind)?.icon;
  const plural = (n: number | undefined, word: string) => (n === 1 ? word : `${word}s`);
</script>

{#if error}
  <div class="alert alert-danger" role="alert">{error}</div>
{:else if !plugins}
  <div class="grid">
    {#each { length: 3 } as _, i}<div class="card skeleton reveal" style:--i={i}></div>{/each}
  </div>
{:else if !plugins.length}
  <div class="card empty reveal">
    <h2>No plugins yet</h2>
    <p>Start from a template and you'll have an API key in a minute.</p>
    <p><a class="btn btn-primary" href="/plugins/new">Create a plugin</a></p>
  </div>
{:else}
  <div class="grid grow scroll">
    {#each plugins as p, i (p.id)}
      {@const fields = questions(p)}
      <a class="card plugin reveal" style:--i={i} href={`/plugins/detail?id=${p.id}`}>
        <div class="top">
          <span class="name">{p.name}</span>
          <span class="chip" class:on={p.prefix}>{p.prefix ? 'Key active' : 'No key'}</span>
        </div>
        {#if p.desc}<p class="muted desc">{p.desc}</p>{/if}
        <div class="fields">
          {#each fields.slice(0, 5) as f}<span class="chip"><span class="ico">{icon(f.kind)}</span>{f.name}</span>{/each}
          {#if fields.length > 5}<span class="chip">+{fields.length - 5}</span>{/if}
        </div>
        <div class="stats">
          <span><b>{p.subscriber_count ?? 0}</b> {plural(p.subscriber_count, 'subscriber')}</span>
          <span><b>{p.result_count ?? 0}</b> {plural(p.result_count, 'result')}</span>
        </div>
        <div class="foot mono">
          <span>{fields.length} {plural(fields.length, 'question')}</span>
          {#if p.prefix}<span>{p.prefix}…</span>{/if}
        </div>
      </a>
    {/each}
  </div>
{/if}

<style>
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(300px, 100%), 1fr)); align-content: start; gap: 14px; padding: 4px; margin: -4px; }
  .plugin {
    display: grid;
    gap: 10px;
    padding: 18px;
    color: var(--text);
    position: relative;
    overflow: hidden;
    transition: border-color 0.25s, translate 0.35s var(--ease), box-shadow 0.35s var(--ease);
  }
  .plugin:hover { color: var(--text); border-color: color-mix(in oklab, var(--accent) 45%, var(--border)); translate: 0 -3px; box-shadow: var(--shadow-lift); }
  .plugin:active { translate: 0 -1px; }
  .top { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
  .top .chip { flex-shrink: 0; white-space: nowrap; }
  .name { font-size: 17px; font-weight: 640; font-stretch: 110%; letter-spacing: -0.01em; overflow: hidden; text-overflow: ellipsis; }
  .ico { color: var(--accent); }
  .desc { display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .fields { display: flex; flex-wrap: wrap; gap: 4px; }
  .fields .chip { overflow-wrap: anywhere; }
  .stats { display: flex; gap: 20px; font-size: 13px; color: var(--muted); }
  .stats b { display: block; color: var(--text); font-size: 22px; font-weight: 680; font-stretch: 115%; line-height: 1.1; font-variant-numeric: tabular-nums; }
  .foot { display: flex; justify-content: space-between; font-size: 12px; color: var(--muted); padding-top: 10px; border-top: 1px solid var(--border); }
  .skeleton { height: 220px; }
  .empty { display: grid; gap: 10px; justify-items: center; }
  .empty h2 { color: var(--text); font-size: 20px; }
</style>
