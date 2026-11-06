<script lang="ts">
  import type { Chart } from 'chart.js';
  import { onMount } from 'svelte';
  import { api, message } from '../lib/api';
  import { loadSession, session } from '../lib/session';
  import DeleteAccount from './DeleteAccount.svelte';

  // Chart.js is most of this page's code, so it loads beside the API calls instead of before the first paint.
  const charts = import('chart.js').then(({ BarController, BarElement, CategoryScale, Chart, LinearScale, Tooltip }) => {
    Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip);
    return Chart;
  });

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
  const top = $derived(!!$session && $session.tiers.some((t) => t.quota > $session!.quota)); // a higher tier exists
  const level = $derived(share >= 1 ? 'full' : share >= 0.8 ? 'high' : '');

  // Chart.js draws on canvas, so it gets the theme as resolved colours and redraws when the scheme flips.
  function graph(canvas: HTMLCanvasElement, days: Day[]) {
    const css = (name: string) => getComputedStyle(canvas).getPropertyValue(name).trim();
    const scheme = matchMedia('(prefers-color-scheme: dark)');
    let chart: Chart<'bar'> | undefined;
    let gone = false;

    const draw = (days: Day[]) => charts.then((C) => !gone && paint(C, days));

    function paint(C: typeof Chart, days: Day[]) {
      chart?.destroy();
      const [accent, faint, border, text, surface] = ['--accent', '--faint', '--border', '--text', '--surface'].map(css);
      const font = { family: css('--font'), size: 11.5 };
      chart = new C(canvas, {
        type: 'bar',
        data: {
          labels: days.map((d) => d.date),
          datasets: [{ data: days.map((d) => d.used), backgroundColor: `${accent}b3`, hoverBackgroundColor: accent, borderRadius: 4, borderSkipped: 'bottom', maxBarThickness: 28 }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: matchMedia('(prefers-reduced-motion: reduce)').matches ? false : { duration: 500 },
          interaction: { mode: 'index', intersect: false },
          scales: {
            x: {
              grid: { display: false },
              border: { color: border },
              ticks: { color: faint, font, maxRotation: 0, autoSkip: true, maxTicksLimit: canvas.clientWidth < 500 ? 4 : 6, callback: (_, i) => fmt(days[i].date, { month: 'short', day: 'numeric' }) },
            },
            y: {
              beginAtZero: true,
              suggestedMax: 10,
              grid: { color: border },
              border: { display: false },
              ticks: { color: faint, font, maxTicksLimit: 4, precision: 0, callback: (v) => num(+v) },
            },
          },
          plugins: {
            tooltip: {
              backgroundColor: surface,
              borderColor: border,
              borderWidth: 1,
              titleColor: faint,
              bodyColor: text,
              titleFont: { ...font, weight: 'normal' },
              bodyFont: { family: font.family, size: 14, weight: 'bold' },
              padding: 10,
              cornerRadius: 10,
              displayColors: false,
              callbacks: { title: (items) => fmt(days[items[0].dataIndex].date, { weekday: 'short', month: 'short', day: 'numeric' }), label: (item) => num(item.parsed.y ?? 0) },
            },
          },
        },
      });
    }

    let current = days;
    const flip = () => draw(current);
    scheme.addEventListener('change', flip);
    draw(days);
    return {
      update: (next: Day[]) => draw((current = next)),
      destroy: () => (scheme.removeEventListener('change', flip), (gone = true), chart?.destroy()),
    };
  }
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
        {#if top}<button type="button" class="btn btn-sm btn-primary">Upgrade</button>{/if}
      </div>
      <p class="figure"><b>{num(today)}</b> <span>of {num(quota)} questions answered</span></p>
      <div class="meter" role="meter" aria-label="Today's quota used" aria-valuemin={0} aria-valuemax={quota} aria-valuenow={Math.min(today, quota)}>
        {#if share > 0}<span class="fill" style:--p={share}></span>{/if}
      </div>
      {#if level === 'full'}<p class="note">Limit reached. New mail isn't answered until tomorrow.</p>{/if}
    </section>

    <section class="card reveal d2">
      <div class="card-head"><span>Usage Graph</span></div>
      <div class="plot">
        <canvas use:graph={series} role="img" aria-label="Questions answered per day"></canvas>
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
  .meter { position: relative; height: 14px; border-radius: 999px; background: var(--surface-2); box-shadow: var(--well), inset 0 0 0 1px var(--border); overflow: hidden; }
  .fill {
    position: absolute;
    inset: 0 auto 0 0;
    width: max(calc(var(--p) * 100%), 14px);
    border-radius: inherit;
    background: var(--accent);
    box-shadow: inset 0 1px 0 rgb(255 255 255 / 0.3);
    animation: fill 1s 0.25s var(--ease) both;
  }
  .high .fill { background: var(--signal); }
  .full .fill { background: var(--danger); }
  @keyframes fill { from { clip-path: inset(0 100% 0 0 round 999px); } to { clip-path: inset(0 0 0 0 round 999px); } }
  .note { margin: 0; font-size: 13px; color: var(--danger); }

  .plot { position: relative; height: 240px; padding: 18px 18px 12px; }

  .leave { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }

  .sk-avatar { flex-shrink: 0; width: 64px; height: 64px; border-radius: 30%; }
  .sk-name { width: 180px; height: 26px; border-radius: 8px; }
  .sk-mail { width: 240px; max-width: 100%; }
  .sk-h2 { width: 60px; height: 14px; }
  .sk-figure { width: 220px; height: 34px; border-radius: 8px; }
  .sk-w { width: 90px; }
  .sk-bars { display: flex; align-items: flex-end; gap: 1.5%; }
  .sk-bars .bone { flex: 1; height: calc(var(--h) * 100%); border-radius: 4px 4px 0 0; }

  @media (max-width: 640px) {
    .who .avatar, .sk-avatar { width: 52px; height: 52px; font-size: 22px; }
    .figure b { font-size: 32px; }
    .plot { padding: 14px 10px 8px; height: 220px; }
  }
</style>
