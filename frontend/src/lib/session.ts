export interface User {
  username: string;
  email: string;
  tier: number;
}

// undefined until the first check, null when signed out.
let current: User | null | undefined;
const listeners = new Set<(user: User | null) => void>();

export function onSession(fn: (user: User | null) => void) {
  listeners.add(fn);
  if (current !== undefined) fn(current);
  return () => listeners.delete(fn);
}

export async function loadSession() {
  // Not through api(): a signed-out visitor is an answer here, not a reason to redirect.
  const res = await fetch('/api/me/', { headers: { Accept: 'application/json' }, credentials: 'same-origin' });
  current = res.ok ? ((await res.json()) as User) : null;
  listeners.forEach((fn) => fn(current ?? null));
  return current;
}
