import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';
import { glob, readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { brotliCompressSync, constants } from 'node:zlib';

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

// Max-level brotli once at build beats Caddy's fast on-the-fly level by ~15-20%; Caddy serves the .br files.
const precompress = {
  name: 'precompress',
  hooks: {
    'astro:build:done': async ({ dir }) => {
      const root = fileURLToPath(dir);
      for await (const file of glob('**/*.{html,js,css,json,svg}', { cwd: root })) {
        const data = await readFile(root + file);
        await writeFile(`${root + file}.br`, brotliCompressSync(data, { params: { [constants.BROTLI_PARAM_QUALITY]: 11 } }));
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
  integrations: [svelte(), preloadIslands, precompress], // precompress last: it must see the final HTML
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
