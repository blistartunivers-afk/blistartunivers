const BASE = new URL('./', self.location.href);
const CACHE_PREFIX = `blist-site:${BASE.pathname}:`;
const CACHE = `${CACHE_PREFIX}v1`;
const SHELL = [
  './', './index.html', './motor/', './motor/index.html',
  './motor/dream-loader.v2.js', './register-sw.js', './app.webmanifest',
  './assets/icon-192.png', './assets/icon-512.png'
].map(path => new URL(path, BASE).href);

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)));
});

self.addEventListener('activate', event => {
  event.waitUntil(Promise.all([
    caches.keys().then(keys => Promise.all(
      keys.filter(key => key.startsWith(CACHE_PREFIX) && key !== CACHE)
        .map(key => caches.delete(key))
    )),
    self.clients.claim()
  ]));
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET' || !SHELL.includes(event.request.url)) return;
  event.respondWith(fetch(event.request).then(response => {
    if (response.ok) {
      const copy = response.clone();
      event.waitUntil(caches.open(CACHE).then(cache => cache.put(event.request, copy)));
    }
    return response;
  }).catch(() => caches.open(CACHE).then(cache => cache.match(event.request))));
});
