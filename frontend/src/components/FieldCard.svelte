<script lang="ts">
  import { tick } from 'svelte';
  import { slide } from 'svelte/transition';
  import { fieldProblems, MAX_LEVELS, MAX_NAME_LENGTH, slug, type Field } from '../lib/schema';
  import { KINDS, retype, SCALES } from '../lib/presets';
  import OptionsInput from './OptionsInput.svelte';

  interface Props {
    field: Field;
    fields: Field[];
    index: number;
    open: boolean;
    onopen: () => void;
    onmove: (by: number) => void;
    onduplicate: () => void;
    onremove: () => void;
  }

  let { field = $bindable(), fields, index, open, onopen, onmove, onduplicate, onremove }: Props = $props();

  const n = $derived(index + 1);
  const id = $props.id();
  let input = $state<HTMLInputElement>();
  // A new question's key follows its text until the user types their own. A key that already
  // exists never changes on its own: saved plugins have API clients reading it.
  let auto = $state(!field.name);
  let touched = $state(false);
  const issues = $derived(fieldProblems(field, fields));
  const laya = $derived(KINDS.find((k) => k.kind === field.kind)!);
  const levels = $derived(field.kind === 'scale' && field.max >= field.min ? field.max - field.min + 1 : 0);
  const summary = $derived(
    field.kind === 'choice'
      ? field.options.length ? field.options.slice(0, 3).join(', ') + (field.options.length > 3 ? ` +${field.options.length - 3}` : '') : 'no answers yet'
      : field.kind === 'scale' ? `${field.min} to ${field.max}` : 'yes or no',
  );

  async function expand() {
    onopen();
    await tick();
    input?.focus();
  }

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

<article class="field" class:open class:bad={touched && issues.length} onfocusout={() => (touched = true)}>
  <div class="head">
    <span class="num" title={laya.label}><i aria-hidden="true">{laya.icon}</i>{n}</span>
    {#if open}
      <input bind:this={input} class="q" type="text" value={field.question} oninput={question} aria-label={`Question ${n}`} placeholder={laya.kind === 'boolean' ? 'Is this email a receipt?' : laya.kind === 'scale' ? 'How urgent is this email?' : 'What is this email about?'} />
    {:else}
      <button type="button" class="row" onclick={expand} aria-label={`Edit question ${n}: ${field.question || 'untitled'}`}>
        <span class="text" class:empty={!field.question}>{field.question || 'Untitled question'}</span>
        <span class="sum">{summary}</span>
        <code class="name">{field.name || '—'}</code>
        <span class="dot" class:on={touched && issues.length} title={touched ? issues.join(' ') : ''}></span>
      </button>
    {/if}
    <div class="tools">
      <button type="button" class="tool" title="Move up" aria-label={`Move question ${n} up`} disabled={index === 0} onclick={() => onmove(-1)}>↑</button>
      <button type="button" class="tool" title="Move down" aria-label={`Move question ${n} down`} disabled={index === fields.length - 1} onclick={() => onmove(1)}>↓</button>
      <button type="button" class="tool" title="Duplicate" aria-label={`Duplicate question ${n}`} onclick={onduplicate}>⧉</button>
      <button type="button" class="tool del" title="Remove" aria-label={`Remove question ${n}`} onclick={onremove}>✕</button>
    </div>
  </div>

  {#if open}
    <div class="rows" transition:slide={{ duration: 200 }}>
      <div class="seg" role="radiogroup" aria-label={`Question ${n} answer type`}>
        {#each KINDS as k}
          <label title={k.note}>
            <input type="radio" name={`kind-${id}`} checked={field.kind === k.kind} onchange={() => retype(field, k.kind)} aria-label={k.label} />
            <span><i>{k.icon}</i>{k.label}</span>
          </label>
        {/each}
      </div>

      {#if field.kind === 'choice'}
        <OptionsInput bind:options={field.options} label={`Question ${n} answers`} />
      {:else if field.kind === 'scale'}
        <div class="range">
          <input class="mono" type="number" step="1" value={field.min} oninput={(e) => field.kind === 'scale' && (field.min = num(e))} aria-label={`Question ${n} lowest value`} />
          <span class="muted">to</span>
          <input class="mono" type="number" step="1" value={field.max} oninput={(e) => field.kind === 'scale' && (field.max = num(e))} aria-label={`Question ${n} highest value`} />
          <select onchange={scalePreset} aria-label="Pick a common range">
            <option value="">Common ranges…</option>
            {#each SCALES as [label], i}<option value={i}>{label}</option>{/each}
          </select>
          {#if levels && levels <= MAX_LEVELS}
            <div class="ticks" aria-hidden="true">
              {#each { length: levels } as _, i}<span style:--i={i}>{field.min + i}</span>{/each}
            </div>
          {/if}
        </div>
      {:else}
        <p class="bool">Answered with <span class="chip on">true</span> or <span class="chip">false</span></p>
      {/if}

      <div class="key">
        <span>Saved as</span>
        <input class="mono" type="text" value={field.name} oninput={key} placeholder="result_key" maxlength={MAX_NAME_LENGTH} aria-label={`Question ${n} result key`} aria-invalid={touched && issues.some((i) => /key/i.test(i))} autocomplete="off" spellcheck="false" />
        {#if auto && field.name}<span class="chip">from the question</span>{/if}
      </div>

      {#if touched && issues.length}
        <ul class="issues" transition:slide={{ duration: 160 }}>
          {#each issues as issue}<li>{issue}</li>{/each}
        </ul>
      {/if}
    </div>
  {/if}
</article>

<style>
  .field { display: grid; grid-template-columns: minmax(0, 1fr); border: 1px solid transparent; border-radius: 12px; transition: border-color 0.25s, box-shadow 0.35s var(--ease), background 0.25s; }
  .field:not(.open):hover { background: var(--surface-2); }
  .field.open { padding-bottom: 14px; background: var(--surface); border-color: color-mix(in oklab, var(--accent) 40%, var(--border)); box-shadow: var(--shadow-lift); }
  .field.bad { border-color: color-mix(in oklab, var(--danger) 40%, transparent); }
  .head { display: flex; align-items: center; gap: 10px; padding: 6px 6px 6px 10px; min-height: 48px; }
  .open .head { padding-top: 10px; }
  .num { display: inline-flex; align-items: center; justify-content: center; gap: 4px; flex-shrink: 0; min-width: 40px; height: 24px; padding: 0 7px; border-radius: 999px; background: var(--accent-soft); color: var(--accent); font-size: 12px; font-weight: 640; font-variant-numeric: tabular-nums; }
  .num i { font-style: normal; font-size: 10px; opacity: 0.8; }
  .q { flex: 1; min-width: 0; font-size: 15px; font-weight: 520; }

  .row { flex: 1; min-width: 0; display: grid; grid-template-columns: minmax(0, 1fr) auto 112px 8px; align-items: baseline; gap: 12px; padding: 6px 4px; border: 0; background: none; color: var(--text); font: inherit; text-align: left; cursor: pointer; border-radius: 8px; }
  .text { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 14.5px; font-weight: 520; }
  .text.empty { color: var(--faint); font-style: italic; }
  .sum { max-width: 220px; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; color: var(--muted); }
  .name { overflow: hidden; text-overflow: ellipsis; font-size: 12px; color: var(--faint); }
  .dot { align-self: center; width: 8px; height: 8px; border-radius: 50%; }
  .dot.on { background: var(--danger); }

  .tools { display: flex; gap: 2px; opacity: 0; transition: opacity 0.2s; }
  .field:hover .tools, .field:focus-within .tools, .open .tools { opacity: 1; }
  .tool { width: 28px; height: 28px; display: grid; place-items: center; border: 0; border-radius: 8px; background: none; color: var(--muted); font-size: 13px; cursor: pointer; transition: background 0.2s, color 0.2s; }
  .tool:hover:not(:disabled) { background: var(--accent-soft); color: var(--accent); }
  .tool:disabled { opacity: 0.35; cursor: default; }
  .tool:focus-visible { outline: 2px solid var(--accent); }
  .del:hover:not(:disabled) { background: var(--danger-soft); color: var(--danger); }
  .rows { display: grid; grid-template-columns: minmax(0, 1fr); gap: 12px; padding: 4px 16px 0 60px; }

  .seg { justify-self: start; display: inline-flex; padding: 2px; gap: 2px; border-radius: 999px; background: var(--surface-2); border: 1px solid var(--border); }
  .seg label { position: relative; }
  .seg input { position: absolute; opacity: 0; inset: 0; cursor: pointer; }
  .seg span { display: block; padding: 4px 12px; border-radius: 999px; font-size: 13px; font-weight: 540; color: var(--muted); transition: background 0.25s, color 0.2s; white-space: nowrap; }
  .seg i { font-style: normal; margin-right: 5px; }
  .seg input:checked + span { background: var(--accent-soft); color: var(--accent); }
  .seg input:focus-visible + span { outline: 2px solid var(--accent); outline-offset: 0; }
  @media (max-width: 380px) { .seg i { display: none; } }

  .range { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .range input { width: 68px; padding-top: 6px; padding-bottom: 6px; }
  .range select { width: auto; max-width: 100%; padding-top: 6px; padding-bottom: 6px; font-size: 13.5px; }
  .ticks { display: flex; gap: 3px; flex: 1 1 100%; }
  .ticks span {
    flex: 1;
    max-width: 40px;
    padding: 3px 0;
    text-align: center;
    font: 11px var(--mono);
    color: var(--accent);
    border-radius: 6px;
    background: color-mix(in oklab, var(--accent) calc(6% + var(--i) * 5%), transparent);
    animation: rise 0.35s var(--ease) both;
    animation-delay: calc(var(--i) * 30ms);
  }
  .bool { display: flex; align-items: center; gap: 6px; margin: 0; font-size: 13.5px; color: var(--muted); }
  .key { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; font-size: 12.5px; color: var(--faint); }
  .key input { width: 200px; max-width: 100%; padding: 4px 8px; font-size: 12.5px; background: transparent; }
  .key .chip { font-size: 11.5px; }
  .issues { margin: 0; padding: 0 0 0 18px; color: var(--danger); font-size: 13px; }
  /* A narrow list keeps the question readable and drops the key, which shows once the question opens. */
  @container (max-width: 520px) {
    .row { grid-template-columns: minmax(0, 1fr) auto 8px; }
    .name { display: none; }
  }
  /* Phones: a closed question is one tap target; its tools show once it opens. */
  @media (max-width: 640px) {
    .head { flex-wrap: wrap; align-items: flex-start; }
    .num { margin-top: 6px; }
    .field:not(.open) .tools { display: none; }
    .open .tools { opacity: 1; margin-left: auto; }
    .row { grid-template-columns: minmax(0, 1fr) 8px; row-gap: 2px; }
    .text { grid-column: 1 / -1; white-space: normal; }
    .open .q { order: 3; flex-basis: 100%; }
    .rows { padding-left: 16px; }
  }
</style>
