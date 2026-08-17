#!/usr/bin/env python3
"""Ένθεση των προετοιμασμένων συνταγών στο index.html.
Δεν γράφει τίποτα αν κάποιος έλεγχος αποτύχει.
Χρήση: python3 _insert.py [--all]"""
import os, re, sys, io

D = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(D) + '/'
HTML = ROOT + 'index.html'
ALL = '--all' in sys.argv

# Φάση Α: μόνο οι 56 νέες. Τα batch8* θέλουν πρώτα αφαίρεση από το SWEETS.
PAT = re.compile(r'^batch.*\.js$' if ALL else r'^batch([1-4]|[567]m).*\.js$')
files = sorted(f for f in os.listdir(D) if PAT.match(f))

# ── συλλογή των μπλοκ κειμένου, αυτούσια ────────────────────────
blocks, ids = [], []
for f in files:
    txt = io.open(os.path.join(D, f), encoding='utf-8').read()
    body = re.sub(r'^//.*$', '', txt, flags=re.M)
    # Καθαρίζουμε μόνο κενές γραμμές στις άκρες, ΧΩΡΙΣ να χαθεί η εσοχή
    # της πρώτης συνταγής — αλλιώς το regex από κάτω δεν την βρίσκει.
    body = body.strip('\n')
    while body.startswith('\n'): body = body[1:]
    body = body.rstrip()
    if not body.strip():
        sys.exit(f'ΣΦΑΛΜΑ: το {f} είναι κενό')
    found = re.findall(r'^  ([a-z_0-9]+):\{ing_en', body, re.M)
    if not found:
        sys.exit(f'ΣΦΑΛΜΑ: το {f} δεν έχει συνταγές')
    ids += found
    blocks.append(f'\n  // ── {f} ──\n' + body)
print(f'Συλλέχθηκαν {len(ids)} συνταγές από {len(files)} αρχεία')
EXPECTED = 82 if ALL else 56
if len(ids) != EXPECTED:
    sys.exit(f'ΣΦΑΛΜΑ: βρέθηκαν {len(ids)} συνταγές, αναμένονταν {EXPECTED}')

if len(ids) != len(set(ids)):
    dup = [i for i in set(ids) if ids.count(i) > 1]
    sys.exit(f'ΣΦΑΛΜΑ: διπλά id {dup}')

# ── εικόνες ─────────────────────────────────────────────────────
imgmap = dict(re.findall(r"(\w+):'(images/[\w.\-]+)'",
                         io.open(os.path.join(D, 'meal-images.txt'), encoding='utf-8').read()))
img_lines = []
for i in ids:
    p = imgmap.get(i)
    if not p:
        sys.exit(f'ΣΦΑΛΜΑ: λείπει εικόνα για {i}')
    if not os.path.exists(ROOT + p):
        sys.exit(f'ΣΦΑΛΜΑ: δεν υπάρχει το αρχείο {p}')
    img_lines.append(f"  {i}:'{p}',")
print(f'Επαληθεύτηκαν {len(img_lines)} εικόνες στον δίσκο')

s = io.open(HTML, encoding='utf-8').read()
before = len(s)

# ── έλεγχος ότι κανένα id δεν υπάρχει ήδη ───────────────────────
for i in ids:
    if re.search(r'\n  ' + i + r':\{', s):
        sys.exit(f'ΣΦΑΛΜΑ: το id «{i}» υπάρχει ήδη στο index.html')

# ── 1. ένθεση στο MEALS, πριν το κλείσιμο ───────────────────────
m_start = s.index('const MEALS={')
m_end = s.index('\n};', m_start)
payload = ',' + ''.join(blocks).rstrip().rstrip(',')
s = s[:m_end] + payload + s[m_end:]
print('1. Ένθεση στο MEALS: ok')

# ── 2. ένθεση στο MEAL_IMAGES ───────────────────────────────────
i_start = s.index('const MEAL_IMAGES={')
i_end = s.index('\n};', i_start)
s = s[:i_end] + '\n  // ── νέες συνταγές ──\n' + '\n'.join(img_lines).rstrip(',') + s[i_end:]
print('2. Ένθεση στο MEAL_IMAGES: ok')

# ── 3. στοιχειώδης έλεγχος ισορροπίας αγκυλών στο payload ───────
if payload.count('{') != payload.count('}'):
    sys.exit(f'ΣΦΑΛΜΑ: ανισορροπία αγκυλών {payload.count("{")} vs {payload.count("}")}')
if payload.count('[') != payload.count(']'):
    sys.exit('ΣΦΑΛΜΑ: ανισορροπία τετράγωνων αγκυλών')
print('3. Ισορροπία αγκυλών: ok')

io.open(HTML, 'w', encoding='utf-8').write(s)
print(f'\n✅ Γράφτηκε το index.html: {before:,} → {len(s):,} χαρακτήρες '
      f'(+{(len(s)-before)/1024:.0f} KB)')
