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
</script>

{#if error}
  <div class="alert alert-danger" role="alert">{error}</div>
{:else if !plugins}
  <div class="grid">
    {#each { length: 3 } as _}<div class="card skeleton"></div>{/each}
  </div>
{:else if !plugins.length}
  <div class="card empty reveal">
    <p>No plugins yet.</p>
    <p><a class="btn btn-primary" href="/plugins/new">+ create one</a></p>
  </div>
{:else}
  <div class="grid grow scroll">
    {#each plugins as p, i (p.id)}
      {@const fields = questions(p)}
      <a class="card plugin reveal" style:--i={i} href={`/plugins/detail?id=${p.id}`}>
        <div class="top">
          <span class="name">{p.name}</span>
          <span class="chip" class:on={p.prefix}>{p.prefix ? 'key active' : 'no key'}</span>
        </div>
        {#if p.desc}<p class="muted desc">{p.desc}</p>{/if}
        <div class="fields">
          {#each fields.slice(0, 5) as f}<span class="chip"><span class="green">{icon(f.kind)}</span>{f.name}</span>{/each}
          {#if fields.length > 5}<span class="chip">+{fields.length - 5}</span>{/if}
        </div>
        <div class="foot mono">
          <span>{fields.length} {fields.length === 1 ? 'question' : 'questions'}</span>
          {#if p.prefix}<span>{p.prefix}…</span>{/if}
        </div>
      </a>
    {/each}
  </div>
{/if}

<style>
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); align-content: start; gap: 14px; padding: 4px; margin: -4px; }
  .plugin {
    display: grid;
    gap: 10px;
    padding: 18px;
    color: var(--text);
    position: relative;
    overflow: hidden;
    transition: border-color 0.25s, transform 0.25s var(--ease), box-shadow 0.25s;
  }
  .plugin::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(120deg, transparent 30%, rgba(61, 220, 132, 0.07), transparent 70%);
    transform: translateX(-100%);
    transition: transform 0.7s var(--ease);
    pointer-events: none;
  }
  .plugin:hover { color: var(--text); border-color: var(--green); transform: translateY(-3px); box-shadow: 0 14px 36px rgba(0, 0, 0, 0.45); }
  .plugin:hover::after { transform: translateX(100%); }
  .top { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
  .name { font: 600 15px var(--mono); overflow: hidden; text-overflow: ellipsis; }
  .desc { display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .fields { display: flex; flex-wrap: wrap; gap: 4px; }
  .foot { display: flex; justify-content: space-between; font-size: 11px; color: var(--muted); padding-top: 10px; border-top: 1px solid var(--border); }
  .skeleton { height: 170px; background: linear-gradient(90deg, var(--surface) 0%, var(--surface-2) 50%, var(--surface) 100%) 0 0 / 200% 100%; animation: shimmer 1.4s linear infinite; }
  @keyframes shimmer { to { background-position: -200% 0; } }
  .empty { display: grid; gap: 10px; justify-items: center; }
</style>
