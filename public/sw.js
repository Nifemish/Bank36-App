/* bank36 PWA service worker
   Required so the browser fires `beforeinstallprompt` (the Install App button)
   and so the installed app can launch/offline-fallback to bank36-app.html. */

const CACHE = 'bank36-v1';
const CORE = [
  'index.html',
  'bank36-register.html',
  'bank36-app.html',
  'manifest.json',
  'icon.svg',
  'icon-512.png'
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE).then((cache) =>
      // Cache what we can; never fail install if one asset 404s.
      Promise.allSettled(CORE.map((url) => cache.add(url)))
    )
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  // For page navigations: try network first, fall back to cached app shell.
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req).catch(() =>
        caches.match(req).then((r) => r || caches.match('bank36-app.html'))
      )
    );
    return;
  }

  // For everything else: cache-first, then network (and cache the result).
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) return cached;
      return fetch(req)
        .then((res) => {
          if (res && res.status === 200 && res.type === 'basic') {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(req, copy));
          }
          return res;
        })
        .catch(() => cached);
    })
  );
});
