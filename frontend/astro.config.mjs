import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';

// Django serves the API, allauth pages and static files; proxy them in dev so the
// session cookie and CSRF token stay same-origin.
const backend = 'http://127.0.0.1:8000';

export default defineConfig({
  output: 'static',
  outDir: './build',
  integrations: [svelte()],
  devToolbar: { enabled: false },
  // Hashes Astro's inline scripts and styles into a CSP meta tag; Caddy adds frame-ancestors.
  security: {
    csp: {
      directives: [
        "default-src 'self'",
        "img-src 'self' data:",
        "connect-src 'self'",
        "base-uri 'self'",
        "object-src 'none'",
        "form-action 'self'",
      ],
    },
  },
  server: { port: 4321 },
  vite: {
    server: {
      proxy: { '/api': backend, '/accounts': backend, '/static': backend, '/admin': backend },
    },
  },
});
