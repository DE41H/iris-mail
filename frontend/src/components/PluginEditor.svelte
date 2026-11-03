<script lang="ts">
  import type { Snippet } from 'svelte';
  import { pluginProblems, problems, type Draft } from '../lib/schema';
  import { message } from '../lib/api';
  import Builder from './Builder.svelte';
  import SchemaPreview from './SchemaPreview.svelte';

  interface Props {
    draft: Draft;
    submit: string;
    onsubmit: () => Promise<unknown>;
    dirty?: boolean;
    locked?: string;
    children?: Snippet;
  }

  let { draft = $bindable(), submit, onsubmit, dirty = true, locked = '', children }: Props = $props();

  let busy = $state(false);
  let error = $state('');
  let open = $state(false);
  const issues = $derived([...pluginProblems(draft.name, draft.desc, draft.hint), ...(locked ? [] : problems(draft.fields))]);

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

<form class="editor" onsubmit={save} novalidate>
  <div class="main stack">
    <section class="card reveal" style:--i={1}>
      <div class="card-head"><span>01 / identity</span><span>what is this plugin for?</span></div>
      <div class="card-body">
        <div class="grid-2">
          <div class="field">
            <label for="name">name</label>
            <input id="name" class="mono" type="text" value={draft.name} oninput={slugify} placeholder="receipts" maxlength="255" autocomplete="off" spellcheck="false" />
            <div class="help">Lowercase, numbers, - and _. Unique to you.</div>
          </div>
          <div class="field">
            <label for="desc">description <span class="count">{draft.desc.length}/1024</span></label>
            <input id="desc" type="text" bind:value={draft.desc} placeholder="Finds receipts and sorts spending." maxlength="1024" />
            <div class="help">Users see this when they turn the plugin on.</div>
          </div>
        </div>
        <div class="field">
          <label for="hint">hint for laya <span class="count">{draft.hint.length}/512</span></label>
          <input id="hint" type="text" bind:value={draft.hint} placeholder="Order confirmations and invoices from online shops." maxlength="512" />
          <div class="help">Describe the kind of email this plugin cares about. Laya reads it as context.</div>
        </div>
      </div>
    </section>

    <section class="card reveal" style:--i={2}>
      <div class="card-head"><span>02 / questions</span><span>one answer per question, per email</span></div>
      <div class="card-body">
        {#if locked}
          <div class="alert alert-danger">{locked}</div>
        {:else}
          <Builder bind:fields={draft.fields} />
        {/if}
      </div>
    </section>
  </div>

  <aside class="side reveal" style:--i={3}>
    <SchemaPreview fields={draft.fields} />
  </aside>

  <div class="bar">
    {#if error}<div class="alert alert-danger" role="alert">{error}</div>{/if}
    {#if open && issues.length}
      <ul class="issues" role="status">
        {#each issues as issue}<li>{issue}</li>{/each}
      </ul>
    {/if}
    <div class="row">
      {#if locked}
        <span class="muted">Editing is off for this schema.</span>
      {:else if issues.length}
        <button type="button" class="state warn" onclick={() => (open = !open)} aria-expanded={open}>
          ● {issues.length} {issues.length === 1 ? 'thing' : 'things'} to fix {open ? '▴' : '▾'}
        </button>
      {:else if dirty}
        <span class="state ok">● ready</span>
      {:else}
        <span class="state">no changes</span>
      {/if}
      {@render children?.()}
      <button class="btn btn-primary" type="submit" disabled={busy || !dirty || !!locked}>{busy ? 'saving…' : submit}</button>
    </div>
  </div>
</form>

<style>
  .editor { display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 20px; align-items: start; }
  .side { position: sticky; top: 76px; }
  .count { float: right; font-weight: 400; }
  .bar {
    grid-column: 1 / -1;
    position: sticky;
    bottom: 16px;
    display: grid;
    gap: 8px;
    padding: 12px 14px;
    border: 1px solid var(--border-strong);
    border-radius: var(--radius);
    background: rgba(10, 15, 13, 0.88);
    backdrop-filter: blur(12px);
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5);
    animation: rise 0.5s var(--ease) 0.3s both;
  }
  .row { display: flex; align-items: center; gap: 8px; justify-content: flex-end; }
  .state { margin-right: auto; font: 12px var(--mono); color: var(--muted); background: none; border: 0; padding: 0; }
  .state.ok { color: var(--green); }
  .state.warn { color: var(--amber); cursor: pointer; }
  .issues { margin: 0; padding: 0 0 0 18px; max-height: 160px; overflow: auto; color: var(--amber); font-size: 12px; }
  @media (max-width: 960px) {
    .editor { grid-template-columns: 1fr; }
    .side { position: static; }
  }
</style>
