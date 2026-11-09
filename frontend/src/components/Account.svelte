<script lang="ts">
  import { onMount } from 'svelte';
  import { api, message } from '../lib/api';
  import { loadSession, session } from '../lib/session';
  import DeleteAccount from './DeleteAccount.svelte';

  type Day = { date: string; used: number };
  const EMPTY_DAYS = 30; // span of the empty graph before any usage exists

  let usage = $state<{ today: string; days: Day[] } | null>(null);
  let error = $state('');
  let broken = $state(false);

  onMount(() => {
    loadSession();
    api<NonNullable<typeof usage>>('/api/v1/usage/').then((u) => (usage = u)).catch((err) => (error = message(err)));
  });

  // Dates are plain YYYY-MM-DD from the server; UTC keeps the math free of DST shifts.
  const ms = (iso: string) => Date.parse(`${iso}T00:00:00Z`);
  const fmt = (iso: string, opts: Intl.DateTimeFormatOptions) => new Date(ms(iso)).toLocaleDateString(undefined, { ...opts, timeZone: 'UTC' });
  const num = (n: number) => n.toLocaleString();

  // Every day from the oldest stored one (days are newest first) to today, gaps filled with 0.
  const series = $derived.by((): Day[] => {
    if (!usage) return [];
    const by = new Map(usage.days.map((d) => [d.date, d.used]));
    const end = ms(usage.today);
    const start = usage.days.length ? Math.min(ms(usage.days.at(-1)!.date), end) : end - (EMPTY_DAYS - 1) * 864e5;
    const out: Day[] = [];
    for (let t = start; t <= end; t += 864e5) {
      const date = new Date(t).toISOString().slice(0, 10);
      out.push({ date, used: by.get(date) ?? 0 });
    }
    return out;
  });

  const today = $derived(usage?.days.find((d) => d.date === usage!.today)?.used ?? 0);
  const quota = $derived($session?.quota ?? 0);
  const share = $derived(quota ? Math.min(today / quota, 1) : 0);
  const upgradable = $derived(!!$session && $session.tiers.some((t) => t.quota > $session!.quota)); // a higher tier exists
  const level = $derived(share >= 1 ? 'full' : share >= 0.8 ? 'high' : '');

  // The y axis tops out at a round number: 1, 2 or 5 times a power of ten.
  const top = $derived.by(() => {
    const peak = Math.max(10, ...series.map((d) => d.used));
    const p = 10 ** Math.floor(Math.log10(peak));
    return [1, 2, 5, 10].map((m) => m * p).find((v) => v >= peak)!;
  });
  const step = $derived(Math.ceil(series.length / 6)); // a date label every `step` days
  const day = (iso: string) => fmt(iso, { month: 'short', day: 'numeric' });
</script>

{#if error}
  <div class="alert alert-danger" role="alert">{error}</div>
{:else if $session && usage}
  <div class="me">
    <header class="who reveal">
      {#if $session.avatar && !broken}
        <img class="avatar" src={$session.avatar} alt="" referrerpolicy="no-referrer" onerror={() => (broken = true)} />
      {:else}
        <span class="avatar">{$session.email[0].toUpperCase()}</span>
      {/if}
      <div class="id">
        <div class="name"><h1>{$session.username}</h1><span class="chip on">{$session.tier} tier</span></div>
        <p class="muted">{$session.email}</p>
      </div>
    </header>

    <section class="card today reveal d1" class:high={level === 'high'} class:full={level === 'full'}>
      <div class="row">
        <h2>Today</h2>
        <!-- Billing isn't wired up yet, so this does nothing for now. -->
        {#if upgradable}<button type="button" class="btn btn-sm btn-primary">Upgrade</button>{/if}
      </div>
      <p class="figure"><b>{num(today)}</b> <span>of {num(quota)} questions answered</span></p>
      <div class="meter" role="meter" aria-label="Today's quota used" aria-valuemin={0} aria-valuemax={quota} aria-valuenow={Math.min(today, quota)}>
        {#if share > 0}<span class="fill" style:--p={share}></span>{/if}
      </div>
      {#if level === 'full'}<p class="note">Limit reached. New mail isn't answered until tomorrow.</p>{/if}
    </section>

    <section class="card reveal d2">
      <div class="card-head"><span>Questions per day</span></div>
      <div class="plot" style:--n={series.length} aria-hidden="true">
        <div class="y"><span>{num(top)}</span><span>{num(top / 2)}</span><span>0</span></div>
        <div class="bars">
          {#each series as d}<span class="bar" style:--h={d.used / top}></span>{/each}
        </div>
        <div class="x">{#each series as d, i}{#if i % step === 0}<span style:grid-column="{i + 1} / span {step}">{day(d.date)}</span>{/if}{/each}</div>
      </div>
      <!-- Tables ignore overflow, so the wrapper does the hiding. -->
      <div class="sr-only">
        <table>
          <caption>Questions answered per day</caption>
          <thead><tr><th>Date</th><th>Questions</th></tr></thead>
          <tbody>{#each series as d}<tr><td>{d.date}</td><td>{d.used}</td></tr>{/each}</tbody>
        </table>
      </div>
    </section>

    <section class="card reveal d3">
      <div class="card-body leave">
        <a class="btn" href="/accounts/logout/">Sign out</a>
        <DeleteAccount />
      </div>
    </section>
  </div>
{:else}
  <div class="me skel" role="status" aria-label="Loading your account">
    <header class="who">
      <span class="bone sk-avatar"></span>
      <div class="id"><span class="bone sk-name"></span><span class="bone sk-mail"></span></div>
    </header>
    <section class="card today">
      <span class="bone sk-h2"></span>
      <span class="bone sk-figure"></span>
      <span class="bone meter"></span>
    </section>
    <section class="card">
      <div class="card-head"><span class="bone sk-w"></span></div>
      <div class="plot sk-bars">{#each { length: 30 } as _, i}<span class="bone" style:--h={0.25 + 0.6 * Math.abs(Math.sin(i * 0.7))}></span>{/each}</div>
    </section>
  </div>
{/if}

<style>
  .me { display: grid; gap: 16px; }

  .who { display: flex; align-items: center; gap: 16px; margin-bottom: 8px; }
  .who .avatar {
    flex-shrink: 0;
    width: 64px;
    height: 64px;
    border-radius: 30%;
    object-fit: cover;
    display: grid;
    place-items: center;
    background: var(--accent-soft);
    color: var(--accent);
    font-size: 26px;
    font-weight: 640;
  }
  @supports (corner-shape: squircle) {
    .who .avatar, .sk-avatar { border-radius: 50%; corner-shape: squircle; }
  }
  .id { flex: 1; min-width: 0; display: grid; gap: 4px; }
  .id h1 { overflow-wrap: anywhere; }
  .id p { margin: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  .today { display: grid; gap: 12px; padding: 20px 22px 22px; }
  .today h2 { margin: 0; font-size: 15px; }
  .row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
  .name { display: flex; align-items: center; flex-wrap: wrap; gap: 6px 12px; }
  .figure { margin: 0; display: flex; align-items: baseline; flex-wrap: wrap; gap: 4px 10px; color: var(--muted); font-size: 17px; }
  .figure b { color: var(--text); font-size: 40px; font-weight: 700; font-stretch: 115%; line-height: 1; font-variant-numeric: tabular-nums; letter-spacing: -0.01em; }
  .meter { position: relative; height: 14px; border-radius: 999px; background: var(--surface-2); box-shadow: inset 0 0 0 1px var(--border); overflow: hidden; }
  .fill {
    position: absolute;
    inset: 0 auto 0 0;
    width: max(calc(var(--p) * 100%), 14px);
    border-radius: inherit;
    background: var(--accent);
    animation: fill 1s 0.25s var(--ease) both;
  }
  .high .fill { background: var(--signal); }
  .full .fill { background: var(--danger); }
  @keyframes fill { from { clip-path: inset(0 100% 0 0 round 999px); } to { clip-path: inset(0 0 0 0 round 999px); } }
  .note { margin: 0; font-size: 13px; color: var(--danger); }

  /* CSS bars instead of a chart library: theme colours apply as is, nothing extra loads. */
  .plot { display: grid; grid-template-columns: auto minmax(0, 1fr); grid-template-rows: 200px auto; column-gap: 10px; padding: 18px 18px 12px; font-size: 11.5px; color: var(--faint); }
  .y { display: flex; flex-direction: column; justify-content: space-between; align-items: flex-end; margin: -0.6em 0; }
  .bars, .x { display: grid; grid-template-columns: repeat(var(--n), minmax(0, 1fr)); }
  .bars {
    border-bottom: 1px solid var(--border);
    background: linear-gradient(var(--border) 0 0) top / 100% 1px no-repeat, linear-gradient(var(--border) 0 0) center / 100% 1px no-repeat;
  }
  .bar { display: flex; align-items: flex-end; justify-content: center; }
  .bar::before {
    content: '';
    width: 72%;
    max-width: 28px;
    height: calc(var(--h) * 100%);
    border-radius: 4px 4px 0 0;
    background: color-mix(in oklab, var(--accent) 70%, transparent);
    transform-origin: bottom;
    transition: background 0.15s;
    animation: grow 0.6s 0.2s var(--ease) both;
  }
  .bar:hover::before { background: var(--accent); }
  @keyframes grow { from { scale: 1 0; } }
  .x { grid-column: 2; padding-top: 6px; white-space: nowrap; }

  .leave { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }

  .sk-avatar { flex-shrink: 0; width: 64px; height: 64px; border-radius: 30%; }
  .sk-name { width: 180px; height: 26px; border-radius: 8px; }
  .sk-mail { width: 240px; max-width: 100%; }
  .sk-h2 { width: 60px; height: 14px; }
  .sk-figure { width: 220px; height: 34px; border-radius: 8px; }
  .sk-w { width: 90px; }
  .sk-bars { display: flex; align-items: flex-end; gap: 1.5%; height: 253px; }
  .sk-bars .bone { flex: 1; height: calc(var(--h) * 100%); border-radius: 4px 4px 0 0; }

  @media (max-width: 640px) {
    .who .avatar, .sk-avatar { width: 52px; height: 52px; font-size: 22px; }
    .figure b { font-size: 32px; }
    .plot { padding: 14px 10px 8px; grid-template-rows: 180px auto; }
    .sk-bars { height: 225px; }
  }
</style>
