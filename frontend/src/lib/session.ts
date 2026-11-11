import { writable } from 'svelte/store';

export interface User {
  username: string;
  email: string;
  tier: string;
  quota: number; // questions per day
  tiers: { tier: number; name: string; quota: number }[]; // every tier, lowest first
  google: boolean; // false once Google access is revoked
  avatar: string | null; // Google profile picture URL
}

const KEY = 'iris-session';
const cached = (): User | null | undefined => {
  try { return JSON.parse(sessionStorage.getItem(KEY) ?? 'undefined'); } catch { return undefined; }
};

// undefined until the first check, null when signed out. Starts from the last page's answer so the nav doesn't reflow.
export const session = writable<User | null | undefined>(cached());

let loading: Promise<void> | undefined;

// Runs once per page however many islands ask.
export const loadSession = () => (loading ??= check());

async function check() {
  // Not through api(): a signed-out visitor is an answer here, not a reason to redirect.
  const res = await fetch('/api/v1/me/', { headers: { Accept: 'application/json' }, credentials: 'same-origin' });
  // Only 401/403 mean signed out; a throttle or deploy blip keeps the last known answer.
  if (!res.ok && res.status !== 401 && res.status !== 403) return session.update((s) => s ?? null);
  const user = res.ok ? ((await res.json()) as User) : null;
  session.set(user);
  try { sessionStorage.setItem(KEY, JSON.stringify(user)); } catch {}
}
