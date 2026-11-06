<script lang="ts">
  import { onMount } from 'svelte';
  import { fly } from 'svelte/transition';

  // Example mail for the landing demo, answered with the matching template's questions.
  const SCENES = [
    {
      title: 'Spending',
      from: 'receipts@northwind.example',
      subject: 'Your receipt from Northwind',
      body: ['Pro plan, billed monthly.', 'Renews on the 5th.', 'Total charged: $12.00'],
      out: { receipt: true, spend_category: 'software', subscription: true, rules: { amount: ['$12.00'] } },
    },
    {
      title: 'Inbox priority',
      from: 'sam@team.example',
      subject: 'Contract needs your signature',
      body: ['The client signed their part.', 'Can you sign and send it back', 'before Friday noon?'],
      out: { importance: 5, needs_reply: true, has_deadline: true, next_action: 'reply' },
    },
    {
      title: 'Security alerts',
      from: 'no-reply@accounts.example',
      subject: 'New sign-in to your account',
      body: ['Chrome on Windows, near Lisbon.', 'IP address 203.0.113.42', 'Not you? Reset your password.'],
      out: { alert: 'new_sign_in', risk: 3, rules: { ip_address: ['203.0.113.42'] } },
    },
  ];
  const PHASES = ['arrive', 'read', 'answer', 'drop'] as const;
  const STEP = { arrive: 900, read: 1700, answer: 1500, drop: 2800 };
  const CAPTION = {
    arrive: 'A new email arrives.',
    read: 'Laya reads it against your questions.',
    answer: 'Answers come out as JSON.',
    drop: 'The email is dropped. Only the answers stay.',
  };

  let scene = $state(0);
  let phase = $state<(typeof PHASES)[number]>('drop');
  let auto = true;
  let timer: ReturnType<typeof setTimeout>;
  const s = $derived(SCENES[scene]);

  function play(at: number) {
    clearTimeout(timer);
    scene = at;
    phase = 'arrive';
    let i = 0;
    const next = () => {
      if (++i < PHASES.length) {
        phase = PHASES[i];
        timer = setTimeout(next, STEP[phase]);
      } else if (auto) play((scene + 1) % SCENES.length);
    };
    timer = setTimeout(next, STEP.arrive);
  }

  function pick(i: number) {
    auto = false;
    play(i);
  }

  onMount(() => {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) phase = 'answer';
    else play(0);
    return () => clearTimeout(timer);
  });
</script>

<figure class="bench" data-phase={phase}>
  <figcaption class="sr">Example: an email goes through Iris and comes out as JSON answers; the email itself is not kept.</figcaption>

  <div class="stage" aria-hidden="true">
    {#key scene}
      <article class="mail" in:fly={{ x: -40, duration: 600, opacity: 0 }}>
        <div class="from">{s.from}</div>
        <div class="subject">{s.subject}</div>
        <div class="body">
          {#each s.body as line, i}<p style:--i={i}><span>{line}</span></p>{/each}
        </div>
        <div class="scan"></div>
      </article>
    {/key}

    <div class="beam in"></div>

    <svg class="iris" viewBox="-64 -64 128 128">
      <defs>
        <clipPath id="lens"><circle r="56" /></clipPath>
        <radialGradient id="pupil">
          <stop offset="0" class="s0" />
          <stop offset="0.55" class="s1" />
          <stop offset="1" class="s2" />
        </radialGradient>
      </defs>
      <circle r="62" class="halo" />
      <g clip-path="url(#lens)">
        <circle r="56" fill="url(#pupil)" />
        <g class="blades">
          {#each { length: 6 } as _, i}
            <g transform={`rotate(${i * 60})`}><path class="blade" style:--i={i} d="M0,-80 A80,80 0 0 1 69.28,-40 L0,0 Z" /></g>
          {/each}
        </g>
      </g>
      <circle r="56" class="rim" />
    </svg>

    <div class="beam out"></div>

    <div class="answers">
      <div class="label">output</div>
      {#key scene}
        <pre>{'{'}{#each Object.entries(s.out) as [k, v], i}<span class="line" style:--i={i}>  <b>"{k}"</b>: <em class:str={typeof v === 'string'}>{JSON.stringify(v)}</em>{i < Object.keys(s.out).length - 1 ? ',' : ''}</span>{/each}{'}'}</pre>
      {/key}
    </div>
  </div>

  <div class="caption" aria-hidden="true">
    {#key phase}<span in:fly={{ y: 8, duration: 350 }}>{CAPTION[phase]}</span>{/key}
  </div>

  <div class="picker" role="group" aria-label="Example plugins">
    {#each SCENES as sc, i}
      <button type="button" aria-pressed={scene === i} onclick={() => pick(i)}>{sc.title}</button>
    {/each}
  </div>
</figure>

<style>
  .bench { margin: 0; display: grid; gap: 14px; }
  .sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); }
  .stage {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 56px clamp(120px, 14vw, 168px) 56px minmax(0, 1fr);
    align-items: stretch;
    min-height: 190px;
  }

  /* The email */
  .mail {
    position: relative;
    overflow: hidden;
    padding: 16px 18px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    font-size: 14px;
    transition: opacity 0.8s var(--ease), translate 0.8s var(--ease), filter 0.8s;
  }
  .from { color: var(--muted); font-size: 13px; }
  .subject { font-weight: 640; margin: 2px 0 10px; }
  .body { display: grid; gap: 4px; color: var(--muted); }
  .body span { transition: color 0.4s, background 0.4s; border-radius: 4px; }
  /* Read: lines light up in turn. Drop: they collapse into blank bars, so nothing is kept. */
  [data-phase='read'] .body span { animation: lit 1.5s calc(var(--i) * 0.35s) both; }
  [data-phase='drop'] .body span { color: transparent; background: var(--border); transition-delay: calc(var(--i) * 0.08s); }
  [data-phase='drop'] .subject, [data-phase='drop'] .from { opacity: 0.35; transition: opacity 0.6s; }
  [data-phase='drop'] .mail { opacity: 0.55; translate: 0 6px; filter: saturate(0.2); }
  @keyframes lit { 30%, 70% { color: var(--text); background: var(--signal-soft); } }
  .scan {
    position: absolute;
    inset: 0 0 auto;
    height: 40%;
    background: linear-gradient(180deg, transparent, color-mix(in oklab, var(--accent) 12%, transparent), transparent);
    translate: 0 -100%;
    pointer-events: none;
  }
  [data-phase='read'] .scan { animation: sweep 1.6s var(--ease) both; }
  @keyframes sweep { to { translate: 0 260%; } }

  /* Beams between the parts */
  .beam { align-self: center; height: 2px; margin: 0 6px; border-radius: 2px; background: var(--border); position: relative; overflow: hidden; }
  .beam::after {
    content: '';
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(90deg, currentColor 0 6px, transparent 6px 14px);
    opacity: 0;
    transition: opacity 0.3s;
    animation: flow 0.5s linear infinite;
  }
  .beam.in { color: var(--faint); }
  .beam.out { color: var(--accent); }
  [data-phase='read'] .beam.in::after, [data-phase='answer'] .beam.out::after { opacity: 1; }
  @keyframes flow { from { background-position: -14px 0; } to { background-position: 0 0; } }

  /* The aperture: six blades swing open on their rim pivots while Laya reads. */
  .iris { width: 100%; overflow: visible; align-self: center; }
  .s0 { stop-color: var(--signal); }
  .s1 { stop-color: color-mix(in oklab, var(--signal) 70%, var(--accent)); }
  .s2 { stop-color: var(--accent-strong); }
  .halo { fill: none; stroke: var(--accent-soft); stroke-width: 6; transition: stroke 0.6s, stroke-width 0.6s; }
  [data-phase='read'] .halo, [data-phase='answer'] .halo { stroke: color-mix(in oklab, var(--accent) 22%, transparent); stroke-width: 14; }
  .rim { fill: none; stroke: var(--accent-strong); stroke-width: 2; }
  .blades { transform-origin: 0 0; transition: rotate 1.6s var(--ease); }
  [data-phase='read'] .blades, [data-phase='answer'] .blades { rotate: 60deg; }
  .blade {
    transform-box: fill-box;
    transform-origin: 0 0;
    fill: color-mix(in oklab, var(--accent) calc(58% + var(--i) * 7%), var(--accent-strong));
    stroke: color-mix(in oklab, var(--accent-strong) 60%, black);
    stroke-width: 0.8;
    rotate: -5deg;
    transition: rotate 1.1s var(--spring);
    transition-delay: calc(var(--i) * 30ms);
  }
  [data-phase='read'] .blade, [data-phase='answer'] .blade { rotate: -34deg; }

  /* The answers */
  .answers {
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 16px 18px;
    background: var(--surface);
    border: 1px solid color-mix(in oklab, var(--accent) 25%, var(--border));
    border-radius: var(--radius);
    box-shadow: var(--shadow-lift);
  }
  .label { font-size: 12.5px; color: var(--muted); margin-bottom: 6px; }
  pre { margin: 0; font-size: 13px; line-height: 1.7; white-space: pre-wrap; overflow-wrap: anywhere; color: var(--faint); }
  .line { display: block; opacity: 0; translate: 8px 0; transition: opacity 0.4s var(--ease), translate 0.5s var(--spring); }
  [data-phase='answer'] .line, [data-phase='drop'] .line { opacity: 1; translate: 0; transition-delay: calc(var(--i) * 0.18s); }
  b { font-weight: 500; color: var(--accent); }
  em { font-style: normal; color: var(--signal-text); }
  em.str { color: var(--text); }

  .caption { min-height: 1.6em; text-align: center; color: var(--muted); font-size: 14px; }
  .picker { display: flex; justify-content: center; gap: 6px; flex-wrap: wrap; }
  .picker button {
    padding: 5px 14px;
    border: 1px solid var(--border);
    border-radius: var(--radius-btn);
    corner-shape: squircle;
    background: transparent;
    color: var(--muted);
    font: 500 13px var(--font);
    cursor: pointer;
    transition: color 0.2s, background 0.2s, border-color 0.2s;
  }
  .picker button:hover { color: var(--text); border-color: var(--border-strong); }
  .picker button[aria-pressed='true'] { color: var(--accent); background: var(--accent-soft); border-color: transparent; }

  @media (max-width: 760px) {
    .stage { grid-template-columns: minmax(0, 1fr); justify-items: stretch; gap: 0; }
    .iris { width: 120px; justify-self: center; }
    .beam { width: 2px; height: 28px; justify-self: center; margin: 6px 0; }
    .beam::after { background: repeating-linear-gradient(180deg, currentColor 0 6px, transparent 6px 14px); animation-name: flow-down; }
    @keyframes flow-down { from { background-position: 0 -14px; } to { background-position: 0 0; } }
  }
</style>
