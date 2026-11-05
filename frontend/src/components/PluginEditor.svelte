<script lang="ts">
  import type { Snippet } from 'svelte';
  import { fly } from 'svelte/transition';
  import { fieldProblems, MAX_FIELDS, MAX_RULES, pluginProblems, problems, ruleProblems, type Draft } from '../lib/schema';
  import { message } from '../lib/api';
  import Builder from './Builder.svelte';
  import RuleList from './RuleList.svelte';
  import SchemaPreview from './SchemaPreview.svelte';

  interface Props {
    draft: Draft;
    submit: string;
    onsubmit: () => Promise<unknown>;
    head: Snippet;
    dirty?: boolean;
    locked?: string;
    tools?: Snippet; // top right, beside the title
    children?: Snippet; // bottom bar, beside the submit button
  }

  let { draft = $bindable(), submit, onsubmit, head, dirty = true, locked = '', tools, children }: Props = $props();

  let busy = $state(false);
  let error = $state('');
  let open = $state(false);
  let tried = $state(false); // problems are only called out once saving was attempted
  const steps: HTMLElement[] = $state([]);
  const issues = $derived([...pluginProblems(draft.name, draft.desc), ...(locked ? [] : problems(draft.fields, draft.rules))]);
  // A step shows a check once it is filled in and has nothing to fix.
  const done = $derived({
    name: !pluginProblems(draft.name, draft.desc).length,
    questions: !!draft.fields.length && draft.fields.every((f) => !fieldProblems(f, draft.fields).length),
    rules: !!draft.rules.length && draft.rules.every((r) => !ruleProblems(r, draft.rules).length),
  });

  const slugify = (e: Event) =>
    (draft.name = (e.currentTarget as HTMLInputElement).value.toLowerCase().replace(/\s+/g, '-').replace(/[^-a-z0-9_]/g, ''));

  async function save(e: SubmitEvent) {
    e.preventDefault();
    if (busy) return; // Enter pressed again while saving would send a second request
    if (issues.length || locked) {
      tried = open = true;
      // Jump to the first step that still needs work, like a checkout form does.
      const fieldsOk = draft.fields.every((f) => !fieldProblems(f, draft.fields).length) && (draft.fields.length || draft.rules.length);
      const at = !done.name ? 0 : !fieldsOk ? 1 : 2;
      steps[at]?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      return;
    }
    busy = true;
    error = '';
    try {
      await onsubmit();
    } catch (err) {
      error = message(err);
    } finally {
      busy = false;
    }
  }
</script>

{#snippet step(n: number, title: string, hint: string, ok: boolean, aside?: string)}
  <header class="step-head">
    <span class="n" class:ok aria-hidden="true">{#if ok}<svg viewBox="0 0 16 16"><path d="M3.5 8.5l3 3 6-7" /></svg>{:else}{n}{/if}</span>
    <div>
      <h2>{title}</h2>
      <p>{hint}</p>
    </div>
    {#if aside}<span class="aside">{aside}</span>{/if}
  </header>
{/snippet}

<form class="editor grow" onsubmit={save} novalidate>
  <div class="page-head reveal">
    <div>{@render head()}</div>
    {#if tools}<div class="actions">{@render tools()}</div>{/if}
  </div>

  <div class="flow grow scroll">
    <div class="column">
      {#if error}<div class="alert alert-danger" role="alert">{error}</div>{/if}

      <section class="card step reveal d1" bind:this={steps[0]}>
        {@render step(1, 'Name it', 'People see this when they choose plugins to switch on.', done.name)}
        <div class="body">
          <label>
            <span class="label">Name</span>
            <input class="mono" type="text" value={draft.name} oninput={slugify} placeholder="receipts" maxlength="255" autocomplete="off" spellcheck="false" />
            <span class="help">Lowercase, numbers, - and _. You call the API with it.</span>
          </label>
          <label>
            <span class="label">Description</span>
            <textarea rows="2" bind:value={draft.desc} placeholder="Finds receipts and sorts them by what was bought." maxlength="1024"></textarea>
          </label>
        </div>
      </section>

      <section class="card step reveal d2" bind:this={steps[1]}>
        {@render step(2, 'Ask questions', 'Laya answers each one for every new email.', done.questions, locked ? '' : `${draft.fields.length} / ${MAX_FIELDS}`)}
        <div class="body">
          {#if locked}
            <div class="alert alert-danger">{locked}</div>
          {:else}
            <Builder bind:fields={draft.fields} />
          {/if}
        </div>
      </section>

      {#if !locked}
        <section class="card step reveal d3" bind:this={steps[2]}>
          {@render step(3, 'Pull out exact text', 'Optional. Patterns copy things like amounts or order numbers word for word.', done.rules, draft.rules.length ? `${draft.rules.length} / ${MAX_RULES}` : 'Optional')}
          <div class="body">
            <RuleList bind:rules={draft.rules} />
          </div>
        </section>
      {/if}

      <section class="card step reveal d3">
        {@render step(4, 'Check the output', 'What you get back for each email. Updates as you type.', !issues.length && !locked)}
        <div class="body flush">
          <SchemaPreview fields={draft.fields} rules={draft.rules} />
        </div>
      </section>
    </div>

    <div class="bar">
      <div class="column bar-in">
        {#if locked}
          <span class="state">Read only</span>
        {:else if issues.length && !tried}
          <span class="state">Not ready yet</span>
        {:else if issues.length}
          <button type="button" class="state warn" onclick={() => (open = !open)} aria-expanded={open}>{issues.length} to fix <span class="caret" class:up={open}>▾</span></button>
        {:else if dirty}
          <span class="state ok">Ready to save</span>
        {:else}
          <span class="state">All saved</span>
        {/if}
        <div class="actions">
          {@render children?.()}
          <button class="btn btn-primary" type="submit" disabled={busy || !dirty || !!locked}>{busy ? 'Saving…' : submit}</button>
        </div>
        {#if open && issues.length}
          <ul class="card issues" role="status" transition:fly={{ y: 6, duration: 150 }}>
            {#each issues as issue}<li>{issue}</li>{/each}
          </ul>
        {/if}
      </div>
    </div>
  </div>
</form>

<style>
  .editor { display: flex; flex-direction: column; gap: 16px; }
  .flow { margin: 0 -24px; padding: 2px 24px 0; scroll-padding: 8px 0 90px; }
  .column { width: 100%; max-width: 760px; margin-inline: auto; }
  .flow > .column { display: grid; grid-template-columns: minmax(0, 1fr); gap: 16px; padding-bottom: 24px; }
  .page-head { max-width: 760px; width: 100%; margin-inline: auto; }

  .step { padding: 0; }
  .step-head { display: flex; align-items: flex-start; gap: 14px; padding: 18px 22px 0; }
  .step-head h2 { font-size: 16px; font-weight: 640; font-stretch: 108%; color: var(--text); }
  .step-head p { margin-top: 2px; font-size: 13.5px; color: var(--muted); }
  .step-head > div { flex: 1; min-width: 0; }
  .aside { flex-shrink: 0; margin-top: 2px; font-size: 12.5px; color: var(--faint); font-variant-numeric: tabular-nums; }
  .n {
    display: grid;
    place-items: center;
    flex-shrink: 0;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    border: 1.5px solid var(--border-strong);
    color: var(--muted);
    font-size: 13px;
    font-weight: 640;
    transition: background 0.3s, border-color 0.3s, color 0.3s;
  }
  .n.ok { background: var(--accent); border-color: var(--accent); color: var(--on-accent); animation: pop 0.4s var(--spring); }
  .n svg { width: 15px; height: 15px; fill: none; stroke: currentColor; stroke-width: 2.2; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 16; animation: tick 0.4s 0.1s var(--ease) both; }
  @keyframes tick { from { stroke-dashoffset: 16; } }
  .body { display: grid; grid-template-columns: minmax(0, 1fr); gap: 16px; padding: 16px 22px 22px 64px; }
  .body.flush { padding: 14px 0 0; }
  .body label { display: block; }
  .body .help { margin-top: 6px; }
  textarea { resize: vertical; min-height: 64px; }

  /* The save bar stays in view at the bottom of the flow, like a checkout button. */
  .bar {
    position: sticky;
    bottom: 0;
    z-index: 5;
    margin: 0 -24px;
    padding: 12px 24px 14px;
    background: color-mix(in oklab, var(--bg) 82%, transparent);
    backdrop-filter: blur(10px);
    border-top: 1px solid var(--border);
  }
  .bar-in { position: relative; display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
  .bar-in .actions { margin-left: auto; }
  .state { display: inline-flex; align-items: center; gap: 7px; font: 540 13px var(--font); color: var(--muted); background: none; border: 0; padding: 0; }
  .state.ok, .state.warn { animation: pop 0.35s var(--spring); }
  .state.ok::before, .state.warn::before { content: ''; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
  .state.ok { color: var(--accent); }
  .state.warn { color: var(--signal-text); cursor: pointer; }
  .caret { display: inline-block; transition: rotate 0.3s var(--spring); }
  .caret.up { rotate: 180deg; }
  .issues {
    position: absolute;
    left: 0;
    bottom: calc(100% + 14px);
    width: min(460px, 100%);
    max-height: 260px;
    overflow: auto;
    margin: 0;
    padding: 12px 16px 12px 32px;
    color: var(--text);
    font-size: 13px;
    box-shadow: var(--shadow-lift);
  }

  @media (max-width: 640px) {
    .flow, .bar { margin-inline: -16px; padding-inline: 16px; }
    .step-head { padding: 16px 16px 0; }
    .body { padding: 14px 16px 18px; }
    .flush :global(.tabs) { padding-left: 6px; }
  }
</style>
