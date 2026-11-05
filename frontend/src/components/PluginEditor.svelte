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
    children?: Snippet; // bottom bar, beside the submit button
  }

  let { draft = $bindable(), submit, onsubmit, head, dirty = true, locked = '', steps = true, tools, aside, children }: Props = $props();

  let busy = $state(false);
  let error = $state('');
  let open = $state(false);
  let tried = $state(false); // problems are only called out once saving was attempted
  const sections: HTMLElement[] = $state([]);
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
      // Jump to the first section that still needs work, like a checkout form does.
      const fieldsOk = draft.fields.every((f) => !fieldProblems(f, draft.fields).length) && (draft.fields.length || draft.rules.length);
      const at = !done.name ? 0 : !fieldsOk ? 1 : 2;
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

{#snippet title(n: number, text: string, hint: string, ok: boolean, count?: string)}
  <header class="sec-head">
    {#if steps}<span class="n" class:ok aria-hidden="true">{#if ok}<svg viewBox="0 0 16 16"><path d="M3.5 8.5l3 3 6-7" /></svg>{:else}{n}{/if}</span>{/if}
    <div>
      <h2>{text}{#if count}<span class="count">{count}</span>{/if}</h2>
      <p>{hint}</p>
    </div>
  </header>
{/snippet}

<form class="editor grow" class:plain={!steps} onsubmit={save} novalidate>
  <div class="page-head reveal">
    <div>{@render head()}</div>
    {#if tools}<div class="actions">{@render tools()}</div>{/if}
  </div>

  <div class="cols grow">
    <div class="main scroll">
      {#if error}<div class="alert alert-danger" role="alert">{error}</div>{/if}

      <section class="card sec reveal d1" bind:this={sections[0]}>
        {@render title(1, steps ? 'Name it' : 'Details', 'People see this when they choose plugins to switch on.', done.name)}
        <div class="body details">
          <label>
            <span class="label">Name</span>
            <input class="mono" type="text" value={draft.name} oninput={slugify} placeholder="receipts" maxlength="255" autocomplete="off" spellcheck="false" />
            <span class="help">Used in API calls.</span>
          </label>
          <label>
            <span class="label">Description</span>
            <textarea rows="2" bind:value={draft.desc} placeholder="Finds receipts and sorts them by what was bought." maxlength="1024"></textarea>
          </label>
        </div>
      </section>

      <section class="card sec reveal d2" bind:this={sections[1]}>
        {@render title(2, 'Questions', 'Laya answers each one for every new email.', done.questions, locked ? '' : `${draft.fields.length} / ${MAX_FIELDS}`)}
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
          {@render title(3, 'Exact text', 'Optional. Patterns copy things like amounts or order numbers word for word.', done.rules, draft.rules.length ? `${draft.rules.length} / ${MAX_RULES}` : '')}
          <div class="body">
            <RuleList bind:rules={draft.rules} />
          </div>
        </section>
      {/if}
    </div>

    {#if aside}<div class="side reveal d1">{@render aside()}</div>{/if}

    <section class="card output reveal d2" class:tall={!aside}>
      <header class="out-head"><h2>Output</h2><span class="live">Updates as you type</span></header>
      <SchemaPreview fields={draft.fields} rules={draft.rules} />
    </section>
  </div>

  <div class="bar">
    {#if locked}
      <span class="state">Read only</span>
    {:else if issues.length && !tried}
      <span class="state">Not ready yet</span>
    {:else if issues.length}
      <button type="button" class="state warn" onclick={() => (open = !open)} aria-expanded={open}>{issues.length} to fix <span class="caret" class:up={open}>▾</span></button>
    {:else if dirty}
      <span class="state ok">Unsaved changes</span>
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
</form>

<style>
  .editor { display: flex; flex-direction: column; gap: 16px; }

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
  .sec-head { display: flex; align-items: flex-start; gap: 14px; padding: 18px 22px 0; }
  .sec-head h2 { display: flex; align-items: baseline; gap: 10px; font-size: 16px; font-weight: 640; font-stretch: 108%; color: var(--text); }
  .sec-head p { margin-top: 2px; font-size: 13.5px; color: var(--muted); }
  .sec-head > div { flex: 1; min-width: 0; }
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
  .details { grid-template-columns: minmax(0, 2fr) minmax(0, 3fr); align-items: start; }
  .body label { display: block; }
  .body .help { margin-top: 6px; }
  textarea { resize: vertical; min-height: 44px; }

  .out-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; padding: 14px 18px 0; }
  .out-head h2 { font-size: 15px; color: var(--text); }
  .live { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: var(--muted); }
  .live::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: var(--accent); }

  .bar {
    position: sticky;
    bottom: 0;
    z-index: 5;
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin: -4px -24px -20px;
    padding: 12px 24px 14px;
    background: color-mix(in oklab, var(--bg) 82%, transparent);
    backdrop-filter: blur(10px);
    border-top: 1px solid var(--border);
  }
  .bar .actions { margin-left: auto; }
  .state { display: inline-flex; align-items: center; gap: 7px; font: 540 13px var(--font); color: var(--muted); background: none; border: 0; padding: 0; }
  .state.ok, .state.warn { animation: pop 0.35s var(--spring); }
  .state.ok::before, .state.warn::before { content: ''; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
  .state.ok { color: var(--accent); }
  .state.warn { color: var(--signal-text); cursor: pointer; }
  .caret { display: inline-block; transition: rotate 0.3s var(--spring); }
  .caret.up { rotate: 180deg; }
  .issues {
    position: absolute;
    left: 24px;
    bottom: calc(100% + 10px);
    width: min(460px, calc(100% - 48px));
    max-height: 260px;
    overflow: auto;
    margin: 0;
    padding: 12px 16px 12px 32px;
    color: var(--text);
    font-size: 13px;
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
    .bar { margin-inline: -16px; padding-inline: 16px; }
    .sec-head { padding: 16px 16px 0; }
    .body, .plain .body { padding: 14px 16px 18px; }
    .details { grid-template-columns: minmax(0, 1fr); }
  }
</style>
