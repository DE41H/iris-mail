<script lang="ts">
  import { api, ApiError } from '#lib/api';
  import Builder from '#lib/components/Builder.svelte';
  import KeyCard from '#lib/components/KeyCard.svelte';
  import { type Field, pluginProblems, problems, toSchema } from '#lib/schema';

  let name = $state('');
  let desc = $state('');
  let hint = $state('');
  let fields = $state<Field[]>([]);
  let submitting = $state(false);
  let serverError = $state('');
  let created = $state<{ id: string; key: string } | null>(null);

  // Recomputed on every keystroke and every builder edit, so the list and the button always match the form.
  const found = $derived([...pluginProblems(name, desc, hint), ...problems(fields)]);

  const create = async (event: SubmitEvent) => {
    event.preventDefault();
    if (found.length) return;
    submitting = true;
    serverError = '';
    try {
      created = await api<{ id: string; key: string }>('/api/plugins/', {
        method: 'POST',
        body: JSON.stringify({ name, desc, hint, schema: toSchema(fields) }),
      });
    } catch (err) {
      serverError = err instanceof ApiError ? err.message : 'Something went wrong.';
      submitting = false;
    }
  };
</script>

<svelte:head><title>New plugin · Iris</title></svelte:head>

<div class="page-head">
  <div>
    <div class="eyebrow">PLUGIN STUDIO / NEW</div>
    <h1>Create an email agent</h1>
    <p class="muted">Give it a purpose, then write the questions it should answer.</p>
  </div>
</div>

{#if created}
  <KeyCard key={created.key}>
    <a class="btn btn-sm" href="/plugins/detail/?id={created.id}">Open plugin</a>
    <a class="btn btn-sm" href="/plugins/">All plugins</a>
  </KeyCard>
{:else}
  <form class="stack" onsubmit={create}>
    <section class="card">
      <div class="card-body">
        <div class="grid-2">
          <div class="field">
            <label for="name">Name</label>
            <input id="name" name="name" class="mono" type="text" required autocomplete="off" spellcheck="false" aria-describedby="name-help" bind:value={name} />
            <div id="name-help" class="help">Lowercase letters, numbers, - and _. Unique to you.</div>
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
      <div class="card-head"><span>01 / QUESTION DESIGN</span><span class="muted">Up to 32 questions</span></div>
      <div class="card-body">
        <p class="muted">Each question becomes one structured value in your results.</p>
        <Builder bind:fields />
      </div>
    </section>

    <ul class="problems" role="status">
      {#each found as message}
        <li>{message}</li>
      {/each}
    </ul>
    {#if serverError}
      <div class="alert alert-danger" role="alert">{serverError}</div>
    {/if}
    <div class="actions">
      <a class="btn" href="/plugins/">Cancel</a>
      <button class="btn btn-primary" type="submit" disabled={found.length > 0 || submitting}>{submitting ? 'Creating…' : 'Create plugin'}</button>
    </div>
  </form>
{/if}
