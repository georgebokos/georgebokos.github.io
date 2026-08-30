/**
 * Ενδιάμεσος worker για τη «βοήθεια με φωτογραφία».
 *
 * Κάνει τρία πράγματα:
 *  1. Κρατά το κλειδί του API. Η σελίδα είναι δημόσια — κλειδί μέσα της θα το
 *     διάβαζε ο καθένας και θα το χρέωνε.
 *  2. Επαληθεύει τη συνδρομή του χρήστη στο RevenueCat, με μυστικό κλειδί.
 *     ΠΟΤΕ δεν εμπιστεύεται τη σελίδα: ένα «είμαι συνδρομητής» από τον πελάτη
 *     το στέλνει οποιοσδήποτε με curl.
 *  3. Μετρά και περιορίζει τις φωτογραφίες ανά χρήστη, ώστε το κόστος να μην
 *     ξεπερνά ποτέ τα έσοδα της συνδρομής.
 *
 * Διαδρομές:
 *   GET  /status       → { active, plan, quotaLeft, credits }
 *   POST /help         → { answer, callPro, quotaLeft, credits }
 *   POST /rc-webhook   → συμβάντα RevenueCat (αγορές, ανανεώσεις, λήξεις)
 */
import Anthropic from '@anthropic-ai/sdk';

const MODEL    = 'claude-opus-5';
const MAX_B64  = 4_500_000;
const PRO_TAG  = '[PRO]';
const RC_BASE  = 'https://api.revenuecat.com/v1';
const RECHECK_MS = 6 * 60 * 60 * 1000;   // κάθε πόσο ξαναρωτάμε το RevenueCat

/* ---------- βοηθητικά ---------- */

function cors(env, extra = {}) {
  return {
    'Access-Control-Allow-Origin': env.ALLOWED_ORIGIN || '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-App-User-Id',
    'Access-Control-Max-Age': '86400',
    'Vary': 'Origin',
    ...extra,
  };
}
const json = (body, status, env) => new Response(JSON.stringify(body), {
  status, headers: cors(env, { 'Content-Type': 'application/json; charset=utf-8' }),
});

const periodKey = () => new Date().toISOString().slice(0, 7);   // 'YYYY-MM'

function packCredits(env, productId) {
  try {
    const map = JSON.parse(env.PACK_PRODUCTS || '{}');
    return map[productId] || 0;
  } catch { return 0; }
}

/* ---------- κατάσταση χρήστη ---------- */

const blank = () => ({ v: 1, checked: 0, active: false, expires: null,
                       period: periodKey(), used: 0, credits: 0, seenTx: [] });

async function loadUser(env, id) {
  if (!env.RL) return blank();
  try { return { ...blank(), ...(JSON.parse(await env.RL.get('u:' + id)) || {}) }; }
  catch { return blank(); }
}
async function saveUser(env, id, rec) {
  if (!env.RL) return;
  // Κρατάμε μόνο τα τελευταία transaction ids· ο πίνακας δεν πρέπει να φουσκώνει.
  rec.seenTx = (rec.seenTx || []).slice(-60);
  await env.RL.put('u:' + id, JSON.stringify(rec), { expirationTtl: 60 * 60 * 24 * 400 });
}

/**
 * Ρωτά το RevenueCat ποια είναι η αλήθεια για αυτόν τον χρήστη.
 * Ενημερώνει τη συνδρομή και πιστώνει όσα πακέτα δεν έχουν ήδη πιστωθεί.
 */
async function verifyWithRevenueCat(env, id, rec) {
  if (!env.RC_SECRET_KEY) return rec;
  let data;
  try {
    const res = await fetch(`${env.RC_API_BASE || RC_BASE}/subscribers/${encodeURIComponent(id)}`, {
      headers: { Authorization: `Bearer ${env.RC_SECRET_KEY}`, 'Content-Type': 'application/json' },
    });
    if (!res.ok) return rec;          // αποτυχία δικτύου: κρατάμε ό,τι ξέραμε
    data = await res.json();
  } catch { return rec; }

  const sub = data && data.subscriber;
  if (!sub) return rec;

  const ent = (sub.entitlements || {})[env.ENTITLEMENT_ID || 'DIY Pro'];
  const exp = ent && ent.expires_date ? Date.parse(ent.expires_date) : null;
  rec.active  = !!ent && (exp === null || exp > Date.now());
  rec.expires = exp;

  // Πακέτα φωτογραφιών: κάθε συναλλαγή πιστώνεται ΜΙΑ φορά.
  const nonSubs = sub.non_subscriptions || {};
  for (const productId of Object.keys(nonSubs)) {
    const credits = packCredits(env, productId);
    if (!credits) continue;
    for (const tx of nonSubs[productId] || []) {
      const txId = tx && (tx.id || tx.store_transaction_id || tx.purchase_date);
      if (!txId || rec.seenTx.includes(txId)) continue;
      rec.seenTx.push(txId);
      rec.credits += credits;
    }
  }
  rec.checked = Date.now();
  return rec;
}

/** Φέρνει την κατάσταση, ξαναρωτώντας το RevenueCat όταν χρειάζεται. */
async function getState(env, id, force) {
  let rec = await loadUser(env, id);
  if (rec.period !== periodKey()) { rec.period = periodKey(); rec.used = 0; }
  const stale = Date.now() - (rec.checked || 0) > RECHECK_MS;
  if (force || stale || (!rec.active && rec.credits === 0)) {
    rec = await verifyWithRevenueCat(env, id, rec);
    await saveUser(env, id, rec);
  }
  return rec;
}

function quotaLeft(env, rec) {
  const q = parseInt(env.SUB_MONTHLY_QUOTA || '60', 10);
  return rec.active ? Math.max(0, q - (rec.used || 0)) : 0;
}

/* ---------- μοντέλο ---------- */

function buildSystem(lang) {
  const el = lang !== 'en';
  return [
    'You are helping someone who is in the middle of a DIY job at home and has got stuck.',
    'They have sent a photo of what is in front of them, plus the exact step of the guide they are on.',
    '',
    'How to answer:',
    '1. Say briefly what you actually see in the photo. If it is blurry, too dark, or shows the wrong thing, say so and ask for a specific better shot instead of guessing.',
    '2. Say whether what you see matches what this step expects, and if not, what is different.',
    '3. Give the concrete next actions, numbered, in the order they should be done.',
    '4. If something in the photo looks unsafe, lead with that before anything else.',
    '',
    'Rules you must not break:',
    '- Never guess about something you cannot actually see in the photo. Say what is uncertain.',
    `- If the job needs a licensed professional (work inside a consumer unit, gas, boilers, structural or load-bearing elements, anything affecting other people's safety), say so plainly and write ${PRO_TAG} on its own line at the end.`,
    '- Never suggest bypassing, removing or disabling a safety device, an earth conductor, an RCD, or a guard.',
    '- If the photo shows burnt, melted or damaged electrical parts, tell them to switch off at the main breaker and call an electrician.',
    '- If the photo has nothing to do with a DIY job, say politely that you can only help with the job in progress.',
    '',
    'Style: short paragraphs, plain words, no jargon without explaining it. Use **bold** for the key action. Aim for 120-220 words. Do not repeat the step text back to them.',
    el ? 'Απάντησε ΑΠΟΚΛΕΙΣΤΙΚΑ στα ελληνικά, σε απλή καθημερινή γλώσσα, στον ενικό.'
       : 'Answer in English only, in plain everyday language.',
  ].join('\n');
}

function buildUser(p) {
  return [
    `Job: ${p.task?.name || '-'}`,
    p.task?.summary ? `What the job is: ${p.task.summary}` : '',
    `They are on step ${p.step?.n}/${p.step?.total}: ${p.step?.title || '-'}`,
    p.step?.detail ? `What this step says to do: ${p.step.detail}` : '',
    Array.isArray(p.safety) && p.safety.length ? `Safety notes for this job: ${p.safety.join(' | ')}` : '',
    p.pro ? `When a professional is required for this job: ${p.pro}` : '',
    p.note ? `What they say is wrong: ${p.note}` : 'They did not describe the problem, so work it out from the photo.',
  ].filter(Boolean).join('\n');
}

/* ---------- διαδρομές ---------- */

async function handleStatus(request, env, userId) {
  const rec = await getState(env, userId);
  return json({
    active: rec.active,
    plan: rec.active ? 'sub' : (rec.credits > 0 ? 'pack' : null),
    quotaLeft: quotaLeft(env, rec),
    credits: rec.credits || 0,
  }, 200, env);
}

async function handleHelp(request, env, userId) {
  const rec = await getState(env, userId);
  const left = quotaLeft(env, rec);
  const free = parseInt(env.FREE_TRIAL || '0', 10);
  const usedFree = rec.freeUsed || 0;
  const onFreeTrial = !rec.active && rec.credits === 0 && usedFree < free;

  if (!rec.active && rec.credits === 0 && !onFreeTrial) {
    return json({ error: 'no_entitlement', active: false, quotaLeft: 0, credits: 0 }, 402, env);
  }
  if (rec.active && left === 0 && rec.credits === 0) {
    return json({ error: 'quota_exhausted', active: true, quotaLeft: 0, credits: rec.credits || 0 }, 402, env);
  }

  let p;
  try { p = await request.json(); } catch { return json({ error: 'bad_json' }, 400, env); }
  if (!p || typeof p.image !== 'string' || !p.image) return json({ error: 'no_image' }, 400, env);
  if (p.image.length > MAX_B64) return json({ error: 'image_too_large' }, 413, env);

  const mime = ['image/jpeg', 'image/png', 'image/webp'].includes(p.mime) ? p.mime : 'image/jpeg';
  const client = new Anthropic({ apiKey: env.ANTHROPIC_API_KEY });

  let response;
  try {
    response = await client.beta.messages.create({
      model: MODEL,
      // Σκόπιμα φραγμένο: το κόστος ανά αίτημα πρέπει να είναι προβλέψιμο,
      // γιατί το καλύπτει η συνδρομή του χρήστη.
      max_tokens: 2000,
      thinking: { type: 'adaptive' },
      output_config: { effort: env.EFFORT || 'medium' },
      betas: ['server-side-fallback-2026-07-01'],
      fallbacks: 'default',
      system: buildSystem(p.lang),
      messages: [{
        role: 'user',
        content: [
          { type: 'image', source: { type: 'base64', media_type: mime, data: p.image } },
          { type: 'text', text: buildUser(p) },
        ],
      }],
    });
  } catch (err) {
    // Αποτυχία του μοντέλου δεν χρεώνεται στον χρήστη.
    if (err?.status === 429) return json({ error: 'upstream_rate_limited' }, 429, env);
    return json({ error: 'upstream_error' }, 502, env);
  }

  if (response.stop_reason === 'refusal') return json({ error: 'refused' }, 422, env);

  let answer = (response.content || []).filter(b => b.type === 'text').map(b => b.text).join('\n').trim();
  if (!answer) return json({ error: 'empty_answer' }, 502, env);

  const callPro = answer.includes(PRO_TAG);
  answer = answer.split(PRO_TAG).join('').trim();

  // Χρέωση μόνο μετά από επιτυχημένη απάντηση.
  if (onFreeTrial)      rec.freeUsed = usedFree + 1;
  else if (rec.active)  rec.used = (rec.used || 0) + 1;
  else                  rec.credits = Math.max(0, (rec.credits || 0) - 1);
  await saveUser(env, userId, rec);

  return json({ answer, callPro, quotaLeft: quotaLeft(env, rec), credits: rec.credits || 0 }, 200, env);
}

/**
 * Συμβάντα RevenueCat. Κρατούν την κατάσταση ενημερωμένη χωρίς να περιμένουμε
 * τον επόμενο έλεγχο, και πιστώνουν αμέσως τα πακέτα φωτογραφιών.
 */
async function handleWebhook(request, env) {
  const auth = request.headers.get('Authorization') || '';
  if (!env.RC_WEBHOOK_TOKEN || auth !== env.RC_WEBHOOK_TOKEN) {
    return new Response('forbidden', { status: 403 });
  }
  let ev;
  try { ev = (await request.json()).event; } catch { return new Response('bad json', { status: 400 }); }
  if (!ev || !ev.app_user_id) return new Response('ignored', { status: 200 });

  const id = ev.app_user_id;
  const rec = await loadUser(env, id);
  if (rec.period !== periodKey()) { rec.period = periodKey(); rec.used = 0; }

  const type = ev.type;
  if (type === 'NON_RENEWING_PURCHASE') {
    const credits = packCredits(env, ev.product_id);
    const txId = ev.transaction_id || ev.id;
    if (credits && txId && !rec.seenTx.includes(txId)) {
      rec.seenTx.push(txId);
      rec.credits += credits;
    }
  } else if (['INITIAL_PURCHASE', 'RENEWAL', 'UNCANCELLATION', 'PRODUCT_CHANGE'].includes(type)) {
    rec.active  = true;
    rec.expires = ev.expiration_at_ms || null;
  } else if (['EXPIRATION', 'SUBSCRIPTION_PAUSED'].includes(type)) {
    rec.active = false;
  }
  // CANCELLATION σημαίνει «δεν θα ανανεωθεί», όχι «έληξε τώρα» — ο χρήστης
  // κρατά την πρόσβασή του μέχρι το EXPIRATION.

  rec.checked = 0;   // ώστε ο επόμενος έλεγχος να επιβεβαιώσει με το RevenueCat
  await saveUser(env, id, rec);
  return new Response('ok', { status: 200 });
}

/* ---------- είσοδος ---------- */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, '') || '/';

    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors(env) });

    // Τα webhooks έρχονται από το RevenueCat, όχι από browser: δικός τους έλεγχος.
    if (path === '/rc-webhook') {
      if (request.method !== 'POST') return new Response('method', { status: 405 });
      return handleWebhook(request, env);
    }

    const origin = request.headers.get('Origin');
    if (env.ALLOWED_ORIGIN && origin && origin !== env.ALLOWED_ORIGIN) {
      return json({ error: 'forbidden_origin' }, 403, env);
    }

    const userId = (request.headers.get('X-App-User-Id') || '').trim();
    if (!userId || userId.length > 200) return json({ error: 'no_user' }, 401, env);

    if (path === '/status' && request.method === 'GET')  return handleStatus(request, env, userId);
    if (path === '/help'   && request.method === 'POST') {
      if (!env.ANTHROPIC_API_KEY) return json({ error: 'not_configured' }, 500, env);
      return handleHelp(request, env, userId);
    }
    return json({ error: 'not_found' }, 404, env);
  },
};
