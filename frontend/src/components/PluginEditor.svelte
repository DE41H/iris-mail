<script lang="ts">
  import type { Snippet } from 'svelte';
  import { fly } from 'svelte/transition';
  import { fieldProblems, MAX_FIELDS, MAX_RULES, pluginProblems, type Draft } from '../lib/schema';
  import { problems, ruleProblems } from '../lib/rules';
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
    steps?: boolean; // numbered steps for a new plugin; plain sections when editing one
    tools?: Snippet; // top right, beside the title
    aside?: Snippet; // top of the side column, above the live output
    children?: Snippet; // page head, beside the submit button
  }

  let { draft = $bindable(), submit, onsubmit, head, dirty = true, locked = '', steps = true, tools, aside, children }: Props = $props();

  let busy = $state(false);
  let error = $state('');
  let open = $state(false);
  let tried = $state(false); // problems are only called out once saving was attempted
  const sections: HTMLElement[] = $state([]);
  const named = $derived(pluginProblems(draft.name, draft.desc, draft.redirect));
  const fieldsOk = $derived(draft.fields.every((f) => !fieldProblems(f, draft.fields).length));
  const issues = $derived([...named, ...(locked ? [] : problems(draft.fields, draft.rules))]);
  // A step shows a check once it is filled in and has nothing to fix.
  const done = $derived({
    name: !named.length,
    questions: !!draft.fields.length && fieldsOk,
    rules: !!draft.rules.length && draft.rules.every((r) => !ruleProblems(r, draft.rules).length),
  });

  const slugify = (e: Event) =>
    (draft.name = (e.currentTarget as HTMLInputElement).value.toLowerCase().replace(/\s+/g, '-').replace(/[^-a-z0-9_]/g, ''));

  async function save(e: SubmitEvent) {
    e.preventDefault();
    if (busy) return; // Enter pressed again while saving would send a second request
    if (issues.length || locked) {
      tried = open = true;
      // Jump to the first section that still needs work, like a checkout form does.
      const at = !done.name ? 0 : !fieldsOk || !(draft.fields.length || draft.rules.length) ? 1 : 2;
      sections[at]?.scrollIntoView({ behavior: 'smooth', block: 'start' });
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

{#snippet status()}
  {#if locked}
    <span class="state">Read only</span>
  {:else if issues.length && tried}
    <button type="button" class="state warn" onclick={() => (open = !open)} aria-expanded={open}>{issues.length} to fix <span class="caret" class:up={open}>▾</span></button>
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
{/snippet}

{#snippet title(n: number, text: string, ok: boolean, count?: string)}
  <header class="sec-head">
    {#if steps}<span class="n" class:ok aria-hidden="true">{#if ok}<svg viewBox="0 0 16 16"><path d="M3.5 8.5l3 3 6-7" /></svg>{:else}{n}{/if}</span>{/if}
    <h2>{text}{#if count}<span class="count">{count}</span>{/if}</h2>
  </header>
{/snippet}

<form class="editor grow" class:plain={!steps} onsubmit={save} novalidate>
  <div class="page-head reveal">
    <div>{@render head()}</div>
    <div class="actions top">
      {@render status()}
      {@render tools?.()}
    </div>
  </div>

  <div class="cols grow">
    <div class="main scroll">
      {#if error}<div class="alert alert-danger" role="alert">{error}</div>{/if}

      <section class="card sec reveal d1" bind:this={sections[0]}>
        {@render title(1, steps ? 'Name it' : 'Details', done.name)}
        <div class="body">
          <label>
            <span class="label">Name</span>
            <input class="mono" type="text" value={draft.name} oninput={slugify} placeholder="receipts" maxlength="255" autocomplete="off" spellcheck="false" />
          </label>
          <label>
            <span class="label">Description</span>
            <textarea rows="1" bind:value={draft.desc} placeholder="Finds receipts and sorts them by what was bought." maxlength="1024"></textarea>
          </label>
          <label>
            <span class="label">Redirect URL</span>
            <input class="mono" type="url" bind:value={draft.redirect} placeholder="https://yourapp.com/iris/done" maxlength="256" autocomplete="off" spellcheck="false" />
          </label>
        </div>
      </section>

      <section class="card sec reveal d2" bind:this={sections[1]}>
        {@render title(2, 'Questions', done.questions, locked ? '' : `${draft.fields.length} / ${MAX_FIELDS}`)}
        <div class="body">
          {#if locked}
            <div class="alert alert-danger">{locked}</div>
          {:else}
            <Builder bind:fields={draft.fields} />
          {/if}
        </div>
      </section>

      {#if !locked}
        <section class="card sec reveal d3" bind:this={sections[2]}>
          {@render title(3, 'Rules', done.rules, draft.rules.length ? `${draft.rules.length} / ${MAX_RULES}` : '')}
          <div class="body">
            <RuleList bind:rules={draft.rules} />
          </div>
        </section>
      {/if}
    </div>

    {#if aside}<div class="side reveal d1">{@render aside()}</div>{/if}

    <section class="card output reveal d2" class:tall={!aside}>
      <header class="out-head"><h2>Output</h2></header>
      <SchemaPreview fields={draft.fields} rules={draft.rules} />
    </section>
  </div>
</form>

<style>
  .editor { display: flex; flex-direction: column; gap: 16px; }
  /* The reveal animation makes the head its own stacking context; lift it so the issues dropdown covers the cards below. */
  .page-head { position: relative; z-index: 6; }

  /* Edit on the left, see the result on the right: both columns scroll on their own. */
  .cols {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(300px, 380px);
    grid-template-rows: auto minmax(0, 1fr);
    grid-template-areas: 'main side' 'main out';
    gap: 16px 20px;
  }
  .main { grid-area: main; display: grid; grid-template-columns: minmax(0, 1fr); align-content: start; gap: 16px; margin: -4px; padding: 4px 4px 24px; scroll-padding: 12px; }
  .side { grid-area: side; display: grid; gap: 16px; }
  .output { grid-area: out; display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
  .output.tall { grid-row: 1 / -1; }

  .sec { padding: 0; }
  .sec-head { display: flex; align-items: center; gap: 14px; padding: 18px 22px 0; }
  .sec-head h2 { display: flex; align-items: baseline; gap: 10px; font-size: 16px; font-weight: 640; font-stretch: 108%; color: var(--text); }
  .count { font-size: 12.5px; font-weight: 500; font-stretch: 100%; letter-spacing: 0; color: var(--faint); font-variant-numeric: tabular-nums; }
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
  .plain .body { padding-left: 22px; }
  .body label { display: block; }

  .out-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; padding: 14px 18px 0; }
  .out-head h2 { font-size: 15px; color: var(--text); }

  /* Status and save sit in the page head. */
  .top { position: relative; }
  .top .actions { display: contents; }
  .state { display: inline-flex; align-items: center; gap: 7px; font: 540 13px var(--font); color: var(--muted); background: none; border: 0; padding: 0; }
  .state.warn { animation: pop 0.35s var(--spring); }
  .state.warn::before { content: ''; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
  .state.warn { color: var(--signal-text); cursor: pointer; }
  .caret { display: inline-block; transition: rotate 0.3s var(--spring); }
  .caret.up { rotate: 180deg; }
  .issues {
    position: absolute;
    right: 0;
    top: calc(100% + 10px);
    z-index: 5;
    width: min(460px, calc(100vw - 32px));
    max-height: 260px;
    overflow: auto;
    margin: 0;
    padding: 12px 16px 12px 32px;
    color: var(--text);
    font-size: 13px;
    background: color-mix(in oklab, var(--signal) 8%, var(--surface));
    border-color: color-mix(in oklab, var(--signal) 45%, var(--border));
    border-left: 3px solid var(--signal);
    box-shadow: var(--shadow-lift);
  }

  /* One column: the key comes first, the output last. The page scrolls instead of the columns. */
  @media (max-width: 960px), (max-height: 600px) {
    .cols { display: flex; flex-direction: column; }
    .side { order: -1; }
    .main { overflow: visible; padding-bottom: 0; }
    .output :global(pre) { max-height: 360px; }
  }
  @media (max-width: 640px) {
    .sec-head { padding: 16px 16px 0; }
    .body, .plain .body { padding: 14px 16px 18px; }
  }
</style>
