import { el } from './api';

// Shows a freshly issued key. The server returns it once, so this card is the only place it lives.
export function keyCard(key: string, ...actions: HTMLElement[]) {
  const card = el('section', 'card key-card');
  const copy = el('button', 'btn btn-sm', 'Copy key');
  copy.type = 'button';
  copy.addEventListener('click', async () => {
    await navigator.clipboard.writeText(key);
    copy.textContent = 'Copied';
    setTimeout(() => (copy.textContent = 'Copy key'), 1500);
  });
  card.append(
    el('h2', '', 'Your API key'),
    el('p', 'muted', 'Copy it now. It will not be shown again.'),
    el('code', 'mono', key),
    el('div', 'actions', ''),
  );
  card.lastElementChild!.append(copy, ...actions);
  return card;
}
