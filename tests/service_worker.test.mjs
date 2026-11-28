import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFileSync } from 'node:fs';

const source = readFileSync(new URL('../sw.js', import.meta.url), 'utf8');

function worker() {
  const listeners = {};
  const loaded = [];
  const deleted = [];
  const saved = new Map();
  const cache = {
    addAll: async urls => loaded.push(...urls),
    match: async request => saved.get(request.url),
    put: async (request, response) => saved.set(request.url, response)
  };
  const context = {
    URL,
    self: {
      location: {href: 'https://example.test/blistartunivers/sw.js'},
      addEventListener: (name, callback) => { listeners[name] = callback; },
      clients: {claim: async () => {}}
    },
    caches: {
      open: async () => cache,
      keys: async () => ['blist-site:/blistartunivers/:v0', 'blist-site:/other/:v0'],
      delete: async name => { deleted.push(name); }
    },
    fetch: async () => { throw new Error('offline'); }
  };
  vm.runInNewContext(source, context);
  return {listeners, loaded, deleted, saved};
}

test('installation caches the shell under the GitHub Pages project path', async () => {
  const h = worker();
  let pending;
  h.listeners.install({waitUntil: promise => { pending = promise; }});
  await pending;
  assert.ok(h.loaded.some(value => value === 'https://example.test/blistartunivers/'));
  assert.ok(h.loaded.every(value => {
    const url = new URL(value);
    return url.origin === 'https://example.test' && url.pathname.startsWith('/blistartunivers/');
  }));
});

test('activation preserves caches belonging to other sites on the same origin', async () => {
  const h = worker();
  let pending;
  h.listeners.activate({waitUntil: promise => { pending = promise; }});
  await pending;
  assert.deepEqual(h.deleted, ['blist-site:/blistartunivers/:v0']);
});

test('offline shell requests fall back to cache and unrelated traffic is untouched', async () => {
  const h = worker();
  const url = 'https://example.test/blistartunivers/';
  h.saved.set(url, 'cached page');
  let response;
  h.listeners.fetch({request: {method: 'GET', url}, respondWith: promise => { response = promise; }});
  assert.equal(await response, 'cached page');
  let intercepted = false;
  h.listeners.fetch({
    request: {method: 'GET', url: 'https://other.test/'},
    respondWith: () => { intercepted = true; }
  });
  assert.equal(intercepted, false);
});
