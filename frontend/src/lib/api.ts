export interface Page<T> {
  next: string | null;
  previous: string | null;
  results: T[];
}

export class ApiError extends Error {}

const csrfToken = () =>
  document.cookie.split('; ').find((c) => c.startsWith('csrftoken='))?.split('=')[1] ?? '';

// DRF errors are {field: [messages]} or {detail: message}.
const describe = (data: unknown) =>
  data && typeof data === 'object'
    ? Object.entries(data).map(([k, v]) => `${k}: ${[v].flat().join(' ')}`).join(' ')
    : 'Request failed.';

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = init.method ?? 'GET';
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (init.body) headers['Content-Type'] = 'application/json';
  if (method !== 'GET') headers['X-CSRFToken'] = csrfToken();

  const res = await fetch(path, { ...init, method, headers, credentials: 'same-origin' });
  if (res.status === 401 || res.status === 403) {
    location.href = `/accounts/login/?next=${encodeURIComponent(location.pathname)}`;
    throw new ApiError('Sign in required.');
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(describe(data));
  return data as T;
}

export const el = (tag: string, className = '', text = '') => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  node.textContent = text;
  return node;
};
