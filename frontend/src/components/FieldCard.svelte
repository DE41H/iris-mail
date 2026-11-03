<script lang="ts">
  import { slide } from 'svelte/transition';
  import { fieldProblems, MAX_LEVELS, slug, type Field } from '../lib/schema';
  import { KINDS, retype, SCALES } from '../lib/presets';
  import OptionsInput from './OptionsInput.svelte';

  interface Props {
    field: Field;
    fields: Field[];
    index: number;
    onmove: (by: number) => void;
    onduplicate: () => void;
    onremove: () => void;
  }

  let { field = $bindable(), fields, index, onmove, onduplicate, onremove }: Props = $props();

  const n = $derived(index + 1);
  const id = $props.id();
  // The key follows the question until the user types their own.
  let auto = $state(!field.name || field.name === slug(field.question));
  let touched = $state(false);
  const issues = $derived(fieldProblems(field, fields));
  const laya = $derived(KINDS.find((k) => k.kind === field.kind)!);
  const levels = $derived(field.kind === 'scale' && field.max >= field.min ? field.max - field.min + 1 : 0);

  function question(e: Event) {
    field.question = (e.currentTarget as HTMLInputElement).value;
    if (auto) field.name = slug(field.question);
  }

  function key(e: Event) {
    field.name = (e.currentTarget as HTMLInputElement).value.toLowerCase().replace(/[\s-]+/g, '_');
    auto = !field.name;
  }

  function scalePreset(e: Event) {
    const select = e.currentTarget as HTMLSelectElement;
    const preset = SCALES[Number(select.value)];
    if (preset && field.kind === 'scale') [, field.min, field.max] = preset;
    select.value = '';
  }

  const num = (e: Event) => {
    const v = (e.currentTarget as HTMLInputElement).value;
    return v === '' ? NaN : Number(v);
  };
</script>

<article class="card field" class:bad={touched && issues.length} onfocusout={() => (touched = true)}>
  <header>
    <span class="num">{String(n).padStart(2, '0')}</span>
    <div class="seg" role="radiogroup" aria-label={`Question ${n} answer type`}>
      {#each KINDS as k}
        <label title={k.note}>
          <input type="radio" name={`kind-${id}`} checked={field.kind === k.kind} onchange={() => retype(field, k.kind)} />
          <span><i>{k.icon}</i>{k.label}</span>
        </label>
      {/each}
    </div>
    <div class="tools">
      <button type="button" class="btn btn-sm btn-ghost" title="Move up" aria-label={`Move question ${n} up`} disabled={index === 0} onclick={() => onmove(-1)}>↑</button>
      <button type="button" class="btn btn-sm btn-ghost" title="Move down" aria-label={`Move question ${n} down`} disabled={index === fields.length - 1} onclick={() => onmove(1)}>↓</button>
      <button type="button" class="btn btn-sm btn-ghost" title="Duplicate" aria-label={`Duplicate question ${n}`} onclick={onduplicate}>⧉</button>
      <button type="button" class="btn btn-sm btn-ghost del" title="Remove" aria-label={`Remove question ${n}`} onclick={onremove}>✕</button>
    </div>
  </header>

  <div class="body">
    <div>
      <label class="label" for={`${id}-q`}>question for laya</label>
      <input id={`${id}-q`} type="text" value={field.question} oninput={question} placeholder={`e.g. ${laya.kind === 'boolean' ? 'Is this email a receipt?' : laya.kind === 'scale' ? 'How urgent is this email?' : 'What is this email about?'}`} />
    </div>

    <div class="keyrow">
      <label class="label" for={`${id}-k`}>result key</label>
      <div class="key">
        <span class="muted">result.</span>
        <input id={`${id}-k`} class="mono" type="text" value={field.name} oninput={key} placeholder="answer_key" aria-invalid={touched && issues.some((i) => i.startsWith('Key'))} autocomplete="off" spellcheck="false" />
        {#if auto && field.name}<span class="chip">auto</span>{/if}
      </div>
    </div>

    {#if field.kind === 'choice'}
      <div>
        <div class="label">possible answers <span class="muted">· laya picks exactly one</span></div>
        <OptionsInput bind:options={field.options} label={`Question ${n} answers`} />
      </div>
    {:else if field.kind === 'scale'}
      <div>
        <div class="label">range <span class="muted">· up to {MAX_LEVELS} levels</span></div>
        <div class="range">
          <input class="mono" type="number" step="1" value={field.min} oninput={(e) => field.kind === 'scale' && (field.min = num(e))} aria-label={`Question ${n} lowest value`} />
          <span class="muted">to</span>
          <input class="mono" type="number" step="1" value={field.max} oninput={(e) => field.kind === 'scale' && (field.max = num(e))} aria-label={`Question ${n} highest value`} />
          <select class="mono" onchange={scalePreset} aria-label="Pick a common range">
            <option value="">common ranges…</option>
            {#each SCALES as [label], i}<option value={i}>{label}</option>{/each}
          </select>
        </div>
        {#if levels && levels <= MAX_LEVELS}
          <div class="ticks" aria-hidden="true">
            {#each { length: levels } as _, i}<span style:--i={i}>{field.min + i}</span>{/each}
          </div>
        {/if}
      </div>
    {:else}
      <div class="bool" aria-hidden="true"><span class="chip on">true</span><span class="chip">false</span><span class="muted">laya answers yes or no</span></div>
    {/if}

    {#if touched && issues.length}
      <ul class="issues" transition:slide={{ duration: 160 }}>
        {#each issues as issue}<li>{issue}</li>{/each}
      </ul>
    {/if}
  </div>
</article>

<style>
  .field { overflow: hidden; transition: border-color 0.25s, box-shadow 0.25s; }
  .field:focus-within { border-color: var(--border-strong); box-shadow: 0 0 0 1px var(--green-soft), 0 12px 32px rgba(0, 0, 0, 0.35); }
  .field.bad { border-color: rgba(255, 95, 95, 0.4); }
  header { display: flex; align-items: center; gap: 12px; padding: 10px 12px; border-bottom: 1px solid var(--border); flex-wrap: wrap; }
  .num { font: 600 12px var(--mono); color: var(--green); }
  .tools { margin-left: auto; display: flex; gap: 2px; }
  .del:hover { color: var(--danger); }
  .body { display: grid; gap: 14px; padding: 14px 16px 16px; }

  .seg { display: inline-flex; border: 1px solid var(--border-strong); border-radius: 6px; overflow: hidden; }
  .seg label { position: relative; }
  .seg input { position: absolute; opacity: 0; inset: 0; cursor: pointer; }
  .seg span { display: block; padding: 4px 10px; font: 12px var(--mono); color: var(--muted); transition: background 0.2s, color 0.2s; }
  .seg i { font-style: normal; margin-right: 6px; }
  .seg label + label span { border-left: 1px solid var(--border-strong); }
  .seg input:checked + span { background: var(--green-soft); color: var(--green); }
  .seg input:focus-visible + span { outline: 2px solid var(--green); outline-offset: -2px; }

  .key { display: flex; align-items: center; gap: 8px; font: 13px var(--mono); }
  .key input { max-width: 260px; }

  .range { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .range input { width: 80px; }
  .range select { width: auto; }
  .ticks { display: flex; gap: 4px; margin-top: 10px; }
  .ticks span {
    flex: 1;
    max-width: 48px;
    padding: 4px 0;
    text-align: center;
    font: 11px var(--mono);
    color: var(--green);
    border-radius: 4px;
    background: rgba(61, 220, 132, calc(0.06 + var(--i) * 0.04));
    animation: rise 0.35s var(--ease) both;
    animation-delay: calc(var(--i) * 30ms);
  }
  .bool { display: flex; align-items: center; gap: 8px; font-size: 12px; }
  .issues { margin: 0; padding: 0 0 0 16px; color: var(--danger); font-size: 12px; }
</style>
