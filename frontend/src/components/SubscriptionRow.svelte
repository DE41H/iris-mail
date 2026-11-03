<script lang="ts">
  import { slide } from 'svelte/transition';
  import { api, message, type Subscription } from '../lib/api';

  let { sub = $bindable() }: { sub: Subscription } = $props();

  let asking = $state(false);
  let busy = $state(false);
  let error = $state('');

  // Sends the state the user chose, not a flip, so a stale tab cannot change sharing by mistake.
  async function set(active: boolean) {
    asking = false;
    busy = true;
    error = '';
    try {
      sub = await api<Subscription>(`/api/subscriptions/${sub.id}/set_active/`, { method: 'POST', body: JSON.stringify({ active }) });
    } catch (err) {
      error = message(err);
    } finally {
      busy = false;
    }
  }

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
    <span class="state">{sub.active ? 'on' : 'off'}</span>
  </label>

  {#if asking}
    <div class="consent" transition:slide={{ duration: 220 }}>
      <p><strong>{sub.plugin_name}</strong>'s creator will receive answers from your new emails. Never the emails.</p>
      <div class="actions">
        <button type="button" class="btn btn-sm" onclick={() => (asking = false)}>cancel</button>
        <!-- svelte-ignore a11y_autofocus -->
        <button type="button" class="btn btn-sm btn-primary" autofocus onclick={() => set(true)}>turn on</button>
      </div>
    </div>
  {/if}
  {#if error}<div class="alert alert-danger wide" role="alert">{error}</div>{/if}
</li>

<style>
  .row { display: flex; flex-wrap: wrap; align-items: center; gap: 16px; padding: 16px 18px; border-top: 1px solid var(--border); transition: background 0.3s; }
  .row.on { background: linear-gradient(90deg, var(--green-soft), transparent 60%); }
  .info { flex: 1; min-width: 0; }
  .name { font: 600 14px var(--mono); }
  .switch { display: inline-flex; align-items: center; gap: 10px; cursor: pointer; position: relative; }
  .switch input { position: absolute; opacity: 0; width: 100%; height: 100%; margin: 0; cursor: pointer; }
  .track { width: 38px; height: 22px; border-radius: 999px; background: var(--border-strong); position: relative; transition: background 0.25s, box-shadow 0.25s; }
  .track::after {
    content: '';
    position: absolute;
    top: 3px;
    left: 3px;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: var(--text);
    transition: transform 0.3s var(--ease);
  }
  input:checked + .track { background: var(--green); box-shadow: 0 0 14px var(--green-glow); }
  input:checked + .track::after { transform: translateX(16px); background: var(--bg); }
  input:focus-visible + .track { outline: 2px solid var(--green); outline-offset: 2px; }
  input:disabled + .track { opacity: 0.5; }
  .state { width: 22px; font: 12px var(--mono); color: var(--muted); }
  .on .state { color: var(--green); }
  .consent, .wide { flex-basis: 100%; }
  .consent { display: grid; gap: 10px; padding: 12px 14px; border: 1px solid rgba(242, 193, 78, 0.35); border-radius: 6px; background: rgba(242, 193, 78, 0.06); font-size: 13px; }
</style>
