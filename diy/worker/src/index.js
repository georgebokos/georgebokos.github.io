/**
 * Ενδιάμεσος worker για τη «βοήθεια με φωτογραφία».
 *
 * Γιατί υπάρχει: η εφαρμογή είναι στατική σελίδα που τη διαβάζει ο καθένας.
 * Κλειδί API μέσα της θα ήταν εκτεθειμένο σε όλους. Ο worker κρατά το κλειδί
 * ως secret, ελέγχει ποιος τον καλεί, βάζει όρια χρήσης, και μόνο μετά
 * προωθεί το αίτημα στο μοντέλο.
 */
import Anthropic from '@anthropic-ai/sdk';

const MODEL = 'claude-opus-5';
const MAX_B64 = 4_500_000;   // ~3,4 MB εικόνα· ο πελάτης στέλνει πολύ μικρότερη
const PRO_TAG = '[PRO]';     // το μοντέλο το βάζει όταν χρειάζεται επαγγελματίας

function cors(env, extra = {}) {
  return {
    'Access-Control-Allow-Origin': env.ALLOWED_ORIGIN || '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
    'Vary': 'Origin',
    ...extra,
  };
}

function json(body, status, env) {
  return new Response(JSON.stringify(body), {
    status,
    headers: cors(env, { 'Content-Type': 'application/json; charset=utf-8' }),
  });
}

/** Όρια ανά IP. Χωρίς το KV binding RL δεν εφαρμόζονται — ο worker δουλεύει,
 *  αλλά είναι εκτεθειμένος σε κατάχρηση, γι' αυτό το KV συνιστάται. */
async function overLimit(request, env) {
  if (!env.RL) return false;
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
  const now = new Date();
  const hourKey = `h:${ip}:${now.toISOString().slice(0, 13)}`;
  const dayKey  = `d:${ip}:${now.toISOString().slice(0, 10)}`;
  const perHour = parseInt(env.LIMIT_PER_HOUR || '12', 10);
  const perDay  = parseInt(env.LIMIT_PER_DAY  || '40', 10);

  const [h, d] = await Promise.all([env.RL.get(hourKey), env.RL.get(dayKey)]);
  if ((parseInt(h || '0', 10) >= perHour) || (parseInt(d || '0', 10) >= perDay)) return true;

  await Promise.all([
    env.RL.put(hourKey, String(parseInt(h || '0', 10) + 1), { expirationTtl: 3900 }),
    env.RL.put(dayKey,  String(parseInt(d || '0', 10) + 1), { expirationTtl: 90000 }),
  ]);
  return false;
}

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
    el
      ? 'Απάντησε ΑΠΟΚΛΕΙΣΤΙΚΑ στα ελληνικά, σε απλή καθημερινή γλώσσα, στον ενικό.'
      : 'Answer in English only, in plain everyday language.',
  ].join('\n');
}

function buildUser(p) {
  const lines = [
    `Job: ${p.task?.name || '-'}`,
    p.task?.summary ? `What the job is: ${p.task.summary}` : '',
    `They are on step ${p.step?.n}/${p.step?.total}: ${p.step?.title || '-'}`,
    p.step?.detail ? `What this step says to do: ${p.step.detail}` : '',
    Array.isArray(p.safety) && p.safety.length ? `Safety notes for this job: ${p.safety.join(' | ')}` : '',
    p.pro ? `When a professional is required for this job: ${p.pro}` : '',
    p.note ? `What they say is wrong: ${p.note}` : 'They did not describe the problem, so work it out from the photo.',
  ];
  return lines.filter(Boolean).join('\n');
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors(env) });
    if (request.method !== 'POST')    return json({ error: 'method_not_allowed' }, 405, env);

    // Μόνο η δική μας σελίδα. Δεν είναι απόλυτη προστασία (το Origin
    // πλαστογραφείται εκτός browser) αλλά κόβει την εύκολη κατάχρηση.
    const origin = request.headers.get('Origin');
    if (env.ALLOWED_ORIGIN && origin && origin !== env.ALLOWED_ORIGIN) {
      return json({ error: 'forbidden_origin' }, 403, env);
    }
    if (!env.ANTHROPIC_API_KEY) return json({ error: 'not_configured' }, 500, env);
    if (await overLimit(request, env)) return json({ error: 'rate_limited' }, 429, env);

    let p;
    try { p = await request.json(); }
    catch { return json({ error: 'bad_json' }, 400, env); }

    if (!p || typeof p.image !== 'string' || !p.image) return json({ error: 'no_image' }, 400, env);
    if (p.image.length > MAX_B64) return json({ error: 'image_too_large' }, 413, env);

    const mime = ['image/jpeg', 'image/png', 'image/webp'].includes(p.mime) ? p.mime : 'image/jpeg';
    const client = new Anthropic({ apiKey: env.ANTHROPIC_API_KEY });

    let response;
    try {
      response = await client.beta.messages.create({
        model: MODEL,
        // Σκόπιμα χαμηλό: η απάντηση είναι σύντομη και το άκρο είναι δημόσιο,
        // οπότε το ανώτατο κόστος ανά αίτημα πρέπει να είναι φραγμένο.
        max_tokens: 2000,
        thinking: { type: 'adaptive' },
        output_config: { effort: 'medium' },
        // Αν το μοντέλο αρνηθεί για λόγους πολιτικής, το αίτημα συνεχίζει
        // αυτόματα σε εναλλακτικό μοντέλο αντί να μείνει ο χρήστης χωρίς απάντηση.
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
      const status = err?.status;
      if (status === 429) return json({ error: 'upstream_rate_limited' }, 429, env);
      return json({ error: 'upstream_error' }, 502, env);
    }

    if (response.stop_reason === 'refusal') return json({ error: 'refused' }, 422, env);

    let answer = (response.content || [])
      .filter(b => b.type === 'text')
      .map(b => b.text)
      .join('\n')
      .trim();

    if (!answer) return json({ error: 'empty_answer' }, 502, env);

    const callPro = answer.includes(PRO_TAG);
    answer = answer.split(PRO_TAG).join('').trim();

    return json({ answer, callPro }, 200, env);
  },
};
