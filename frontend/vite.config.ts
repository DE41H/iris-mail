import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

// Django serves the API, allauth pages and static files; proxy them in dev so the
// session cookie and CSRF token stay same-origin.
const backend = 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [
    sveltekit({
      adapter: adapter(),
      // Every route is listed, so the crawler never requests the stylesheet link in app.html.
      prerender: { crawl: false, entries: ['/', '/plugins/', '/plugins/new/', '/plugins/detail/', '/subscriptions/'] },
    }),
  ],
  server: {
    port: 4321,
    proxy: {
      '/api': backend,
      '/accounts': backend,
      '/static': backend,
      '/admin': backend,
    },
  },
});
