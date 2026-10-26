import { defineConfig } from 'astro/config';

// Django serves the API, allauth pages and static files; proxy them in dev so the
// session cookie and CSRF token stay same-origin.
const backend = 'http://127.0.0.1:8000';

export default defineConfig({
  output: 'static',
  vite: {
    server: {
      proxy: {
        '/api': backend,
        '/accounts': backend,
        '/static': backend,
        '/admin': backend,
      },
    },
  },
});
