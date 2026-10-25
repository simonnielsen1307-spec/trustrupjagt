const CACHE = 'trustrup-v9';
const ASSETS = ['./', './index.html', './manifest.json', './icon-192.png', './icon-512.png'];

self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).catch(() => {}));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE && !k.startsWith('tiles')).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET' || e.request.url.includes('firebasedatabase')) return;
  const url = new URL(e.request.url);
  const same = url.origin === self.location.origin;
  // kort-felter og biblioteker: brug gemt kopi først (virker uden signal)
  if (!same && !/open-meteo|firebase/.test(url.host)) {
    const keep = /unpkg\.com|fonts\.(googleapis|gstatic)\.com/.test(url.host);
    e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(r => {
      if (keep && (r.ok || r.type === 'opaque')) { const c = r.clone(); caches.open(CACHE).then(ca => ca.put(e.request, c)); }
      return r;
    })));
    return;
  }
  // egne filer: spørg altid serveren først (undgår gammel version i 10 min)
  e.respondWith(fetch(e.request, same ? { cache: 'no-cache' } : {}).then(r => {
    if (same && r.ok) { const c = r.clone(); caches.open(CACHE).then(ca => ca.put(e.request, c)); }
    return r;
  }).catch(() => caches.match(e.request)));
});

self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(cs => {
    for (const c of cs) { if ('focus' in c) return c.focus(); }
    return self.clients.openWindow('./');
  }));
});
