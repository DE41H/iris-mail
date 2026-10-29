<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '#lib/api';
  import Builder from '#lib/components/Builder.svelte';
  import KeyCard from '#lib/components/KeyCard.svelte';
  import { type Field, fromSchema, pluginProblems, problems, toSchema } from '#lib/schema';

  interface Plugin {
    id: string;
    name: string;
    desc: string;
    hint: string;
    schema: unknown;
    prefix: string | null;
  }

  const errorText = (err: unknown) => (err instanceof Error ? err.message : 'Something went wrong.');

  let id = $state('');
  let title = $state('Plugin');
  let name = $state('');
  let desc = $state('');
  let hint = $state('');
  let fields = $state<Field[]>([]);
  let prefix = $state<string | null>(null);
  let unsupported = $state('');
  let loaded = $state(false);
  let saving = $state(false);
  let saved = $state('');
  let notice = $state('');
  let error = $state('');
  let rotatedKey = $state('');
  let arming = $state<'rotate' | 'delete' | null>(null);
  let timer = 0;

  const snap = () => JSON.stringify([name, desc, hint, fields]);

  // Recomputed on every keystroke and every builder edit.
  const found = $derived([...pluginProblems(name, desc, hint), ...problems(fields)]);
  const dirty = $derived(snap() !== saved);
  // Save is only live when something changed, the schema is editable and every check passes.
  const canSave = $derived(loaded && !unsupported && dirty && found.length === 0 && !saving);

  onMount(async () => {
    id = new URLSearchParams(location.search).get('id') ?? '';
    if (!id) {
      location.href = '/plugins/';
      return;
    }
    try {
      const plugin = await api<Plugin>(`/api/plugins/${id}/`);
      title = plugin.name;
      name = plugin.name;
      desc = plugin.desc;
      hint = plugin.hint;
      prefix = plugin.prefix;
      const parsed = fromSchema(plugin.schema);
      if ('error' in parsed) unsupported = parsed.error;
      else fields = parsed.fields;
      saved = snap();
      loaded = true;
    } catch (err) {
      error = errorText(err);
    }
  });

  const save = async (event: SubmitEvent) => {
    event.preventDefault();
    if (!canSave) return;
    const sent = snap();
    saving = true;
    try {
      const plugin = await api<Plugin>(`/api/plugins/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify({ name, desc, hint, schema: toSchema(fields) }),
      });
      title = plugin.name;
      saved = sent;
      error = '';
      notice = 'Changes saved.';
    } catch (err) {
      notice = '';
      error = errorText(err);
    }
    saving = false;
  };

  // First click arms the button; a second click within 4 seconds runs the action.
  const arm = (action: 'rotate' | 'delete', run: () => Promise<void>) => {
    clearTimeout(timer);
    if (arming !== action) {
      arming = action;
      timer = window.setTimeout(() => (arming = null), 4000);
      return;
    }
    arming = null;
    run();
  };

  const rotate = async () => {
    error = '';
    try {
      const { key } = await api<{ key: string }>(`/api/plugins/${id}/rotate_key/`, { method: 'POST' });
      rotatedKey = key;
      prefix = key.slice(0, 16);
    } catch (err) {
      error = errorText(err);
    }
  };

  const remove = async () => {
    error = '';
    try {
      await api(`/api/plugins/${id}/`, { method: 'DELETE' });
      location.href = '/plugins/';
    } catch (err) {
      error = errorText(err);
    }
  };
</script>

<svelte:head><title>{title} · Iris</title></svelte:head>

<div class="page-head">
  <div>
    <div class="eyebrow">PLUGIN STUDIO / CONFIGURATION</div>
    <h1 class="mono">{title}</h1>
    <p class="muted">Tune the questions and access for this email agent.</p>
  </div>
  <a class="btn" href="/plugins/">All plugins</a>
</div>

{#if error}<div class="alert alert-danger" role="alert">{error}</div>{/if}
{#if notice}<div class="alert alert-success" role="status">{notice}</div>{/if}
{#if rotatedKey}<KeyCard key={rotatedKey} />{/if}

<form class="stack" onsubmit={save}>
  <section class="card">
    <div class="card-body">
      <div class="grid-2">
        <div class="field">
          <label for="name">Name</label>
          <input id="name" name="name" class="mono" type="text" required autocomplete="off" spellcheck="false" bind:value={name} />
        </div>
        <div class="field">
          <label for="desc">Description</label>
          <input id="desc" name="desc" type="text" bind:value={desc} />
        </div>
      </div>
      <div class="field">
        <label for="hint">Hint</label>
        <input id="hint" name="hint" type="text" bind:value={hint} />
        <div class="help">Helps Laya know what to look for in an email.</div>
      </div>
    </div>
  </section>

  <section class="card">
    <div class="card-head">QUESTION DESIGN</div>
    <div class="card-body">
      {#if unsupported}
        <div class="alert alert-danger">{unsupported}</div>
      {:else if loaded}
        <Builder bind:fields />
      {/if}
    </div>
  </section>

  <ul class="problems" role="status">
    {#each found as message}
      <li>{message}</li>
    {/each}
  </ul>
  <div class="actions">
    {#if dirty}<span class="muted">Unsaved changes</span>{/if}
    <button class="btn btn-primary" type="submit" disabled={!canSave}>{saving ? 'Saving…' : 'Save changes'}</button>
  </div>
</form>

<section class="card">
  <div class="card-head">Access</div>
  <div class="card-body">
    <p class="mono muted">{prefix ? `Key prefix ${prefix}…` : 'No key issued'}</p>
    <p class="muted">Rotating issues a new key and stops the current one immediately.</p>
    <button class="btn" type="button" onclick={() => arm('rotate', rotate)}>{arming === 'rotate' ? 'Confirm rotate' : 'Rotate key'}</button>
  </div>
</section>

<section class="card danger">
  <div class="card-head">Danger zone</div>
  <div class="card-body">
    <p class="muted">Deleting removes the plugin, its subscriptions and its results. This cannot be undone.</p>
    <button class="btn btn-danger" type="button" onclick={() => arm('delete', remove)}>{arming === 'delete' ? 'Really delete?' : 'Delete plugin'}</button>
  </div>
</section>
