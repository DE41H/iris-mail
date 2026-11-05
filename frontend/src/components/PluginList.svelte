<script lang="ts">
  import { onMount } from 'svelte';
  import { listAll, message, type Plugin } from '../lib/api';
  import { fromSchema } from '../lib/schema';
  import { KINDS } from '../lib/presets';
  import Count from './Count.svelte';

  let plugins = $state<Plugin[] | null>(null);
  let error = $state('');

  onMount(() => listAll<Plugin>('/api/plugins/').then((p) => (plugins = p)).catch((err) => (error = message(err))));

  const questions = (p: Plugin) => {
    const parsed = fromSchema(p.schema);
    return 'fields' in parsed ? parsed.fields : [];
  };
  const icon = (kind: string) => KINDS.find((k) => k.kind === kind)?.icon;
  const plural = (n: number | undefined, word: string) => (n === 1 ? word : `${word}s`);
  // Each plugin gets its own iris colour, stable across visits.
  // FNV-1a: uuid7 ids share a time prefix, so a weak hash would give neighbours the same colour.
  const hue = (id: string) => [...id].reduce((h, c) => Math.imul(h ^ c.charCodeAt(0), 16777619) >>> 0, 2166136261) % 160 + 180; // teal to magenta, around the brand violet
  const total = (key: 'subscriber_count' | 'result_count') => plugins?.reduce((n, p) => n + (p[key] ?? 0), 0) ?? 0;

  function spot(e: PointerEvent) {
    const el = e.currentTarget as HTMLElement;
    const r = el.getBoundingClientRect();
    el.style.setProperty('--mx', `${e.clientX - r.left}px`);
    el.style.setProperty('--my', `${e.clientY - r.top}px`);
  }

  // Names only the clicked card, so the detail page can grow out of it.
  const open = (e: MouseEvent) => ((e.currentTarget as HTMLElement).style.viewTransitionName = 'plugin');
</script>

{#if error}
  <div class="alert alert-danger" role="alert">{error}</div>
{:else if !plugins}
  <div class="grid">
    {#each { length: 3 } as _, i}<div class="card skeleton reveal" style:--i={i}></div>{/each}
  </div>
{:else if !plugins.length}
  <div class="card empty reveal">
    <span class="emblem big" style:--h={262} aria-hidden="true"></span>
    <h2>No plugins yet</h2>
    <p>Start from a template and you'll have an API key in a minute.</p>
    <p><a class="btn btn-primary" href="/plugins/new">Create a plugin</a></p>
  </div>
{:else}
  <dl class="totals reveal">
    <div><dt>{plural(plugins.length, 'plugin')}</dt><dd><Count value={plugins.length} /></dd></div>
    <div><dt>{total('subscriber_count') === 1 ? 'person' : 'people'} switched on</dt><dd><Count value={total('subscriber_count')} delay={80} /></dd></div>
    <div><dt>{plural(total('result_count'), 'answer')} so far</dt><dd><Count value={total('result_count')} delay={160} /></dd></div>
  </dl>

  <div class="grid grow scroll">
    {#each plugins as p, i (p.id)}
      {@const fields = questions(p)}
      <a class="card plugin reveal" style:--i={i + 1} style:--h={hue(p.id)} href={`/plugins/detail?id=${p.id}`} onpointermove={spot} onclick={open}>
        <div class="top">
          <span class="emblem" aria-hidden="true"></span>
          <span class="title">
            <span class="name">{p.name}</span>
            <span class="ver">version {p.version}</span>
          </span>
          <span class="chip" class:on={p.prefix}>{p.prefix ? 'Key active' : 'No key'}</span>
        </div>
        {#if p.desc}<p class="muted desc">{p.desc}</p>{/if}
        <div class="fields">
          {#each fields.slice(0, 5) as f}<span class="chip"><span class="ico">{icon(f.kind)}</span>{f.name}</span>{/each}
          {#if fields.length > 5}<span class="chip">+{fields.length - 5}</span>{/if}
        </div>
        <div class="stats">
          <span><b><Count value={p.subscriber_count ?? 0} delay={i * 60} /></b>{p.subscriber_count === 1 ? 'person' : 'people'}</span>
          <span><b><Count value={p.result_count ?? 0} delay={i * 60 + 80} /></b>{plural(p.result_count, 'answer')}</span>
          <span><b>{fields.length}</b>{plural(fields.length, 'question')}</span>
        </div>
      </a>
    {/each}
    <a class="card add reveal" style:--i={plugins.length + 1} href="/plugins/new">
      <span class="plus" aria-hidden="true"></span>
      <span>New plugin</span>
    </a>
  </div>
{/if}

<style>
  .totals { display: flex; flex-wrap: wrap; gap: 12px 40px; margin: 0; }
  .totals div { display: flex; flex-direction: column-reverse; }
  .totals dt { font-size: 13px; color: var(--muted); }
  .totals dd { margin: 0; font-size: 34px; font-weight: 700; font-stretch: 118%; letter-spacing: -0.03em; line-height: 1.1; }

  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(310px, 100%), 1fr)); align-content: start; gap: 16px; padding: 6px; margin: -6px; }
  .plugin {
    --tint: oklch(0.58 0.19 var(--h));
    display: grid;
    align-content: start;
    gap: 12px;
    padding: 18px;
    color: var(--text);
    position: relative;
    overflow: hidden;
    isolation: isolate;
    transition: border-color 0.3s, translate 0.45s var(--spring), box-shadow 0.4s var(--ease);
  }
  /* A soft light in the plugin's own colour follows the pointer. */
  .plugin::before {
    content: '';
    position: absolute;
    inset: 0;
    z-index: -1;
    background: radial-gradient(260px circle at var(--mx, 50%) var(--my, 0%), color-mix(in oklab, var(--tint) 14%, transparent), transparent 70%);
    opacity: 0;
    transition: opacity 0.4s;
  }
  .plugin:hover::before { opacity: 1; }
  .plugin:hover { color: var(--text); border-color: color-mix(in oklab, var(--tint) 45%, var(--border)); translate: 0 -4px; box-shadow: var(--shadow-lift); }
  .plugin:active { translate: 0 -1px; transition-duration: 0.1s; }

  .top { display: flex; align-items: center; gap: 12px; }
  .title { flex: 1; min-width: 0; display: grid; }
  .name { font-size: 17px; font-weight: 660; font-stretch: 110%; letter-spacing: -0.01em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .ver { font-size: 12.5px; color: var(--faint); }
  .top .chip { flex-shrink: 0; white-space: nowrap; }
  .chip.on::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

  /* The plugin's iris: blades in its colour around a saffron pupil; it turns open on hover. */
  .emblem {
    --tint: oklch(0.58 0.19 var(--h));
    flex-shrink: 0;
    width: 42px;
    height: 42px;
    border-radius: 50%;
    background:
      radial-gradient(circle, var(--signal) 0 17%, transparent 19%),
      radial-gradient(circle, transparent 0 38%, var(--surface) 40% 44%, transparent 46%),
      repeating-conic-gradient(from calc(var(--h) * 1deg), var(--tint) 0 30deg, oklch(0.46 0.2 calc(var(--h) + 24)) 30deg 60deg);
    box-shadow: 0 6px 16px -6px var(--tint);
    transition: rotate 1s var(--spring), scale 0.5s var(--spring);
  }
  .plugin:hover .emblem { rotate: 150deg; scale: 1.08; }
  .emblem.big { width: 72px; height: 72px; animation: spin 18s linear infinite; }

  .desc { display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .fields { display: flex; flex-wrap: wrap; gap: 5px; }
  .fields .chip { overflow-wrap: anywhere; }
  .ico { color: var(--tint); }
  .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; padding-top: 12px; border-top: 1px solid var(--border); font-size: 12.5px; color: var(--muted); }
  .stats b { display: block; color: var(--text); font-size: 22px; font-weight: 680; font-stretch: 115%; line-height: 1.15; }

  .add {
    display: grid;
    place-content: center;
    justify-items: center;
    gap: 10px;
    min-height: 200px;
    border: 1.5px dashed var(--border-strong);
    background: transparent;
    box-shadow: none;
    color: var(--muted);
    font-weight: 560;
    transition: color 0.25s, border-color 0.25s, background 0.25s;
  }
  .add:hover { color: var(--accent); border-color: var(--accent); background: var(--accent-soft); }
  .plus {
    position: relative;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: var(--accent-soft);
    transition: rotate 0.5s var(--spring), background 0.25s;
  }
  .plus::before, .plus::after { content: ''; position: absolute; inset: 50% 12px auto; height: 2px; margin-top: -1px; border-radius: 2px; background: currentColor; }
  .plus::after { rotate: 90deg; }
  .add:hover .plus { rotate: 90deg; background: var(--surface); }

  .skeleton { height: 230px; }
  .empty { display: grid; gap: 12px; justify-items: center; }
  .empty h2 { color: var(--text); font-size: 20px; }

  @media (hover: none) { .plugin::before { display: none; } }
</style>
