import { writable } from 'svelte/store';

export interface User {
  username: string;
  email: string;
  tier: number;
}

// undefined until the first check, null when signed out.
export const session = writable<User | null | undefined>(undefined);

export async function loadSession() {
  // Not through api(): a signed-out visitor is an answer here, not a reason to redirect.
  const res = await fetch('/api/me/', { headers: { Accept: 'application/json' }, credentials: 'same-origin' });
  session.set(res.ok ? ((await res.json()) as User) : null);
}
