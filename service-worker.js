// FoodDaily Service Worker v3.5
const VERSION = '2026-07-29-61';
const CACHE = `fooddaily-2026-07-29-61`;
const ASSETS = [
  '/',
  '/index.html',
  '/dances.html',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png'
];

// Pages that must NOT fall back to /index.html
const STANDALONE_PAGES = new Set(['/dances.html']);

// Install: cache core files immediately, don't wait for old SW to go away
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

// Activate: clear old caches, claim clients, restore persisted timer/notif state
self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    // 1. Clear old versioned caches (keep fd-* pref caches)
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== CACHE && !k.startsWith('fd-')).map(k => caches.delete(k)));

    // 2. Take control of all clients immediately
    await self.clients.claim();

    // 3. Restore timer state if SW was killed mid-timer
    try {
      const cache = await caches.open('fd-prefs');
      const timerResp = await cache.match('/fd-timer-state');
      if (timerResp) {
        const state = await timerResp.json();
        if (state && state.end) {
          const remaining = state.end - Date.now();
          self._timerMealId  = state.mealId  || '';
          self._timerStepIdx = state.stepIdx || 0;
          self._timerEnd     = state.end;
          self._timerNotifDismissed = false;
          if (remaining > 0) {
            // Timer still active — restore
            _swShowRunning();
            if (self._timerPoll) clearInterval(self._timerPoll);
            self._timerPoll = setInterval(() => {
              if (self._timerEnd - Date.now() <= 0) _swFireDone();
            }, 5000);
            if (self._timerTo) clearTimeout(self._timerTo);
            self._timerTo = setTimeout(_swFireDone, remaining);
          } else {
            // Timer expired while SW was dead — fire done notification now
            _swFireDone();
          }
        }
      }

      // 4. Restore daily notification schedule
      if (!self._dailyNotifTo) {
        const dailyResp = await cache.match('/fd-daily-fire-at');
        if (dailyResp) {
          const fireAt = parseInt(await dailyResp.text());
          if (!isNaN(fireAt)) {
            const delay = fireAt - Date.now();
            if (delay > 0 && delay < 24 * 60 * 60 * 1000) {
              self._dailyNotifTo = setTimeout(() => _swFireDailyNotif(cache), delay);
            } else if (delay <= 0) {
              // Should have fired already — fire now (periodic sync may have missed it)
              _swFireDailyNotif(cache);
            }
          }
        }
      }
    } catch (e) {}

    // 5. Notify open tabs only when a genuinely older cache existed (real update)
    if (keys.some(k => k !== CACHE && k.startsWith('fooddaily-'))) {
      self.clients.matchAll({ type: 'window' }).then(clients => {
        clients.forEach(c => c.postMessage({ type: 'SW_UPDATED' }));
      });
    }
  })());
});

// ── DAILY NOTIF FIRE HELPER ───────────────────────────────────────────────────
// Compute next fire timestamp from stored prefs time (h:m tomorrow-or-today)
const _swNextFireAt = async (cache) => {
  let h = 9, m = 0;
  try {
    const pR = await cache.match('/fd-notif-prefs');
    if (pR) { const p = await pR.json(); const t = (p.time || '09:00').split(':'); h = +t[0]; m = +t[1]; }
  } catch (e) {}
  const next = new Date(); next.setHours(h, m, 0, 0);
  if (next <= new Date()) next.setDate(next.getDate() + 1);
  return next.getTime();
};

const _swFireDailyNotif = async (cache) => {
  if (!cache) cache = await caches.open('fd-prefs');
  // Respect user prefs: if notifications are off, clean up and stop
  try {
    const pR = await cache.match('/fd-notif-prefs');
    if (pR) { const p = await pR.json(); if (p.on !== 'true') { await cache.delete('/fd-daily-fire-at'); return; } }
  } catch (e) {}
  const today = new Date().toDateString();
  const lastResp = await cache.match('/fd-notif-last');
  if (lastResp && (await lastResp.text()) === today) {
    // Already sent today — roll the schedule forward so a stale past timestamp
    // can't cause an off-hours fire on the next SW wake-up
    const nx = await _swNextFireAt(cache);
    await cache.put('/fd-daily-fire-at', new Response(String(nx), { headers: { 'Content-Type': 'text/plain' } }));
    return;
  }
  let title = '🍽️ FoodDaily — Πρόταση Μέρας';
  let body  = 'Τι μαγειρεύουμε σήμερα; Δες τις προτάσεις σου!';
  try {
    const mR = await cache.match('/fd-featured-meal');
    if (mR) {
      const m = await mR.json();
      if (m && m.n) body = `${m.e || '🍽️'} ${m.n}  |  ⏱ ${m.time}'  |  🔥 ${m.cal}`;
    }
  } catch (e) {}
  try {
    await self.registration.showNotification(title, {
      body, icon: '/icon-192.png', badge: '/icon-96.png',
      tag: 'fd-meal-daily', vibrate: [200, 100, 200], requireInteraction: false
    });
    await cache.put('/fd-notif-last', new Response(today, { headers: { 'Content-Type': 'text/plain' } }));
  } catch (err) {}
  // Reschedule for tomorrow at the user's chosen time (instead of dropping the schedule)
  const nextAt = await _swNextFireAt(cache);
  await cache.put('/fd-daily-fire-at', new Response(String(nextAt), { headers: { 'Content-Type': 'text/plain' } }));
  const nd = nextAt - Date.now();
  if (self._dailyNotifTo) clearTimeout(self._dailyNotifTo);
  self._dailyNotifTo = (nd > 0 && nd < 25 * 60 * 60 * 1000) ? setTimeout(() => _swFireDailyNotif(null), nd) : null;
};

// Fetch: stale-while-revalidate for same-origin, network-only for external
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return;

  e.respondWith(
    caches.open(CACHE).then(cache =>
      cache.match(e.request).then(cached => {
        const fetchPromise = fetch(e.request).then(resp => {
          if (resp && resp.status === 200) {
            cache.put(e.request, resp.clone());
          }
          return resp;
        }).catch(() => null);

        const fallback = STANDALONE_PAGES.has(url.pathname) ? null : caches.match('/index.html');
        return cached || fetchPromise.then(r => r || fallback);
      })
    )
  );
});

// ── TIMER HELPERS ─────────────────────────────────────────────────────────────
// Running notification uses a SEPARATE tag so the done notification is always NEW
// (same tag = Android treats done as an update → no sound)
const _swShowRunning = () => {
  if (!self._timerEnd) return;
  const end = new Date(self._timerEnd);
  const hh = String(end.getHours()).padStart(2, '0');
  const mm = String(end.getMinutes()).padStart(2, '0');
  return self.registration.showNotification('⏱️ Timer FoodDaily', {
    body: `Τελειώνει στις ${hh}:${mm}`,
    icon: '/icon-192.png',
    badge: '/icon-96.png',
    tag: 'fd-timer-run',
    silent: true,
    requireInteraction: true
  });
};

const _swFireDone = () => {
  if (self._timerPoll) { clearInterval(self._timerPoll); self._timerPoll = null; }
  if (self._timerTo)   { clearTimeout(self._timerTo);    self._timerTo   = null; }
  // Resolve the keep-alive promise so the SW event lifecycle can end cleanly
  if (self._timerWaitResolve) { self._timerWaitResolve(); self._timerWaitResolve = null; }
  // Clear persisted timer state
  caches.open('fd-prefs').then(c => c.delete('/fd-timer-state'));
  // Show done FIRST (running notification still keeping SW alive), THEN close running.
  self.registration.showNotification('⏱️ FoodDaily — Timer', {
    body: 'Ο χρόνος τελείωσε! Δες το επόμενο βήμα.',
    icon: '/icon-192.png',
    badge: '/icon-96.png',
    tag: 'fd-timer',
    vibrate: [300, 150, 300, 150, 300],
    requireInteraction: true
  }).then(() =>
    self.registration.getNotifications({ tag: 'fd-timer-run' })
      .then(ns => ns.forEach(n => n.close()))
  );
};

// ── RESTORE TIMER HELPER (used by TIMER_PING and activate) ───────────────────
const _swRestoreTimer = async () => {
  try {
    const cache = await caches.open('fd-prefs');
    const timerResp = await cache.match('/fd-timer-state');
    if (!timerResp) return;
    const state = await timerResp.json();
    if (!state || !state.end) return;
    const remaining = state.end - Date.now();
    self._timerMealId  = state.mealId  || '';
    self._timerStepIdx = state.stepIdx || 0;
    self._timerEnd     = state.end;
    self._timerNotifDismissed = false;
    if (remaining > 0) {
      _swShowRunning();
      if (self._timerPoll) clearInterval(self._timerPoll);
      self._timerPoll = setInterval(() => {
        if (self._timerEnd - Date.now() <= 0) _swFireDone();
      }, 5000);
      if (self._timerTo) clearTimeout(self._timerTo);
      self._timerTo = setTimeout(_swFireDone, remaining);
    } else {
      _swFireDone();
    }
  } catch (e) {}
};

// Message from page
self.addEventListener('message', e => {
  if (!e.data) return;

  if (e.data.type === 'SHOW_NOTIFICATION') {
    e.waitUntil(
      self.registration.showNotification(e.data.title, {
        body: e.data.body,
        icon: '/icon-192.png',
        badge: '/icon-96.png',
        tag: e.data.tag || 'fd-meal',
        vibrate: [200, 100, 200],
        requireInteraction: false
      })
    );
  }

  // Step-timer: persistent notification + poll + keepalive pings from page
  if (e.data.type === 'SCHEDULE_TIMER') {
    if (self._timerTo)   { clearTimeout(self._timerTo);    self._timerTo   = null; }
    if (self._timerPoll) { clearInterval(self._timerPoll); self._timerPoll = null; }
    self._timerEnd     = Date.now() + e.data.delay;
    self._timerMealId  = e.data.mealId  || '';
    self._timerStepIdx = e.data.stepIdx || 0;
    self._timerNotifDismissed = false;

    // Persist timer state so it survives SW termination
    caches.open('fd-prefs').then(c => c.put('/fd-timer-state', new Response(JSON.stringify({
      end: self._timerEnd, mealId: self._timerMealId, stepIdx: self._timerStepIdx
    }), { headers: { 'Content-Type': 'application/json' } })));

    // Keep SW alive for the full timer duration via a long-lived waitUntil promise.
    // This is the most reliable web mechanism — Android may still kill it for very long
    // timers, but for typical cooking steps (2–60 min) this keeps it alive.
    if (self._timerWaitResolve) { self._timerWaitResolve(); self._timerWaitResolve = null; }
    const _keepAlive = new Promise(r => { self._timerWaitResolve = r; });
    e.waitUntil((_swShowRunning() || Promise.resolve()).then(() => _keepAlive));

    self._timerPoll = setInterval(() => {
      if (self._timerEnd - Date.now() <= 0) _swFireDone();
    }, 5000);

    self._timerTo = setTimeout(_swFireDone, e.data.delay);
  }

  if (e.data.type === 'CANCEL_TIMER') {
    if (self._timerTo)   { clearTimeout(self._timerTo);    self._timerTo   = null; }
    if (self._timerPoll) { clearInterval(self._timerPoll); self._timerPoll = null; }
    if (self._timerWaitResolve) { self._timerWaitResolve(); self._timerWaitResolve = null; }
    self._timerEnd = null;
    self._timerNotifDismissed = false;
    // Clear persisted state
    caches.open('fd-prefs').then(c => c.delete('/fd-timer-state'));
    ['fd-timer-run', 'fd-timer'].forEach(tag =>
      self.registration.getNotifications({ tag }).then(ns => ns.forEach(n => n.close()))
    );
  }

  // App minimised — re-show notification (unless user dismissed it)
  if (e.data.type === 'TIMER_APP_HIDDEN') {
    if (self._timerEnd && !self._timerNotifDismissed) {
      if (self._timerEnd - Date.now() > 0) _swShowRunning();
      else _swFireDone();
    }
  }

  // Keepalive ping from page every ~20 s — wakes SW, restores timer if SW was killed
  if (e.data.type === 'TIMER_PING') {
    if (self._timerEnd) {
      if (Date.now() >= self._timerEnd) _swFireDone();
    } else {
      // SW may have been restarted by Android — check cache for active timer
      e.waitUntil(_swRestoreTimer());
    }
  }

  // Page requests any pending navigation (e.g. opened via timer notification tap)
  if (e.data.type === 'GET_PENDING_NAV') {
    if (self._pendingTimerNav && e.source) {
      e.source.postMessage(self._pendingTimerNav);
      self._pendingTimerNav = null;
    }
  }

  // Daily meal suggestion notification
  if (e.data.type === 'SCHEDULE_DAILY_NOTIF') {
    if (self._dailyNotifTo) clearTimeout(self._dailyNotifTo);
    const fireAt = Date.now() + e.data.delay;

    // Persist scheduled fire time and featured meal info for SW resurrection
    caches.open('fd-prefs').then(async c => {
      await c.put('/fd-daily-fire-at', new Response(String(fireAt), { headers: { 'Content-Type': 'text/plain' } }));
      if (e.data.meal) {
        await c.put('/fd-featured-meal', new Response(JSON.stringify(e.data.meal), { headers: { 'Content-Type': 'application/json' } }));
      }
    });

    const fireAndReschedule = async () => {
      const cache = await caches.open('fd-prefs');
      const today = new Date().toDateString();
      const lastResp = await cache.match('/fd-notif-last');
      if (lastResp && (await lastResp.text()) === today) {
        // Already sent today — reschedule for tomorrow
        const nextFireAt = Date.now() + 24 * 60 * 60 * 1000;
        self._dailyNotifTo = setTimeout(fireAndReschedule, 24 * 60 * 60 * 1000);
        cache.put('/fd-daily-fire-at', new Response(String(nextFireAt), { headers: { 'Content-Type': 'text/plain' } }));
        return;
      }
      await _swFireDailyNotif(cache);
      const nextFireAt = Date.now() + 24 * 60 * 60 * 1000;
      self._dailyNotifTo = setTimeout(fireAndReschedule, 24 * 60 * 60 * 1000);
      cache.put('/fd-daily-fire-at', new Response(String(nextFireAt), { headers: { 'Content-Type': 'text/plain' } }));
    };
    self._dailyNotifTo = setTimeout(fireAndReschedule, e.data.delay);
  }

  if (e.data.type === 'STORE_FEATURED_MEAL') {
    if (e.data.meal) {
      caches.open('fd-prefs').then(c => c.put('/fd-featured-meal',
        new Response(JSON.stringify(e.data.meal), { headers: { 'Content-Type': 'application/json' } })
      ));
    }
  }

  if (e.data.type === 'CANCEL_DAILY_NOTIF') {
    if (self._dailyNotifTo) { clearTimeout(self._dailyNotifTo); self._dailyNotifTo = null; }
    caches.open('fd-prefs').then(c => c.delete('/fd-daily-fire-at'));
  }

  if (e.data.type === 'SCHEDULE_ONE_SHOT_NOTIF') {
    const { delay, title, body, tag } = e.data;
    if (self._oneShotTo) clearTimeout(self._oneShotTo);
    self._oneShotTo = setTimeout(() => {
      self.registration.showNotification(title || '🍳 FoodDaily', {
        body: body || '',
        icon: '/icon-192.png',
        badge: '/icon-96.png',
        tag: tag || 'fd-oneshot',
        requireInteraction: false
      });
      self._oneShotTo = null;
    }, Math.max(0, delay));
  }
});

// Notification dismissed by swipe — if timer still running, mark so we don't re-show
self.addEventListener('notificationclose', e => {
  if (e.notification.tag === 'fd-timer-run' && self._timerEnd && Date.now() < self._timerEnd) {
    self._timerNotifDismissed = true;
  }
});

// Notification click: open or focus the app; for timer taps navigate to the recipe step
self.addEventListener('notificationclick', e => {
  e.notification.close();
  const isTimer = e.notification.tag === 'fd-timer' || e.notification.tag === 'fd-timer-run';
  e.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(cls => {
      const existing = cls.find(c => c.url.includes(self.location.origin));
      if (isTimer && self._timerMealId) {
        const msg = { type: 'OPEN_TIMER_STEP', mealId: self._timerMealId, stepIdx: self._timerStepIdx || 0 };
        if (existing) { existing.postMessage(msg); return existing.focus(); }
        self._pendingTimerNav = msg;
        return clients.openWindow('/');
      }
      if (existing) return existing.focus();
      return clients.openWindow('/');
    })
  );
});

// ── TOP-LEVEL RESTORE ────────────────────────────────────────────────────────
// Runs every time Android kills & restarts the SW (not just on activate).
// Without this, timers and daily notifications are lost silently after SW termination.
(async () => {
  try {
    const cache = await caches.open('fd-prefs');

    // Restore timer
    if (!self._timerEnd) {
      const tr = await cache.match('/fd-timer-state');
      if (tr) {
        const state = await tr.json();
        if (state && state.end) {
          const rem = state.end - Date.now();
          self._timerMealId  = state.mealId  || '';
          self._timerStepIdx = state.stepIdx || 0;
          self._timerEnd     = state.end;
          self._timerNotifDismissed = false;
          if (rem > 0) {
            _swShowRunning();
            if (self._timerPoll) clearInterval(self._timerPoll);
            self._timerPoll = setInterval(() => { if (self._timerEnd - Date.now() <= 0) _swFireDone(); }, 5000);
            if (self._timerTo) clearTimeout(self._timerTo);
            self._timerTo = setTimeout(_swFireDone, rem);
          } else {
            _swFireDone();
          }
        }
      }
    }

    // Restore daily notification
    if (!self._dailyNotifTo) {
      const dr = await cache.match('/fd-daily-fire-at');
      if (dr) {
        const fireAt = parseInt(await dr.text());
        if (!isNaN(fireAt)) {
          const delay = fireAt - Date.now();
          if (delay > 0 && delay < 24 * 60 * 60 * 1000) {
            self._dailyNotifTo = setTimeout(() => _swFireDailyNotif(cache), delay);
          } else if (delay <= 0) {
            _swFireDailyNotif(cache);
          }
        }
      }
    }
  } catch (_) {}
})();

// Periodic Background Sync — daily suggestion + evening prep reminders
self.addEventListener('periodicsync', e => {
  if (e.tag === 'fd-daily-notif') {
    e.waitUntil((async () => {
      try {
        const cache = await caches.open('fd-prefs');
        const nowH = new Date().getHours();
        const today = new Date().toDateString();

        // ── Evening prep reminder (18:00–22:00) ──────────────────
        if (nowH >= 18 && nowH < 22) {
          const prepResp = await cache.match('/fd-tomorrow-prep');
          if (prepResp) {
            const prepData = await prepResp.json();
            if (prepData.prepMsg) {
              const lastPrepResp = await cache.match('/fd-prep-last');
              const lastPrep = lastPrepResp ? await lastPrepResp.text() : '';
              if (lastPrep !== today) {
                await self.registration.showNotification(
                  `${prepData.titlePrefix || '🍽️ Αύριο: '}${prepData.mealName}`,
                  { body: prepData.prepMsg, icon: '/icon-192.png', badge: '/icon-96.png', tag: 'fd-prep', vibrate: [200, 100, 200, 100, 200] }
                );
                await cache.put('/fd-prep-last', new Response(today, { headers: { 'Content-Type': 'text/plain' } }));
                return;
              }
            }
          }
        }

        // ── Daily meal suggestion — respect user's scheduled time ────
        if (nowH >= 23 || nowH < 6) return;

        const resp = await cache.match('/fd-notif-prefs');
        if (!resp) return;
        const prefs = await resp.json();
        if (prefs.on !== 'true') return;

        const now = new Date();
        const [schedH, schedM] = (prefs.time || '09:00').split(':').map(Number);
        const nowMins   = nowH * 60 + now.getMinutes();
        const schedMins = schedH * 60 + schedM;
        if (nowMins < schedMins) return;

        const lastResp = await cache.match('/fd-notif-last');
        if (lastResp && (await lastResp.text()) === today) return;

        // Use cached featured meal for rich notification body
        let title = '🍽️ FoodDaily — Πρόταση Μέρας';
        let body  = 'Τι μαγειρεύουμε σήμερα; Δες τις προτάσεις σου!';
        try {
          const mR = await cache.match('/fd-featured-meal');
          if (mR) {
            const m = await mR.json();
            if (m && m.n) body = `${m.e || '🍽️'} ${m.n}  |  ⏱ ${m.time}'  |  🔥 ${m.cal}`;
          }
        } catch (e) {}

        try {
          await self.registration.showNotification(title, {
            body, icon: '/icon-192.png', badge: '/icon-96.png',
            tag: 'fd-meal-daily', vibrate: [200, 100, 200]
          });
          await cache.put('/fd-notif-last', new Response(today, { headers: { 'Content-Type': 'text/plain' } }));
        } catch (notifErr) {}
      } catch (err) {}
    })());
  }
});
