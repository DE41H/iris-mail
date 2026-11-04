<script lang="ts">
  import type { Snippet } from 'svelte';
  import { fly } from 'svelte/transition';
  import { pluginProblems, problems, type Draft } from '../lib/schema';
  import { message } from '../lib/api';
  import Builder from './Builder.svelte';
  import SchemaPreview from './SchemaPreview.svelte';

  interface Props {
    draft: Draft;
    submit: string;
    onsubmit: () => Promise<unknown>;
    head: Snippet;
    dirty?: boolean;
    locked?: string;
    children?: Snippet;
  }

  let { draft = $bindable(), submit, onsubmit, head, dirty = true, locked = '', children }: Props = $props();

  let busy = $state(false);
  let error = $state('');
  let open = $state(false);
  const issues = $derived([...pluginProblems(draft.name, draft.desc), ...(locked ? [] : problems(draft.fields))]);

  const slugify = (e: Event) =>
    (draft.name = (e.currentTarget as HTMLInputElement).value.toLowerCase().replace(/\s+/g, '-').replace(/[^-a-z0-9_]/g, ''));

  async function save(e: SubmitEvent) {
    e.preventDefault();
    if (issues.length || locked) return (open = true);
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

<form class="editor grow" onsubmit={save} novalidate>
  <div class="page-head top reveal">
    <div>{@render head()}</div>
    <div class="actions">
      {#if locked}
        <span class="state">read only</span>
      {:else if issues.length}
        <button type="button" class="state warn" onclick={() => (open = !open)} aria-expanded={open}>● {issues.length} to fix {open ? '▴' : '▾'}</button>
      {:else if dirty}
        <span class="state ok">● ready</span>
      {:else}
        <span class="state">saved</span>
      {/if}
      {@render children?.()}
      <button class="btn btn-primary" type="submit" disabled={busy || !dirty || !!locked}>{busy ? 'saving…' : submit}</button>
    </div>
    {#if open && issues.length}
      <ul class="card issues" role="status" transition:fly={{ y: -6, duration: 150 }}>
        {#each issues as issue}<li>{issue}</li>{/each}
      </ul>
    {/if}
  </div>
  {#if error}<div class="alert alert-danger" role="alert">{error}</div>{/if}

  <div class="cols grow">
    <div class="left">
      <section class="card ident reveal d1">
        <label>
          <span class="label">name</span>
          <input class="mono" type="text" value={draft.name} oninput={slugify} placeholder="receipts" maxlength="255" autocomplete="off" spellcheck="false" />
        </label>
        <label>
          <span class="label">description</span>
          <input type="text" bind:value={draft.desc} placeholder="Shown to users" maxlength="1024" />
        </label>
      </section>

      <section class="card questions grow reveal d2">
        {#if locked}
          <div class="alert alert-danger">{locked}</div>
        {:else}
          <Builder bind:fields={draft.fields} />
        {/if}
      </section>
    </div>

    <aside class="side reveal d3">
      <SchemaPreview fields={draft.fields} />
    </aside>
  </div>
</form>

<style>
  .editor { display: flex; flex-direction: column; gap: 12px; }
  .top { position: relative; z-index: 6; }
  .cols { display: grid; grid-template-columns: minmax(0, 1fr) 340px; gap: 16px; }
  .left { display: flex; flex-direction: column; gap: 12px; min-height: 0; }
  .side { min-height: 0; display: flex; }
  .ident { display: grid; grid-template-columns: 1fr 1.5fr 1.5fr; gap: 12px; padding: 12px 14px; }
  .ident .label { margin-bottom: 4px; }
  .questions { display: flex; flex-direction: column; padding: 12px 14px; }
  .state { font: 12px var(--mono); color: var(--muted); background: none; border: 0; padding: 0 6px; }
  .state.ok { color: var(--green); }
  .state.warn { color: var(--amber); cursor: pointer; }
  .issues {
    position: absolute;
    right: 0;
    top: calc(100% + 6px);
    z-index: 5;
    width: min(440px, 100%);
    max-height: 240px;
    overflow: auto;
    margin: 0;
    padding: 10px 14px 10px 28px;
    color: var(--amber);
    font-size: 12px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5);
  }
  @media (max-width: 960px) {
    .cols, .ident { grid-template-columns: minmax(0, 1fr); }
  }
</style>
