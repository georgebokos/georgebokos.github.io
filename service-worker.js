// FoodDaily Service Worker v3.1
const VERSION = '2026-06-16-02';
const CACHE = `fooddaily-${VERSION}`;
const ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png'
];

// ── TIMER HELPERS ─────────────────────────────────────────────────────────────
// Separate tag for "running" so the done notification is always NEW
// (same tag = Android treats done as an update → no sound/vibration)
const _swShowRunning = () => {
  if (!self._timerEnd) return Promise.resolve();
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

const _clearTimerCache = () =>
  caches.open('fd-prefs').then(c => c.delete('/fd-timer-state')).catch(() => {});

const _swFireDone = () => {
  if (self._timerPoll) { clearInterval(self._timerPoll); self._timerPoll = null; }
  if (self._timerTo)   { clearTimeout(self._timerTo);    self._timerTo   = null; }
  self._timerEnd = null;
  // Clear persisted timer state
  _clearTimerCache();
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

// Persist timer state so it survives SW termination
const _persistTimerState = async () => {
  try {
    const cache = await caches.open('fd-prefs');
    if (self._timerEnd && Date.now() < self._timerEnd) {
      await cache.put('/fd-timer-state', new Response(
        JSON.stringify({ timerEnd: self._timerEnd, mealId: self._timerMealId || '', stepIdx: self._timerStepIdx || 0 }),
        { headers: { 'Content-Type': 'application/json' } }
      ));
    } else {
      await cache.delete('/fd-timer-state');
    }
  } catch(e) {}
};

// Restore timer from cache after SW restart
const _restoreTimerState = async () => {
  try {
    const cache = await caches.open('fd-prefs');
    const resp = await cache.match('/fd-timer-state');
    if (!resp) return;
    const data = await resp.json();
    const remaining = data.timerEnd - Date.now();
    if (remaining <= 0) { await cache.delete('/fd-timer-state'); return; }
    self._timerEnd = data.timerEnd;
    self._timerMealId = data.mealId;
    self._timerStepIdx = data.stepIdx;
    self._timerNotifDismissed = false;
    if (self._timerTo) clearTimeout(self._timerTo);
    if (self._timerPoll) clearInterval(self._timerPoll);
    self._timerTo = setTimeout(_swFireDone, remaining);
    self._timerPoll = setInterval(() => {
      if (self._timerEnd - Date.now() <= 0) _swFireDone();
    }, 5000);
    await _swShowRunning();
  } catch(e) {}
};

// ── DAILY NOTIFICATION HELPERS ────────────────────────────────────────────────

// Build a rich notification body using the featured meal stored by the page
const _buildDailyBody = async () => {
  try {
    const cache = await caches.open('fd-prefs');
    const resp = await cache.match('/fd-featured-meal');
    if (resp) {
      const m = await resp.json();
      const today = new Date().toDateString();
      if (m.date === today && m.name)
        return `${m.emoji || '🍽️'} ${m.name}  |  ⏱ ${m.time}'  |  🔥 ${m.cal}  |  💰 ${m.cost || '~5€'}`;
    }
  } catch(e) {}
  return 'Τι μαγειρεύουμε σήμερα; Δες τις προτάσεις σου!';
};

const _dailyFireAndReschedule = async () => {
  const cache = await caches.open('fd-prefs');
  const today = new Date().toDateString();
  const lastResp = await cache.match('/fd-notif-last');
  if (lastResp && (await lastResp.text()) === today) {
    // Already sent today — reschedule for same time tomorrow
    self._dailyNotifTo = setTimeout(_dailyFireAndReschedule, 24 * 60 * 60 * 1000);
    return;
  }
  try {
    const body = await _buildDailyBody();
    await self.registration.showNotification('🍽️ FoodDaily — Πρόταση Μέρας', {
      body,
      icon: '/icon-192.png',
      badge: '/icon-96.png',
      tag: 'fd-meal-daily',
      vibrate: [200, 100, 200],
      requireInteraction: false
    });
    await cache.put('/fd-notif-last',
      new Response(today, { headers: { 'Content-Type': 'text/plain' } })
    );
  } catch(err) { /* leave notif-last unset so next sync retries */ }
  self._dailyNotifTo = setTimeout(_dailyFireAndReschedule, 24 * 60 * 60 * 1000);
};

const _scheduleDailyNotif = delay => {
  if (self._dailyNotifTo) clearTimeout(self._dailyNotifTo);
  self._dailyNotifTo = setTimeout(_dailyFireAndReschedule, delay);
};

// Restore daily notification schedule from cache after SW restart
const _restoreDailyNotif = async () => {
  try {
    const cache = await caches.open('fd-prefs');
    const resp = await cache.match('/fd-notif-prefs');
    if (!resp) return;
    const prefs = await resp.json();
    if (prefs.on !== 'true') return;
    const [h, m] = (prefs.time || '09:00').split(':').map(Number);
    const now = new Date();
    const next = new Date(now);
    next.setHours(h, m, 0, 0);
    if (next <= now) next.setDate(next.getDate() + 1);
    _scheduleDailyNotif(next - now);
  } catch(e) {}
};

// ── INSTALL ───────────────────────────────────────────────────────────────────
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

// ── ACTIVATE ──────────────────────────────────────────────────────────────────
self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    // Remove stale app caches (keep fd-* preference caches)
    const keys = await caches.keys();
    await Promise.all(
      keys.filter(k => k !== CACHE && !k.startsWith('fd-')).map(k => caches.delete(k))
    );

    await self.clients.claim();

    // Restore persisted state (timer + daily notif) after SW restart
    await _restoreTimerState();
    await _restoreDailyNotif();

    // Notify any already-open windows about the update
    const cls = await self.clients.matchAll({ type: 'window' });
    cls.forEach(c => c.postMessage({ type: 'SW_UPDATED' }));

    // If no windows were open when we activated (app was closed during update),
    // set a flag so the page detects the update on next open.
    if (cls.length === 0) {
      const cache = await caches.open('fd-prefs');
      await cache.put('/fd-sw-update-pending',
        new Response('1', { headers: { 'Content-Type': 'text/plain' } })
      );
    }
  })());
});

// ── FETCH ─────────────────────────────────────────────────────────────────────
// Navigation requests → network-first so the user always gets fresh HTML after an update.
// Asset requests → stale-while-revalidate for instant loads with background refresh.
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return;

  if (e.request.mode === 'navigate') {
    e.respondWith(
      fetch(e.request)
        .then(resp => {
          if (resp && resp.status === 200)
            caches.open(CACHE).then(c => c.put(e.request, resp.clone()));
          return resp;
        })
        .catch(() => caches.match('/index.html'))
    );
    return;
  }

  e.respondWith(
    caches.open(CACHE).then(cache =>
      cache.match(e.request).then(cached => {
        const fetchPromise = fetch(e.request)
          .then(resp => {
            if (resp && resp.status === 200) cache.put(e.request, resp.clone());
            return resp;
          })
          .catch(() => null);
        return cached || fetchPromise;
      })
    )
  );
});

// ── MESSAGES FROM PAGE ────────────────────────────────────────────────────────
self.addEventListener('message', e => {
  if (!e.data) return;

  // Show a notification on behalf of the page (most reliable path on Android TWA)
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

  // Step-timer: persistent notification + 5s poll + keepalive pings from page
  if (e.data.type === 'SCHEDULE_TIMER') {
    if (self._timerTo)   { clearTimeout(self._timerTo);    self._timerTo   = null; }
    if (self._timerPoll) { clearInterval(self._timerPoll); self._timerPoll = null; }
    self._timerEnd = Date.now() + e.data.delay;
    self._timerMealId = e.data.mealId || '';
    self._timerStepIdx = e.data.stepIdx || 0;
    self._timerNotifDismissed = false;

    // Persist to cache so state survives SW termination
    e.waitUntil(_persistTimerState().then(() => _swShowRunning()));

    self._timerPoll = setInterval(() => {
      if (self._timerEnd - Date.now() <= 0) _swFireDone();
    }, 5000);
    self._timerTo = setTimeout(_swFireDone, e.data.delay);
  }

  if (e.data.type === 'CANCEL_TIMER') {
    if (self._timerTo)   { clearTimeout(self._timerTo);    self._timerTo   = null; }
    if (self._timerPoll) { clearInterval(self._timerPoll); self._timerPoll = null; }
    self._timerEnd = null;
    self._timerNotifDismissed = false;
    _clearTimerCache();
    ['fd-timer-run', 'fd-timer'].forEach(tag =>
      self.registration.getNotifications({ tag }).then(ns => ns.forEach(n => n.close()))
    );
  }

  // App minimised — re-show running notification (unless user dismissed it)
  if (e.data.type === 'TIMER_APP_HIDDEN') {
    if (self._timerEnd && !self._timerNotifDismissed) {
      if (self._timerEnd - Date.now() > 0) _swShowRunning();
      else _swFireDone();
    }
  }

  // Keepalive ping from page every ~20 s — wakes SW, checks if timer already expired
  if (e.data.type === 'TIMER_PING') {
    if (self._timerEnd && Date.now() >= self._timerEnd) _swFireDone();
  }

  // Page requests pending navigation (e.g. opened via timer notification tap)
  if (e.data.type === 'GET_PENDING_NAV') {
    if (self._pendingTimerNav && e.source) {
      e.source.postMessage(self._pendingTimerNav);
      self._pendingTimerNav = null;
    }
  }

  // Page tells SW when to fire the daily meal suggestion notification.
  // Uses module-level _dailyFireAndReschedule so the schedule survives across
  // multiple SCHEDULE_DAILY_NOTIF calls (e.g. every app open).
  if (e.data.type === 'SCHEDULE_DAILY_NOTIF') {
    _scheduleDailyNotif(e.data.delay);
  }

  if (e.data.type === 'CANCEL_DAILY_NOTIF') {
    if (self._dailyNotifTo) { clearTimeout(self._dailyNotifTo); self._dailyNotifTo = null; }
  }

  // Page stores featured meal so SW can show rich notifications when app is closed
  if (e.data.type === 'STORE_FEATURED_MEAL') {
    caches.open('fd-prefs').then(c =>
      c.put('/fd-featured-meal', new Response(
        JSON.stringify(e.data.meal),
        { headers: { 'Content-Type': 'application/json' } }
      ))
    );
  }
});

// ── NOTIFICATION EVENTS ───────────────────────────────────────────────────────

// User swiped away the running notification — stop re-showing it
self.addEventListener('notificationclose', e => {
  if (e.notification.tag === 'fd-timer-run' && self._timerEnd && Date.now() < self._timerEnd) {
    self._timerNotifDismissed = true;
  }
});

// Tap notification: open / focus app; timer taps navigate to the recipe step
self.addEventListener('notificationclick', e => {
  e.notification.close();
  const isTimer = e.notification.tag === 'fd-timer' || e.notification.tag === 'fd-timer-run';
  e.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(cls => {
      const existing = cls.find(c => c.url.includes(self.location.origin));
      if (isTimer && self._timerMealId) {
        const msg = { type: 'OPEN_TIMER_STEP', mealId: self._timerMealId, stepIdx: self._timerStepIdx || 0 };
        if (existing) { existing.postMessage(msg); return existing.focus(); }
        // App was closed — store nav target; page will request it via GET_PENDING_NAV
        self._pendingTimerNav = msg;
        return clients.openWindow('/');
      }
      if (existing) return existing.focus();
      return clients.openWindow('/');
    })
  );
});

// ── PERIODIC BACKGROUND SYNC ──────────────────────────────────────────────────
// Backup for when SW setTimeout is lost (SW killed while app was closed).
// Chrome Android fires this every ~3h for installed PWAs.
self.addEventListener('periodicsync', e => {
  if (e.tag === 'fd-daily-notif') {
    e.waitUntil((async () => {
      try {
        const cache = await caches.open('fd-prefs');
        const nowH = new Date().getHours();
        const today = new Date().toDateString();

        // ── Evening prep reminder (18:00–22:00) ──────────────────────────────
        if (nowH >= 18 && nowH < 22) {
          const prepResp = await cache.match('/fd-tomorrow-prep');
          if (prepResp) {
            const prepData = await prepResp.json();
            if (prepData.prepMsg) {
              const lastPrepResp = await cache.match('/fd-prep-last');
              const lastPrep = lastPrepResp ? await lastPrepResp.text() : '';
              if (lastPrep !== today) {
                await self.registration.showNotification(
                  `🍽️ Αύριο: ${prepData.mealName}`,
                  {
                    body: prepData.prepMsg,
                    icon: '/icon-192.png',
                    badge: '/icon-96.png',
                    tag: 'fd-prep',
                    vibrate: [200, 100, 200, 100, 200]
                  }
                );
                await cache.put('/fd-prep-last',
                  new Response(today, { headers: { 'Content-Type': 'text/plain' } })
                );
                return; // One notification per sync cycle
              }
            }
          }
        }

        // ── Daily meal suggestion — respect user's scheduled time ─────────────
        if (nowH >= 23 || nowH < 6) return; // Night blackout window

        const resp = await cache.match('/fd-notif-prefs');
        if (!resp) return;
        const prefs = await resp.json();
        if (prefs.on !== 'true') return;

        // Don't fire before the user's chosen hour:minute
        const now = new Date();
        const [schedH, schedM] = (prefs.time || '09:00').split(':').map(Number);
        const nowMins   = nowH * 60 + now.getMinutes();
        const schedMins = schedH * 60 + schedM;
        if (nowMins < schedMins) return;

        const lastResp = await cache.match('/fd-notif-last');
        if (lastResp && (await lastResp.text()) === today) return; // Already sent today

        const body = await _buildDailyBody();
        try {
          await self.registration.showNotification('🍽️ FoodDaily — Πρόταση Μέρας', {
            body,
            icon: '/icon-192.png',
            badge: '/icon-96.png',
            tag: 'fd-meal-daily',
            vibrate: [200, 100, 200]
          });
          await cache.put('/fd-notif-last',
            new Response(today, { headers: { 'Content-Type': 'text/plain' } })
          );
        } catch(notifErr) { /* leave notif-last unset so next sync retries */ }
      } catch (err) {}
    })());
  }
});
