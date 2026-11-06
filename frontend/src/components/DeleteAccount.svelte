<script lang="ts">
  import { api, message } from '../lib/api';
  import ConfirmButton from './ConfirmButton.svelte';

  let error = $state('');

  // Deletes the account, its Google access, subscriptions, results and own plugins, then signs out.
  async function leave() {
    error = '';
    try {
      await api('/api/v1/me/', { method: 'DELETE' });
      location.href = '/';
    } catch (err) {
      error = message(err);
    }
  }
</script>

<div class="leave">
  <ConfirmButton label="Delete account" confirm="Delete everything?" danger onconfirm={leave} />
  {#if error}<div class="alert alert-danger" role="alert">{error}</div>{/if}
</div>

<style>
  .leave { display: grid; gap: 8px; justify-items: end; }
</style>
