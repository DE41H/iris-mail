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
  <div class="line">
    <span class="num">{String(n).padStart(2, '0')}</span>
    <div class="seg" role="radiogroup" aria-label={`Question ${n} answer type`}>
      {#each KINDS as k}
        <label title={k.note}>
          <input type="radio" name={`kind-${id}`} checked={field.kind === k.kind} onchange={() => retype(field, k.kind)} aria-label={k.label} />
          <span><i>{k.icon}</i>{k.label}</span>
        </label>
      {/each}
    </div>
    <input class="q" type="text" value={field.question} oninput={question} aria-label={`Question ${n}`} placeholder={laya.kind === 'boolean' ? 'Is this email a receipt?' : laya.kind === 'scale' ? 'How urgent is this email?' : 'What is this email about?'} />
    <div class="tools">
      <button type="button" class="btn btn-sm btn-ghost" title="Move up" aria-label={`Move question ${n} up`} disabled={index === 0} onclick={() => onmove(-1)}>↑</button>
      <button type="button" class="btn btn-sm btn-ghost" title="Move down" aria-label={`Move question ${n} down`} disabled={index === fields.length - 1} onclick={() => onmove(1)}>↓</button>
      <button type="button" class="btn btn-sm btn-ghost" title="Duplicate" aria-label={`Duplicate question ${n}`} onclick={onduplicate}>⧉</button>
      <button type="button" class="btn btn-sm btn-ghost del" title="Remove" aria-label={`Remove question ${n}`} onclick={onremove}>✕</button>
    </div>
  </div>

  <div class="line">
    <div class="key" title="Result key">
      <span class="muted">→</span>
      <input class="mono" type="text" value={field.name} oninput={key} placeholder="result_key" aria-label={`Question ${n} result key`} aria-invalid={touched && issues.some((i) => i.startsWith('Key'))} autocomplete="off" spellcheck="false" />
      {#if auto && field.name}<span class="chip">auto</span>{/if}
    </div>

    <div class="answer">
      {#if field.kind === 'choice'}
        <OptionsInput bind:options={field.options} label={`Question ${n} answers`} />
      {:else if field.kind === 'scale'}
        <div class="range">
          <input class="mono" type="number" step="1" value={field.min} oninput={(e) => field.kind === 'scale' && (field.min = num(e))} aria-label={`Question ${n} lowest value`} />
          <span class="muted">–</span>
          <input class="mono" type="number" step="1" value={field.max} oninput={(e) => field.kind === 'scale' && (field.max = num(e))} aria-label={`Question ${n} highest value`} />
          <select class="mono" onchange={scalePreset} aria-label="Pick a common range">
            <option value="">range…</option>
            {#each SCALES as [label], i}<option value={i}>{label}</option>{/each}
          </select>
          {#if levels && levels <= MAX_LEVELS}
            <div class="ticks" aria-hidden="true">
              {#each { length: levels } as _, i}<span style:--i={i}>{field.min + i}</span>{/each}
            </div>
          {/if}
        </div>
      {:else}
        <div class="bool" aria-hidden="true"><span class="chip on">true</span><span class="chip">false</span></div>
      {/if}
    </div>
  </div>

  {#if touched && issues.length}
    <ul class="issues" transition:slide={{ duration: 160 }}>
      {#each issues as issue}<li>{issue}</li>{/each}
    </ul>
  {/if}
</article>

<style>
  .field { display: grid; gap: 8px; padding: 10px 12px; transition: border-color 0.25s, box-shadow 0.25s; }
  .field:focus-within { border-color: var(--border-strong); box-shadow: 0 0 0 1px var(--green-soft), 0 12px 32px rgba(0, 0, 0, 0.35); }
  .field.bad { border-color: rgba(255, 95, 95, 0.4); }
  .line { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
  .num { font: 600 12px var(--mono); color: var(--green); }
  .q { flex: 1 1 220px; width: auto; }
  .tools { display: flex; gap: 2px; }
  .del:hover { color: var(--danger); }

  .seg { display: inline-flex; border: 1px solid var(--border-strong); border-radius: 6px; overflow: hidden; }
  .seg label { position: relative; }
  .seg input { position: absolute; opacity: 0; inset: 0; cursor: pointer; }
  .seg span { display: block; padding: 4px 8px; font: 12px var(--mono); color: var(--muted); transition: background 0.2s, color 0.2s; white-space: nowrap; }
  .seg i { font-style: normal; margin-right: 4px; }
  .seg label + label span { border-left: 1px solid var(--border-strong); }
  .seg input:checked + span { background: var(--green-soft); color: var(--green); }
  .seg input:focus-visible + span { outline: 2px solid var(--green); outline-offset: -2px; }

  .key { display: flex; align-items: center; gap: 6px; font: 13px var(--mono); padding-left: 22px; }
  .key input { width: 170px; padding-top: 6px; padding-bottom: 6px; }
  .answer { flex: 1 1 280px; min-width: 0; }

  .range { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .range input { width: 64px; padding-top: 6px; padding-bottom: 6px; }
  .range select { width: auto; padding-top: 6px; padding-bottom: 6px; }
  .ticks { display: flex; gap: 3px; flex: 1; min-width: 120px; }
  .ticks span {
    flex: 1;
    max-width: 36px;
    padding: 3px 0;
    text-align: center;
    font: 11px var(--mono);
    color: var(--green);
    border-radius: 4px;
    background: rgba(61, 220, 132, calc(0.06 + var(--i) * 0.04));
    animation: rise 0.35s var(--ease) both;
    animation-delay: calc(var(--i) * 30ms);
  }
  .bool { display: flex; align-items: center; gap: 6px; }
  .issues { margin: 0; padding: 0 0 0 40px; color: var(--danger); font-size: 12px; }
</style>
