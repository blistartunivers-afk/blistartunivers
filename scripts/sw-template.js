// Service Worker Template - Workbox will inject precache manifest
// This file provides custom logic + runtime caching on top of Workbox

import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching';
import { registerRoute, NavigationRoute } from 'workbox-routing';
import { StaleWhileRevalidate, CacheFirst, NetworkFirst } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';

// Precache manifest (injected by Workbox)
precacheAndRoute(self.__WB_MANIFEST);

// Cleanup old caches
cleanupOutdatedCaches();

// Skip waiting & claim clients
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// ─── Runtime Caching ───

// Google Fonts stylesheets
registerRoute(
  ({ url }) => url.origin === 'https://fonts.googleapis.com',
  new StaleWhileRevalidate({
    cacheName: 'google-fonts-stylesheets',
    plugins: [
      new ExpirationPlugin({ maxEntries: 10, maxAgeSeconds: 60 * 60 * 24 * 365 })
    ]
  })
);

// Google Fonts webfonts
registerRoute(
  ({ url }) => url.origin === 'https://fonts.gstatic.com',
  new CacheFirst({
    cacheName: 'google-fonts-webfonts',
    plugins: [
      new ExpirationPlugin({ maxEntries: 30, maxAgeSeconds: 60 * 60 * 24 * 365 }),
      new CacheableResponsePlugin({ statuses: [0, 200] })
    ]
  })
);

// Dream images (gallery PNGs)
registerRoute(
  ({ url }) => url.pathname.startsWith('/motor/gallery/') && url.pathname.endsWith('.png'),
  new CacheFirst({
    cacheName: 'dream-images',
    plugins: [
      new ExpirationPlugin({ maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 * 30 }),
      new CacheableResponsePlugin({ statuses: [0, 200] })
    ]
  })
);

// Gallery metadata (INDEX.txt, MANIFEST.json, METADATA.json)
registerRoute(
  ({ url }) => url.pathname.includes('INDEX.txt') || 
               url.pathname.includes('MANIFEST.json') || 
               url.pathname.includes('METADATA.json'),
  new StaleWhileRevalidate({
    cacheName: 'gallery-metadata',
    plugins: [
      new ExpirationPlugin({ maxEntries: 10, maxAgeSeconds: 60 * 60 * 24 * 7 })
    ]
  })
);

// HTML pages - NetworkFirst with fallback
registerRoute(
  ({ request }) => request.mode === 'navigate',
  new NetworkFirst({
    cacheName: 'html-cache',
    networkTimeoutSeconds: 3,
    plugins: [
      new ExpirationPlugin({ maxEntries: 20, maxAgeSeconds: 60 * 60 * 24 * 7 })
    ]
  })
);

// Offline fallback for navigation
const navigationRoute = new NavigationRoute(
  new NetworkFirst({
    cacheName: 'html-cache',
    networkTimeoutSeconds: 3
  }),
  {
    denylist: [
      /^\/motor\/gallery\//,
      /\.(?:png|pgm|json|txt)$/
    ]
  }
);
registerRoute(navigationRoute);

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-dreams') {
    event.waitUntil(syncDreams());
  }
});

async function syncDreams() {
  console.log('[SW] Background sync triggered');
}

// Periodic background sync
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'update-gallery-metadata') {
    event.waitUntil(updateGalleryMetadata());
  }
});

async function updateGalleryMetadata() {
  try {
    const cache = await caches.open('gallery-metadata');
    await cache.add('/motor/gallery/MANIFEST.json');
    await cache.add('/motor/gallery/INDEX.txt');
    console.log('[SW] Gallery metadata updated');
  } catch (err) {
    console.warn('[SW] Failed to update gallery metadata:', err);
  }
}

console.log('[SW] Service Worker loaded - BlistArt Univers v11');