<script lang="ts">
  import { onMount } from 'svelte';
  import { hue, listAll, message, type Plugin } from '../lib/api';
  import { fromSchema, KINDS } from '../lib/schema';
  import Count from './Count.svelte';
  import Iris from './Iris.svelte';

  let plugins = $state<Plugin[] | null>(null);
  let error = $state('');

  onMount(() => listAll<Plugin>('/api/v1/plugins/').then((p) => (plugins = p)).catch((err) => (error = message(err))));

  const questions = (p: Plugin) => {
    const parsed = fromSchema(p.schema);
    return 'fields' in parsed ? parsed.fields : [];
  };
  const icon = (kind: string) => KINDS.find((k) => k.kind === kind)?.icon;
  const plural = (n: number | undefined, word: string) => (n === 1 ? word : `${word}s`);

  function spot(e: PointerEvent) {
    const el = e.currentTarget as HTMLElement;
    const r = el.getBoundingClientRect();
    el.style.setProperty('--mx', `${e.clientX - r.left}px`);
    el.style.setProperty('--my', `${e.clientY - r.top}px`);
  }

  // Keeps the chips on one line: hides the ones that wrap and counts them in the last "+N" chip.
  function oneLine(row: HTMLElement) {
    const more = row.lastElementChild as HTMLElement;
    const chips = [...row.children].slice(0, -1) as HTMLElement[];
    const fit = () => {
      if (!chips.length) return;
      chips.forEach((c) => (c.hidden = false));
      chips[0].style.maxWidth = '';
      more.hidden = true;
      const top = chips[0].offsetTop;
      let shown = chips.filter((c) => c.offsetTop === top).length;
      if (shown === chips.length) return;
      chips.slice(shown).forEach((c) => (c.hidden = true));
      more.hidden = false;
      // the "+N" chip needs room too; drop chips until it fits on the line
      while (true) {
        more.textContent = `+${chips.length - shown}`;
        if (more.offsetTop === top) return;
        if (shown === 1) break;
        chips[--shown].hidden = true;
      }
      // one chip as wide as the line: shorten it (it ends in an ellipsis) to make room
      chips[0].style.maxWidth = `${row.clientWidth - more.offsetWidth - parseFloat(getComputedStyle(row).columnGap)}px`;
    };
    const ro = new ResizeObserver(fit);
    ro.observe(row);
    document.fonts.ready.then(fit); // web fonts change chip widths
    return { destroy: () => ro.disconnect() };
  }

  // Names only the clicked card, so the detail page can grow out of it.
  const open = (e: MouseEvent) => ((e.currentTarget as HTMLElement).style.viewTransitionName = 'plugin');
</script>

{#if error}
  <div class="alert alert-danger" role="alert">{error}</div>
{:else if !plugins}
  <div class="grid skel" role="status" aria-label="Loading plugins">
    {#each { length: 3 } as _}
      <div class="card sk">
        <div class="sk-row"><span class="bone sk-ico"></span><span class="bone w40"></span><span class="bone sk-pill"></span></div>
        <span class="bone w90"></span>
        <span class="bone w60"></span>
        <div class="sk-row"><span class="bone sk-pill"></span><span class="bone sk-pill"></span><span class="bone sk-pill"></span></div>
        <div class="sk-row sk-stats"><span class="bone w20"></span><span class="bone w20"></span><span class="bone w20"></span></div>
      </div>
    {/each}
  </div>
{:else}
  <div class="grid grow scroll">
    {#each plugins as p, i (p.id)}
      {@const fields = questions(p)}
      {@const rules = Object.keys(p.rules ?? {})}
      {@const chips = [...fields.map((f) => ({ name: f.name, ico: icon(f.kind) })), ...rules.map((name) => ({ name, ico: '' }))]}
      <a class="card plugin reveal" style:--i={i + 1} style:--h={hue(p.id)} href={`/plugins/detail?id=${p.id}`} onpointermove={spot} onclick={open}>
        <div class="top">
          <Iris />
          <span class="name">{p.name}</span>
          <span class="chip" title={`Version ${p.version}`}>v{p.version}</span>
        </div>
        <p class="muted desc" title={p.desc}>{p.desc}</p>
        <div class="fields" use:oneLine>
          {#each chips as c}<span class="chip" class:rule={!c.ico} title={c.name}>{#if c.ico}<span class="ico">{c.ico}</span>{/if}<span class="text">{c.name}</span></span>{/each}
          <span class="chip more" hidden></span>
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
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(310px, 100%), 1fr)); grid-auto-rows: max-content; align-content: start; gap: 16px; padding: 6px; margin: -6px; }
  .plugin {
    --tint: oklch(0.58 0.19 var(--h));
    display: flex;
    flex-direction: column;
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
  .name { flex: 1; min-width: 0; font-size: 17px; font-weight: 660; font-stretch: 110%; letter-spacing: -0.01em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .top .chip { flex-shrink: 0; font-variant-numeric: tabular-nums; transition: color 0.3s, background 0.3s, border-color 0.3s; }
  .plugin:hover .top .chip { color: var(--tint); border-color: color-mix(in oklab, var(--tint) 30%, transparent); background: color-mix(in oklab, var(--tint) 10%, var(--surface)); }

  /* Every section keeps a fixed height, so the stats line up across cards. */
  .desc { display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; height: 2lh; margin: 0; overflow-wrap: anywhere; }
  .fields { display: flex; flex-wrap: wrap; gap: 5px; min-width: 0; }
  .fields .chip { max-width: 100%; min-width: 0; white-space: nowrap; }
  .fields .chip[hidden] { display: none; }
  .text { overflow: hidden; text-overflow: ellipsis; }
  .more { flex-shrink: 0; font-variant-numeric: tabular-nums; }
  .ico { color: var(--tint); }
  .fields .rule { color: var(--signal-text); background: var(--signal-soft); border-color: transparent; }
  .stats { margin-top: auto; display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; padding-top: 12px; border-top: 1px solid var(--border); font-size: 12.5px; color: var(--muted); }
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

  .sk { display: flex; flex-direction: column; gap: 14px; padding: 18px; height: 230px; }
  .sk-row { display: flex; align-items: center; gap: 10px; }
  .sk-ico { width: 34px; height: 34px; border-radius: 50%; }
  .sk-pill { width: 64px; height: 22px; border-radius: 999px; }
  .sk-row > .w40 { flex: 0 0 40%; }
  .sk-stats { margin-top: auto; padding-top: 14px; border-top: 1px solid var(--border); }
  .sk-stats .bone { flex: 0 0 20%; height: 14px; }
  .w90 { width: 90%; }
  .w60 { width: 60%; }

  @media (hover: none) { .plugin::before { display: none; } }
</style>
