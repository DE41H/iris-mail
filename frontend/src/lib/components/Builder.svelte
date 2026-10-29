<script lang="ts">
  import { tick } from 'svelte';
  import { type Field, MAX_FIELDS, toSchema } from '#lib/schema';

  let { fields = $bindable([]) }: { fields: Field[] } = $props();

  let root: HTMLElement;

  // Changing a field's type starts it fresh, keeping only its name and question.
  const retype = (i: number, kind: Field['kind']) => {
    const { name, question } = fields[i];
    fields[i] =
      kind === 'choice' ? { kind, name, question, options: [] }
      : kind === 'scale' ? { kind, name, question, min: 0, max: 4 }
      : { kind, name, question };
  };

  const addField = async () => {
    fields = [...fields, { kind: 'choice', name: '', question: '', options: [] }];
    await tick();
    root.querySelector<HTMLInputElement>('.field-card:last-child .field-name')?.focus();
  };

  const addOption = async (f: Extract<Field, { kind: 'choice' }>, card: HTMLElement) => {
    f.options.push('');
    await tick();
    card.querySelector<HTMLInputElement>('.option-line:last-child input')?.focus();
  };

  const KINDS = [
    ['choice', 'Choice'],
    ['boolean', 'Yes / no'],
    ['scale', 'Scale'],
  ] as const;
</script>

<div bind:this={root}>
  <div class="builder-head">
    <div>Questions</div>
    <span class="field-count">{fields.length} / {MAX_FIELDS} fields</span>
  </div>

  <div class="fields">
    {#if fields.length}
      {#each fields as f, i (i)}
        <div class="field-card" style:--field-index={i}>
          <div class="field-top">
            <span class="field-index">{String(i + 1).padStart(2, '0')}</span>
            <input class="mono field-name" type="text" placeholder="field_name" spellcheck="false" autocomplete="off" aria-label="Field {i + 1} name" bind:value={f.name} />
            <div class="seg" role="radiogroup" aria-label="Field {i + 1} type">
              {#each KINDS as [kind, label] (kind)}
                <label>
                  <input type="radio" name="kind-{i}" value={kind} checked={f.kind === kind} onchange={() => retype(i, kind)} />
                  <span>{label}</span>
                </label>
              {/each}
            </div>
            <button type="button" class="btn-link" aria-label="Remove field {i + 1}" onclick={() => (fields = fields.filter((_, j) => j !== i))}>Remove</button>
          </div>

          <input class="field-question" type="text" placeholder="Question for Laya, e.g. Is this a receipt?" spellcheck="false" autocomplete="off" aria-label="Field {i + 1} question" bind:value={f.question} />

          {#if f.kind === 'choice'}
            <div class="option-box">
              <div class="option-title">Possible answers</div>
              <div class="option-list">
                {#each f.options as _, oi}
                  <div class="option-line">
                    <input type="text" placeholder="Option {oi + 1}" spellcheck="false" autocomplete="off" aria-label="Field {i + 1} option {oi + 1}" bind:value={f.options[oi]} onchange={() => (f.options[oi] = f.options[oi].trim())} />
                    <button type="button" class="option-remove" aria-label="Remove option {oi + 1}" onclick={() => f.options.splice(oi, 1)}>×</button>
                  </div>
                {/each}
              </div>
              <button type="button" class="btn btn-sm option-add" onclick={(event) => addOption(f, event.currentTarget.closest('.field-card') as HTMLElement)}>+ Add answer</button>
            </div>
          {:else if f.kind === 'scale'}
            <div class="range">
              <span class="muted">From</span>
              <input type="number" step="1" aria-label="Field {i + 1} lowest value" bind:value={f.min} />
              <span class="muted">to</span>
              <input type="number" step="1" aria-label="Field {i + 1} highest value" bind:value={f.max} />
            </div>
          {:else}
            <div class="type-note">A clear yes or no for each email.</div>
          {/if}
        </div>
      {/each}
    {:else}
      <div class="empty">No fields yet. Each field is one question Laya answers per email.</div>
    {/if}
  </div>

  <button type="button" class="btn btn-sm" disabled={fields.length >= MAX_FIELDS} onclick={addField}>Add field</button>

  <section class="schema-preview">
    <div class="preview-head">
      <span class="eyebrow">LIVE OUTPUT</span>
      <span class="muted">JSON schema</span>
    </div>
    <pre class="preview mono">{JSON.stringify(toSchema(fields), null, 2)}</pre>
  </section>
</div>
