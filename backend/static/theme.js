// Blocking, before paint, so the page never flashes the wrong theme. A stored choice beats the system's.
const root = document.documentElement;
const dark = matchMedia('(prefers-color-scheme: dark)');
const apply = () => {
  let t;
  try { t = localStorage.theme; } catch {}
  root.dataset.theme = t || (dark.matches ? 'dark' : 'light');
};
// The browser bar follows the page background, including a theme picked with the toggle.
const bar = document.head.appendChild(Object.assign(document.createElement('meta'), { name: 'theme-color' }));
const paint = () => (bar.content = getComputedStyle(root).getPropertyValue('--bg').trim());
new MutationObserver(paint).observe(root, { attributeFilter: ['data-theme'] });
apply();
dark.addEventListener('change', apply);
