// Service worker της εφαρμογής «Ελληνικοί Παραδοσιακοί Χοροί».
// Εμβέλεια: /dances/ — ΜΟΝΟ αυτή. Δεν αγγίζει τίποτε άλλο στο origin.
// Το cache έχει δικό του πρόθεμα (dances-) ώστε να μη μπερδεύεται ποτέ με
// άλλες εφαρμογές που φιλοξενούνται στο ίδιο domain.
const VERSION = '2026-08-29-1';
const CACHE   = `dances-${VERSION}`;
const SCOPE   = new URL('./', self.location).pathname;   // → /dances/

const ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icon.svg',
  './icon-192.png',
  './icon-512.png'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(ASSETS))
      .then(() => self.skipWaiting())
      .catch(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    // Σβήνουμε ΜΟΝΟ παλιά δικά μας cache (πρόθεμα dances-).
    await Promise.all(
      keys.filter(k => k.startsWith('dances-') && k !== CACHE).map(k => caches.delete(k))
    );
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  // Οι φωτογραφίες των χορών έρχονται από τη Wikipedia: εκτός origin,
  // δεν τις αγγίζουμε καθόλου.
  if (url.origin !== location.origin) return;
  // Ό,τι είναι εκτός /dances/ δεν μας αφορά.
  if (!url.pathname.startsWith(SCOPE)) return;

  // Δίκτυο πρώτα, cache ως εφεδρεία.
  e.respondWith(
    fetch(e.request).then(resp => {
      if (resp && resp.status === 200 && resp.type === 'basic') {
        const copy = resp.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy));
      }
      return resp;
    }).catch(() =>
      caches.match(e.request).then(cached => cached || caches.match('./index.html'))
    )
  );
});
