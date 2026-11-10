<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { api, hue, message } from '../lib/api';
  import { fromSchema, KINDS, type Field } from '../lib/schema';
  import { loadSession, session } from '../lib/session';
  import Iris from './Iris.svelte';

  interface Asking {
    id: string;
    name: string;
    desc: string;
    developer: string;
    schema: unknown;
    rules: Record<string, string>;
  }

  // The code arrives in the hash so it stays out of server logs. It is kept for this tab so it survives Google sign-in.
  const KEY = 'iris-connect';
  const CODE = /^[\w-]{43}$/;
  const keep = (code: string | null) => {
    try { code ? sessionStorage.setItem(KEY, code) : sessionStorage.removeItem(KEY); } catch {}
  };
  const kept = () => {
    try { return sessionStorage.getItem(KEY); } catch { return null; }
  };

  const returned = new URLSearchParams(location.search).get('status'); // back here when the plugin has no redirect
  let code = $state<string | null>(null);
  let plugin = $state<Asking | null>(null);
  let fields = $state<Field[]>([]);
  let error = $state('');
  let busy = $state<'accept' | 'deny' | null>(null);
  let done = $state<'accepted' | 'denied' | null>(returned === 'accepted' || returned === 'denied' ? returned : null);

  const rules = $derived(Object.keys(plugin?.rules ?? {}));
  const kind = (f: Field) => KINDS.find((k) => k.kind === f.kind);
  const still = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

  onMount(async () => {
    const fresh = location.hash.slice(1);
    if (CODE.test(fresh)) {
      keep(fresh);
      history.replaceState(null, '', location.pathname + location.search); // the code is single use; keep it off screen and out of history
    }
    if (done) return keep(null);
    code = kept();
    if (!code || !CODE.test(code)) return (error = 'This link is missing its code.');
    await loadSession();
    if (get(session) === null) return (location.href = '/accounts/login/?next=/connect/'); // the code stays kept for after sign-in
    api<Asking>(`/api/v1/connect/${code}/`)
      .then((p) => {
        plugin = p;
        const parsed = fromSchema(p.schema);
        fields = 'fields' in parsed ? parsed.fields : [];
      })
      .catch((err) => {
        keep(null);
        error = message(err);
      });
  });

  async function decide(choice: 'accept' | 'deny') {
    if (busy || !code) return;
    busy = choice;
    error = '';
    try {
      const { redirect } = await api<{ redirect: string | null }>(`/api/v1/connect/${code}/${choice}/`, { method: 'POST' });
      keep(null);
      done = choice === 'accept' ? 'accepted' : 'denied';
      // The iris opens before the app takes over, so the choice is seen to land.
      if (redirect) setTimeout(() => location.replace(redirect), still() ? 0 : 900);
    } catch (err) {
      error = message(err);
      busy = null;
    }
  }
</script>

{#if plugin || done}
  <div class="consent" style:--h={plugin ? hue(plugin.id) : undefined}>
    <div class="mark reveal"><Iris open={done === 'accepted'} /></div>

    {#if done && plugin}
      <p class="sr-only" role="status">{done === 'accepted' ? 'Allowed. Taking you back.' : 'Denied. Taking you back.'}</p>
    {:else if done}
      <div class="head reveal d1" role="status">
        <h1>{done === 'accepted' ? 'Connected' : 'Not connected'}</h1>
        <p class="muted">
          {#if done === 'accepted'}
            The app now gets answers from new mail.
            Turn it off any time in <a href="/subscriptions">Inbox</a>.
          {:else}
            Nothing was shared.
          {/if}
        </p>
        <p class="muted small">You can close this tab.</p>
      </div>
    {:else if plugin}
      <h1 class="head reveal d1">Allow access to your inbox?</h1>

      {#if error}<div class="alert alert-danger" role="alert">{error}</div>{/if}
      {#if $session && !$session.google}
        <div class="alert alert-danger" role="alert">Iris can't read your Gmail right now. <a href="/accounts/google/login/?action=reauthenticate&next=/connect/">Reconnect Google</a></div>
      {/if}

      <section class="card reveal d2" aria-labelledby="who">
        <div class="who">
          <h2 id="who">{plugin.name}</h2>
          <p class="muted small">By {plugin.developer}</p>
          {#if plugin.desc}<p class="desc" title={plugin.desc}>{plugin.desc}</p>{/if}
        </div>
        <div class="card-body stack">
          {#if fields.length}
            <div>
              <h3>For each new email, it asks</h3>
              <ul class="asks">
                {#each fields as f (f.name)}
                  <li>
                    <span class="q">{f.question || f.name}</span>
                    {#if f.kind === 'choice' || f.kind === 'multi'}
                      <span class="opts">{#each f.options as o}<span class="chip">{o}</span>{/each}</span>
                    {:else}
                      <span class="kind muted"><span aria-hidden="true">{kind(f)?.icon}</span> {kind(f)?.label}</span>
                    {/if}
                  </li>
                {/each}
              </ul>
            </div>
          {/if}
          {#if rules.length}
            <div>
              <h3>It also copies short bits of text matching</h3>
              <p class="opts">{#each rules as r}<span class="chip rule">{r}</span>{/each}</p>
            </div>
          {/if}
        </div>
      </section>

      <div class="choose reveal d3">
        <button type="button" class="btn" disabled={!!busy} onclick={() => decide('deny')}>{busy === 'deny' ? 'Denying…' : 'Deny'}</button>
        <button type="button" class="btn btn-primary" disabled={!!busy || ($session ? !$session.google : false)} onclick={() => decide('accept')}>
          {busy === 'accept' ? 'Allowing…' : 'Allow'}
        </button>
      </div>
    {/if}
  </div>
{:else if error}
  <div class="consent">
    <div class="mark reveal"><Iris /></div>
    <div class="head reveal d1">
      <h1>Can't connect</h1>
      <p class="muted">{error} Go back to the app for a new link.</p>
    </div>
  </div>
{:else}
  <div class="consent skel" role="status" aria-label="Loading">
    <span class="bone sk-mark"></span>
    <div class="head"><span class="bone sk-title"></span></div>
    <div class="card">
      <div class="who"><span class="bone sk-name"></span><span class="bone sk-line"></span></div>
      <div class="card-body stack">
        {#each { length: 3 } as _}<div class="sk-row"><span class="bone sk-q"></span><span class="bone sk-kind"></span></div>{/each}
      </div>
    </div>
    <div class="choose"><span class="bone sk-btn"></span><span class="bone sk-btn"></span></div>
  </div>
{/if}

<style>
  .consent { display: grid; gap: 22px; width: 100%; max-width: 560px; margin: 6vh auto 0; }
  .mark { justify-self: center; }
  .mark :global(.iris) { width: 72px; height: 72px; }
  .head { display: grid; gap: 8px; text-align: center; }
  .head p { max-width: 52ch; margin-inline: auto; }
  .small { font-size: 13px; }
  h3 { font-size: 14px; font-weight: 600; margin: 0 0 10px; letter-spacing: -0.01em; }
  .who { display: grid; gap: 2px; padding: 16px 18px; border-bottom: 1px solid var(--border); }
  .who h2 { font-size: 17px; }
  /* Long descriptions stop at two lines; the full text is in the tooltip. */
  .desc { margin-top: 6px; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; line-clamp: 2; overflow: hidden; overflow-wrap: anywhere; }
  .asks { list-style: none; margin: 0; padding: 0; display: grid; }
  .asks li { display: flex; align-items: baseline; justify-content: space-between; gap: 6px 16px; flex-wrap: wrap; padding: 10px 0; border-top: 1px solid var(--border); }
  .asks li:first-child { border-top: 0; padding-top: 0; }
  .q { flex: 1 1 220px; }
  .kind { font-size: 13px; white-space: nowrap; }
  .opts { display: flex; flex-wrap: wrap; gap: 4px; }
  .rule { color: var(--signal-text); background: var(--signal-soft); border-color: transparent; }
  .choose { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .choose .btn { padding-block: 11px; }
  @media (max-width: 480px) {
    .consent { margin-top: 2vh; }
    .choose { grid-template-columns: 1fr; }
    .choose .btn-primary { order: -1; }
  }
  .sk-mark { justify-self: center; width: 72px; height: 72px; border-radius: 50%; }
  .skel .head { justify-items: center; }
  .sk-title { width: 60%; height: 22px; }
  .sk-name { width: 35%; height: 15px; margin-bottom: 6px; }
  .sk-line { width: 25%; }
  .sk-row { display: flex; justify-content: space-between; gap: 16px; }
  .sk-q { width: 55%; }
  .sk-kind { width: 18%; }
  .sk-btn { height: 44px; border-radius: var(--radius-btn); corner-shape: squircle; }
</style>
