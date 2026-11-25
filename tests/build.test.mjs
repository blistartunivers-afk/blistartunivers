import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));

test('build works outside the checkout and emits the motor module it imports', () => {
  const cwd = mkdtempSync(join(tmpdir(), 'blist-site-build-'));
  try {
    execFileSync(process.execPath, [join(root, 'scripts/build.mjs')], { cwd });
    for (const page of ['index.html', 'motor/index.html']) {
      const html = readFileSync(join(root, 'dist', page), 'utf8');
      assert.ok(!html.includes('cppn-engine.js'), 'missing engine must not be imported');
      assert.ok(!html.includes("register('/sw.js')"), 'missing service worker must not be registered');
    }
    assert.ok(existsSync(join(root, 'dist/motor/dream-loader.v2.js')));
    assert.ok(existsSync(join(root, 'dist/motor/gallery/INDEX.txt')));
    const app = JSON.parse(readFileSync(join(root, 'dist/app.webmanifest'), 'utf8'));
    for (const icon of app.icons) {
      assert.ok(existsSync(join(root, 'dist', icon.src)));
    }
    assert.ok(existsSync(join(root, 'dist/sw.js')));
    const manifest = JSON.parse(readFileSync(join(root, 'dist/manifest.json'), 'utf8'));
    for (const path of Object.keys(manifest.files)) {
      assert.ok(existsSync(join(root, 'dist', path)), `missing manifest entry: ${path}`);
    }
  } finally {
    rmSync(cwd, { recursive: true, force: true });
  }
});
