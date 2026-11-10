<script lang="ts">
  import Json from './Json.svelte';
  import VersionPicker from './VersionPicker.svelte';

  type Schema = Record<string, any>;
  interface Op { method: string; path: string; op: Schema }

  let spec = $state<Schema | null>(null);
  let error = $state('');
  let versions = $state<string[]>([]);
  let version = $state('');

  // Static files written by `gen_schema` in docker/deploy.sh.
  const get = (file: string) =>
    fetch(`/static/schema/${file}.json`).then((r) => (r.ok ? r.json() : Promise.reject(new Error(`Could not load the docs (${r.status}).`))));

  get('versions')
    .then((vs: string[]) => {
      versions = vs;
      version = vs.at(-1)!;
    })
    .catch((err) => (error = err.message));

  $effect(() => {
    const v = version;
    if (!v) return;
    error = '';
    get(v)
      .then((s) => v === version && (spec = s))
      .catch((err) => v === version && (error = err.message));
  });

  const ref = (s: Schema): Schema => (s?.$ref ? spec!.components.schemas[s.$ref.split('/').pop()] : s);

  // Turns a JSON schema into a readable sample: each leaf becomes its type, e.g. "string (uuid)".
  // `skip` drops readOnly fields from requests and writeOnly fields from responses.
  const shape = (s: Schema, skip = '', depth = 0): unknown => {
    s = ref(s);
    if (!s || depth > 6) return '…';
    if (s.allOf) return shape(s.allOf[0], skip, depth);
    if (s.oneOf) return s.oneOf.map((o: Schema) => shape(o, skip, depth + 1));
    if (s.enum) return s.enum.join(' | ');
    if (s.type === 'array') return [shape(s.items, skip, depth + 1)];
    if (s.type === 'object' || s.properties) {
      const props = Object.entries<Schema>(s.properties ?? {}).filter(([, p]) => !(skip && p[skip]));
      return Object.fromEntries(props.map(([k, p]) => [k, shape(p, skip, depth + 1)]));
    }
    return [s.format ?? s.type, s.nullable && '| null'].filter(Boolean).join(' ');
  };

  const body = (content: Schema | undefined, skip: string) => {
    const s = content?.['application/json']?.schema;
    return s && shape(s, skip);
  };

  // The base path is in the intro, so each path drops it.
  const ops = $derived<Op[]>(
    spec
      ? Object.entries<Schema>(spec.paths).flatMap(([path, methods]) =>
          Object.entries<Schema>(methods).map(([method, op]) => ({ method, path: path.replace(/^\/api\/v\d+/, ''), op })),
        )
      : [],
  );
  // Odd pieces of a split on backticks are inline code.
  const parts = (text = '') => text.split('`');
</script>

<div class="page-head reveal">
  <div><h1>The Iris API</h1></div>
  <VersionPicker {versions} bind:value={version} />
</div>

{#if error}
  <div class="alert alert-danger" role="alert">{error}</div>
{:else if spec}
  <section class="card reveal docs">
    <div class="grow scroll">
      {#snippet text(t: string | undefined)}{#each parts(t) as part, i}{#if i % 2}<code>{part}</code>{:else}{part}{/if}{/each}{/snippet}
      <p class="card-body muted intro">{@render text(spec.info.description)}</p>
      {#each ops as { method, path, op } (method + path)}
        {@const status = Object.keys(op.responses ?? {})[0]}
        {@const response = body(op.responses?.[status]?.content, 'writeOnly')}
        {@const request = body(op.requestBody?.content, 'readOnly')}
        <details>
          <summary>
            <span class="method {method}">{method.toUpperCase()}</span>
            <span class="mono">{path}</span>
            {#if op.summary}<span class="muted">{op.summary}</span>{/if}
          </summary>
          <div class="op">
            {#if op.description}<p class="muted">{@render text(op.description)}</p>{/if}
            {#if op.parameters?.length}
              <table>
                <tbody>
                  {#each op.parameters as p}
                    <tr>
                      <td class="mono">{p.name}{p.required ? '' : '?'}</td>
                      <td class="mono muted">{shape(p.schema)}</td>
                      <td class="muted">{@render text(p.description)}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            {/if}
            {#if request}<Json value={request} />{/if}
            <div class="label">→ {status}</div>
            {#if response}<Json value={response} />{/if}
          </div>
        </details>
      {/each}
    </div>
  </section>
{:else}
  <section class="card docs skel" role="status" aria-label="Loading docs">
    <div class="card-body"><span class="bone sk-w" style:--w="55%"></span></div>
    {#each [38, 52, 30, 46, 40, 34] as w}
      <div class="sk-op"><span class="bone sk-method"></span><span class="bone sk-w" style:--w={`${w}%`}></span></div>
    {/each}
  </section>
{/if}

<style>
  .docs { display: flex; flex-direction: column; min-height: 0; }
  .intro { margin: 0; }
  /* The card below is its own stacking context; keep the open picker on top of it. */
  .page-head { position: relative; z-index: 3; }
  .sk-w { width: var(--w); }
  .sk-op { display: flex; align-items: center; gap: 12px; padding: 13px 18px; border-top: 1px solid var(--border); }
  .sk-method { width: 60px; height: 18px; }
  details { border-top: 1px solid var(--border); }
  summary { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 12px; padding: 11px 18px; cursor: pointer; list-style: none; transition: background 0.2s; }
  details[open] summary { background: var(--surface-2); }
  details[open] .op { animation: rise 0.4s var(--ease) both; }
  summary::-webkit-details-marker { display: none; }
  summary:hover { background: var(--accent-soft); }
  .method { flex-shrink: 0; width: 60px; padding: 1px 0; border-radius: 6px; text-align: center; font: 500 11px/1.6 var(--mono); color: var(--muted); background: var(--surface-2); }
  .method.get { color: var(--accent); background: var(--accent-soft); }
  .method.post { color: var(--signal-text); background: var(--signal-soft); }
  .method.put, .method.patch { color: var(--signal-text); }
  .method.delete { color: var(--danger); background: var(--danger-soft); }
  .op { padding: 12px 18px 18px; display: grid; gap: 8px; }
  .op p { margin: 0; }
  .label { margin: 4px 0 0; }
  /* Name and type stay on one line; the description wraps. */
  table { border-collapse: collapse; font-size: 13px; }
  td { padding: 4px 16px 4px 0; vertical-align: top; }
  td:not(:last-child) { white-space: nowrap; }
  code { font-family: var(--mono); color: var(--text); }
</style>
