// Blocking, before paint, so the page never flashes the wrong theme. A stored choice beats the system's.
const dark = matchMedia('(prefers-color-scheme: dark)');
const apply = () => {
  let t;
  try { t = localStorage.theme; } catch {}
  document.documentElement.dataset.theme = t || (dark.matches ? 'dark' : 'light');
};
apply();
dark.addEventListener('change', apply);
