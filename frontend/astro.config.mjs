import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';
import { glob, readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

// An island only finds its imports once its own file arrives. Listing the whole static import graph as
// modulepreload links fetches it all at once, saving a round trip or two before the page renders.
const preloadIslands = {
  name: 'preload-islands',
  hooks: {
    'astro:build:done': async ({ dir }) => {
      const root = fileURLToPath(dir);
      const graph = async (file, seen) => {
        if (seen.has(file)) return;
        seen.add(file);
        const code = await readFile(root + file, 'utf8');
        for (const [, dep] of code.matchAll(/(?:import|from)"\.\/([\w.-]+\.js)"/g)) await graph(`_astro/${dep}`, seen);
      };
      for await (const page of glob('**/*.html', { cwd: root })) {
        const html = await readFile(root + page, 'utf8');
        const seen = new Set();
        for (const [, url] of html.matchAll(/(?:component|renderer)-url="\/(_astro\/[^"]+)"/g)) await graph(url, seen);
        const links = [...seen].map((f) => `<link rel="modulepreload" href="/${f}">`).join('');
        await writeFile(root + page, html.replace('</head>', `${links}</head>`));
      }
    },
  },
};

// Django serves the API, allauth pages and static files; proxy them in dev so the
// session cookie and CSRF token stay same-origin.
const backend = 'http://127.0.0.1:8000';

export default defineConfig({
  output: 'static',
  outDir: './build',
  integrations: [svelte(), preloadIslands],
  devToolbar: { enabled: false },
  markdown: { syntaxHighlight: false }, // no markdown pages; Shiki's inline styles would break CSP
  // Hashes Astro's inline scripts and styles into a CSP meta tag; Caddy adds frame-ancestors.
  security: {
    csp: {
      directives: [
        "default-src 'self'",
        "img-src 'self' data: https://lh3.googleusercontent.com",
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
