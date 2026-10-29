<script lang="ts">
  import { api, type Subscription } from '#lib/api';

  // Turning a plugin on shares extracted data with its creator, so it asks first, inline.
  // Turning one off takes effect right away.
  let { sub, onupdate }: { sub: Subscription; onupdate: (updated: Subscription) => void } = $props();

  // The consent prompt opens for a decision, so its confirm button takes focus.
  const focusOnMount = (node: HTMLElement) => node.focus();

  let box: HTMLInputElement;
  let consenting = $state(false);
  let busy = $state(false);
  let error = $state('');

  // Sends the state the user chose, not a flip, so a stale tab cannot turn sharing on or off by mistake.
  const setActive = async (active: boolean) => {
    consenting = false;
    busy = true;
    error = '';
    try {
      onupdate(await api<Subscription>(`/api/subscriptions/${sub.id}/set_active/`, { method: 'POST', body: JSON.stringify({ active }) }));
    } catch (err) {
      box.checked = sub.active;
      error = err instanceof Error ? err.message : 'Something went wrong.';
    }
    busy = false;
  };

  const change = () => {
    if (box.checked) {
      box.checked = false;
      consenting = true;
    } else {
      setActive(false);
    }
  };
</script>

<li class="row sub subscription-row" aria-busy={busy}>
  <div class="grow">
    <span class="row-kicker">SIGNAL SOURCE</span>
    <div class="title mono">{sub.plugin_name}</div>
    <div class="muted">{sub.plugin_desc || 'No description'}</div>
  </div>

  <label class="switch">
    <input bind:this={box} type="checkbox" role="switch" checked={sub.active} disabled={busy} onchange={change} />
    <span class="track" aria-hidden="true"></span>
    <span class="switch-text">{sub.active ? 'On' : 'Off'}</span>
  </label>

  <div class="sub-status">
    {#if consenting}
      <div class="consent">
        <p>Enabling {sub.plugin_name} shares what Laya extracts from your emails with its creator. Raw emails are never shared.</p>
        <div class="actions">
          <button type="button" class="btn btn-sm" onclick={() => (consenting = false)}>Cancel</button>
          <button type="button" class="btn btn-primary btn-sm" use:focusOnMount onclick={() => setActive(true)}>Enable</button>
        </div>
      </div>
    {:else if error}
      <div class="alert alert-danger">{error}</div>
    {/if}
  </div>
</li>
