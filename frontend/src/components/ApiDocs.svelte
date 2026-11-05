<script lang="ts">
  import { onMount } from 'svelte';
  import Json from './Json.svelte';

  type Schema = Record<string, any>;
  interface Op { method: string; path: string; tag: string; op: Schema }

  let spec = $state<Schema | null>(null);
  let error = $state('');

  // Plain fetch: the docs are public, and api() would redirect a signed-out visitor to sign in.
  onMount(() =>
    fetch('/api/schema/?format=json')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`Schema request failed (${r.status}).`))))
      .then((s) => (spec = s))
      .catch((err) => (error = err.message)),
  );

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
    return [s.type, s.format && `(${s.format})`, s.nullable && '| null'].filter(Boolean).join(' ');
  };

  const body = (content: Schema | undefined, skip: string) => {
    const s = content?.['application/json']?.schema;
    return s && shape(s, skip);
  };

  const ops = $derived<Op[]>(
    spec
      ? Object.entries<Schema>(spec.paths).flatMap(([path, methods]) =>
          Object.entries<Schema>(methods).map(([method, op]) => ({ method, path, op, tag: op.tags?.[0] ?? 'other' })),
        )
      : [],
  );
  // Spec tag order and descriptions first, then any untagged leftovers.
  const tags = $derived([...new Set([...(spec?.tags ?? []).map((t: Schema) => t.name), ...ops.map((o) => o.tag)])].filter((t) => ops.some((o) => o.tag === t)));
  const tagDesc = (name: string) => spec?.tags?.find((t: Schema) => t.name === name)?.description;
  const auth = (op: Schema) =>
    (op.security ?? []).flatMap((s: Schema) => Object.keys(s)).map((k: string) => (k === 'PluginKey' ? 'API key' : 'session'));
</script>

{#if error}
  <div class="alert alert-danger" role="alert">{error}</div>
{:else if spec}
  <section class="card reveal docs">
    <div class="card-head"><span>{spec.info.title} {spec.info.version}</span><span>{ops.length} endpoints</span></div>
    <div class="grow scroll">
      <p class="card-body muted intro">Plugin endpoints take <code>Authorization: Bearer &lt;api key&gt;</code>.</p>
      {#each tags as tag}
        <h2>{tag}</h2>
        {#if tagDesc(tag)}<p class="muted tag-desc">{tagDesc(tag)}</p>{/if}
        {#each ops.filter((o) => o.tag === tag) as { method, path, op } (method + path)}
          {@const status = Object.keys(op.responses ?? {})[0]}
          {@const response = body(op.responses?.[status]?.content, 'writeOnly')}
          {@const request = body(op.requestBody?.content, 'readOnly')}
          <details>
            <summary>
              <span class="method {method}">{method.toUpperCase()}</span>
              <span class="mono">{path}</span>
              {#if op.summary}<span class="muted">{op.summary}</span>{/if}
              <span class="via">
                {#each auth(op) as a}<span class="chip" class:on={a === 'API key'}>{a}</span>{/each}
              </span>
            </summary>
            <div class="op">
              {#if op.description}<p class="muted">{op.description}</p>{/if}
              {#if op.parameters?.length}
                <div class="label">Parameters</div>
                <table>
                  <tbody>
                    {#each op.parameters as p}
                      <tr>
                        <td class="mono">{p.name}{p.required ? '' : '?'}</td>
                        <td class="muted">{p.in}</td>
                        <td class="mono muted">{shape(p.schema)}</td>
                        <td class="muted">{p.description ?? ''}</td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              {/if}
              {#if request}
                <div class="label">Request body</div>
                <Json value={request} />
              {/if}
              <div class="label">Response {status}</div>
              {#if response}<Json value={response} />{:else}<p class="muted">No content</p>{/if}
            </div>
          </details>
        {/each}
      {/each}
    </div>
  </section>
{:else}
  <div class="card skeleton docs-skel"></div>
{/if}

<style>
  .docs { display: flex; flex-direction: column; min-height: 0; }
  .intro { margin: 0; }
  h2 { padding: 20px 18px 6px; margin: 0; text-transform: capitalize; }
  .docs-skel { flex: 1; min-height: 300px; }
  .tag-desc { margin: 0; padding: 0 16px 10px; font-size: 13px; }
  details { border-top: 1px solid var(--border); }
  summary { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 12px; padding: 11px 18px; cursor: pointer; list-style: none; transition: background 0.2s; }
  details[open] summary { background: var(--surface-2); }
  details[open] .op { animation: rise 0.4s var(--ease) both; }
  summary::-webkit-details-marker { display: none; }
  summary:hover { background: var(--accent-soft); }
  .via { margin-left: auto; display: flex; gap: 6px; }
  .method { flex-shrink: 0; width: 60px; padding: 1px 0; border-radius: 6px; text-align: center; font: 500 11px/1.6 var(--mono); color: var(--muted); background: var(--surface-2); }
  .method.get { color: var(--accent); background: var(--accent-soft); }
  .method.post { color: var(--signal-text); background: var(--signal-soft); }
  .method.put, .method.patch { color: var(--signal-text); }
  .method.delete { color: var(--danger); background: var(--danger-soft); }
  .op { padding: 12px 18px 18px; display: grid; gap: 8px; }
  .op p { margin: 0; }
  .label { margin: 8px 0 0; }
  /* Scrolls sideways on its own when a phone is too narrow for the columns. */
  table { display: block; overflow-x: auto; border-collapse: collapse; font-size: 13px; }
  td { padding: 4px 16px 4px 0; vertical-align: top; }
  td:not(:last-child) { white-space: nowrap; }
  td:last-child { min-width: 180px; }
  code { font-family: var(--mono); color: var(--text); }
</style>
