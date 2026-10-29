// Writes a CSP source for every inline script in the build, so Caddy can allow exactly those scripts
// without 'unsafe-inline'. Each prerendered page has its own bootstrap script, so the set has several hashes.
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const htmlFiles = (dir) =>
  readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return htmlFiles(path);
    return name.endsWith('.html') ? [path] : [];
  });

const sources = new Set();
for (const file of htmlFiles('build')) {
  for (const [, body] of readFileSync(file, 'utf8').matchAll(/<script>([\s\S]*?)<\/script>/g)) {
    sources.add(`'sha256-${createHash('sha256').update(body).digest('base64')}'`);
  }
}

writeFileSync('build/csp-script-src', [...sources].join(' '));
console.log(`csp-script-src: ${sources.size} inline script hash(es)`);
