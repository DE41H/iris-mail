import { writable } from 'svelte/store';

export interface User {
  username: string;
  email: string;
  tier: number;
  tier_name: string;
  google: boolean; // false once Google access is revoked
  avatar: string | null; // Google profile picture URL
}

// undefined until the first check, null when signed out.
export const session = writable<User | null | undefined>(undefined);

let loading: Promise<void> | undefined;

// Runs once per page however many islands ask.
export const loadSession = () => (loading ??= check());

async function check() {
  // Not through api(): a signed-out visitor is an answer here, not a reason to redirect.
  const res = await fetch('/api/me/', { headers: { Accept: 'application/json' }, credentials: 'same-origin' });
  session.set(res.ok ? ((await res.json()) as User) : null);
}
