<script lang="ts">
  import { slide } from 'svelte/transition';
  import { api, message, type Subscription } from '../lib/api';
  import ConfirmButton from './ConfirmButton.svelte';

  let { sub = $bindable(), onremove }: { sub: Subscription; onremove: () => void } = $props();

  let asking = $state(false);
  let busy = $state(false);
  let error = $state('');

  async function run(fn: () => Promise<unknown>) {
    if (busy) return;
    busy = true;
    error = '';
    try {
      await fn();
    } catch (err) {
      error = message(err);
    } finally {
      busy = false;
    }
  }

  // Sends the state the user chose, not a flip, so a stale tab cannot change sharing by mistake.
  function set(active: boolean) {
    asking = false;
    return run(async () => {
      sub = await api<Subscription>(`/api/v1/subscriptions/${sub.id}/set_active/`, { method: 'POST', body: JSON.stringify({ active }) });
    });
  }

  const remove = () => run(() => api(`/api/v1/subscriptions/${sub.id}/`, { method: 'DELETE' }).then(onremove));

  // Turning a plugin on shares extracted data with its creator, so it asks first, inline.
  function toggle(e: Event) {
    const box = e.currentTarget as HTMLInputElement;
    box.checked = sub.active;
    if (sub.active) set(false);
    else asking = true;
  }
</script>

<li class="row" class:on={sub.active} aria-busy={busy}>
  <div class="info">
    <div class="name">{sub.plugin_name}</div>
    {#if sub.plugin_desc}<p class="muted">{sub.plugin_desc}</p>{/if}
  </div>
  <label class="switch">
    <input type="checkbox" role="switch" checked={sub.active} disabled={busy || asking} onchange={toggle} aria-label={`Share ${sub.plugin_name} results`} />
    <span class="track" aria-hidden="true"></span>
    <span class="state">{sub.active ? 'On' : 'Off'}</span>
  </label>
  <ConfirmButton label="Remove" confirm="Remove it?" danger onconfirm={remove} />

  {#if asking}
    <div class="consent" transition:slide={{ duration: 220 }}>
      <p><strong>{sub.plugin_name}</strong>'s creator will receive answers and short matched snippets from your new emails. Never whole emails.</p>
      <div class="actions">
        <button type="button" class="btn btn-sm" onclick={() => (asking = false)}>Cancel</button>
        <!-- svelte-ignore a11y_autofocus -->
        <button type="button" class="btn btn-sm btn-primary" autofocus onclick={() => set(true)}>Turn on</button>
      </div>
    </div>
  {/if}
  {#if error}<div class="alert alert-danger wide" role="alert">{error}</div>{/if}
</li>

<style>
  .row { position: relative; display: flex; flex-wrap: wrap; align-items: center; gap: 16px; padding: 16px 20px; border-top: 1px solid var(--border); transition: background 0.4s; }
  .row::before { content: ''; position: absolute; left: 0; top: 14px; bottom: 14px; width: 3px; border-radius: 0 3px 3px 0; background: var(--accent); scale: 1 0; transition: scale 0.45s var(--spring); }
  .row.on::before { scale: 1 1; }
  .row.on { background: color-mix(in oklab, var(--accent) 4%, transparent); }
  .info { flex: 1 1 220px; min-width: 0; }
  .name { font-size: 16px; font-weight: 640; font-stretch: 108%; }
  .switch { margin-right: auto; display: inline-flex; align-items: center; gap: 10px; cursor: pointer; position: relative; }
  .switch input { position: absolute; opacity: 0; width: 100%; height: 100%; margin: 0; cursor: pointer; }
  .track { width: 44px; height: 26px; border-radius: 999px; background: var(--border-strong); position: relative; transition: background 0.3s; }
  .track::after {
    content: '';
    position: absolute;
    top: 3px;
    left: 3px;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: var(--surface);
    box-shadow: 0 1px 3px rgb(0 0 0 / 0.25);
    transition: translate 0.45s var(--spring), width 0.2s var(--ease);
  }
  /* The thumb stretches while pressed, like a physical switch. */
  .switch:active .track::after { width: 26px; }
  input:checked + .track { background: var(--accent); }
  input:checked + .track::after { translate: 18px 0; }
  .switch:active input:checked + .track::after { translate: 12px 0; }
  input:focus-visible + .track { outline: 2px solid var(--accent); outline-offset: 2px; }
  input:disabled + .track { opacity: 0.5; }
  .state { width: 24px; font-size: 13px; font-weight: 560; color: var(--muted); }
  .on .state { color: var(--accent); }
  .consent, .wide { flex-basis: 100%; }
  /* Accent panel with a saffron edge: saffron washes turn brown over the dark indigo. */
  .consent { display: grid; gap: 10px; padding: 14px 16px 14px 18px; border: 1px solid var(--border); border-left: 3px solid var(--signal); border-radius: var(--radius-sm); background: var(--accent-soft); font-size: 14px; animation: rise 0.35s var(--ease) both; }
</style>
