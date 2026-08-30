// Service worker της εφαρμογής «Φτιάξ' το μόνος σου».
// Εμβέλεια: /diy/ — ΜΟΝΟ αυτή. Δεν αγγίζει τίποτε άλλο στο origin.
// Το cache έχει δικό του πρόθεμα (diy-) ώστε να μη μπερδεύεται ποτέ με άλλες
// εφαρμογές που φιλοξενούνται στο ίδιο domain.
const VERSION = '2026-08-30-3';
const CACHE   = `diy-${VERSION}`;
const SCOPE   = new URL('./', self.location).pathname;   // → /diy/

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
    // Σβήνουμε ΜΟΝΟ παλιά δικά μας cache (πρόθεμα diy-).
    await Promise.all(
      keys.filter(k => k.startsWith('diy-') && k !== CACHE).map(k => caches.delete(k))
    );
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return;
  // Ό,τι είναι εκτός /diy/ δεν μας αφορά — το αφήνουμε στο δίκτυο.
  if (!url.pathname.startsWith(SCOPE)) return;

  // Δίκτυο πρώτα, cache ως εφεδρεία: η σελίδα ενημερώνεται αμέσως μόλις
  // ανέβει νέα έκδοση, αλλά η εφαρμογή δουλεύει και χωρίς σύνδεση.
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
