#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ένθεση των 21 περιφερειακών συνταγών (παρτίδες 9-11).

Ξεχωριστό από το _insert.py, που αφορά τις παλιές παρτίδες και έχει δικούς
του ελέγχους πλήθους. Εδώ γίνονται όλα μαζί και με τη σωστή σειρά:

1. MEALS και MEAL_IMAGES στο index.html
2. αντιγραφή των εικόνων στο images/
3. συγχώνευση των γερμανικών στο lang/de.json
4. μενού «Καλεσμένοι» (P4/P3/P2)

Δεν γράφει τίποτα αν κάποιος έλεγχος αποτύχει.
Χρήση: python3 _insert2.py [--apply]
"""
import io, json, os, re, shutil, subprocess, sys

D     = os.path.dirname(os.path.abspath(__file__))
ROOT  = os.path.dirname(D)
HTML  = os.path.join(ROOT, 'index.html')
DEJ   = os.path.join(ROOT, 'lang', 'de.json')
IMGS  = os.path.join(D, 'images-new')
APPLY = '--apply' in sys.argv

FILES = ['batch9-nisia.js', 'batch10-kriti-ipeiros.js', 'batch11-mikrasiatika-voria.js']
DEF   = {'batch9-nisia.js': 'i18n/de-batch9.json',
         'batch10-kriti-ipeiros.js': 'i18n/de-batch10.json',
         'batch11-mikrasiatika-voria.js': 'i18n/de-batch11.json'}
EXPECTED = 21

# Μενού «Καλεσμένοι» — εγκεκριμένο από τον χρήστη
GUEST = {'P4': ['mastelo'],
         'P3': ['hunkiar_begenti', 'tas_kebap', 'bianco', 'savoro', 'louza'],
         'P2': ['giaprakia', 'biftekia_feta']}

def die(msg):
    sys.exit('ΣΦΑΛΜΑ: ' + msg)

# ── συλλογή ─────────────────────────────────────────────────────
blocks, ids = [], []
for f in FILES:
    txt = io.open(os.path.join(D, f), encoding='utf-8').read()
    body = re.sub(r'^//.*$', '', txt, flags=re.M).strip('\n').rstrip()
    while body.startswith('\n'):
        body = body[1:]
    found = re.findall(r'^  ([a-z_0-9]+):\{ing_en', body, re.M)
    if not found:
        die(f'το {f} δεν έχει συνταγές')
    ids += found
    blocks.append(f'\n  // ── {f} ──\n' + body)
print(f'Συλλέχθηκαν {len(ids)} συνταγές από {len(FILES)} αρχεία')
if len(ids) != EXPECTED:
    die(f'βρέθηκαν {len(ids)}, αναμένονταν {EXPECTED}')
if len(ids) != len(set(ids)):
    die('διπλά id: ' + str([i for i in set(ids) if ids.count(i) > 1]))

# ── εικόνες ─────────────────────────────────────────────────────
for i in ids:
    if not os.path.exists(os.path.join(IMGS, i + '.jpg')):
        die(f'λείπει η εικόνα {i}.jpg')
extra = [f[:-4] for f in os.listdir(IMGS) if f.endswith('.jpg') and f[:-4] not in ids]
if extra:
    die('αχρησιμοποίητες εικόνες: ' + ', '.join(extra))
print(f'Επαληθεύτηκαν {len(ids)} εικόνες')

# ── γερμανικά ───────────────────────────────────────────────────
de_new = {}
for f in FILES:
    de_new.update(json.load(io.open(os.path.join(D, DEF[f]), encoding='utf-8')))
if set(de_new) != set(ids):
    die('τα γερμανικά δεν ταιριάζουν με τις συνταγές')
print(f'Επαληθεύτηκαν {len(de_new)} γερμανικές μεταφράσεις')

s = io.open(HTML, encoding='utf-8').read()
before = len(s)

for i in ids:
    if re.search(r'\n  ' + i + r':\{', s):
        die(f'το id «{i}» υπάρχει ήδη στο index.html')

# ── 1. MEALS ────────────────────────────────────────────────────
m_end = s.index('\n};', s.index('const MEALS={'))
payload = ',' + ''.join(blocks).rstrip().rstrip(',')
if payload.count('{') != payload.count('}'):
    die('ανισορροπία αγκυλών στο payload')
if payload.count('[') != payload.count(']'):
    die('ανισορροπία τετράγωνων αγκυλών')
s = s[:m_end] + payload + s[m_end:]
print('1. MEALS: ok')

# ── 2. MEAL_IMAGES ──────────────────────────────────────────────
i_end = s.index('\n};', s.index('const MEAL_IMAGES={'))
lines = '\n'.join(f"  {i}:'images/{i}.jpg'," for i in ids)
s = s[:i_end] + '\n  // ── περιφερειακές συνταγές ──\n' + lines + s[i_end:]
print('2. MEAL_IMAGES: ok')

# ── 3. Μενού «Καλεσμένοι» ───────────────────────────────────────
for tier, items in GUEST.items():
    unknown = [x for x in items if x not in ids]
    if unknown:
        die(f'{tier}: άγνωστα id {unknown}')
    m = re.search(r'(const ' + tier + r'=\[)', s)
    if not m:
        die(f'δεν βρέθηκε ο πίνακας {tier}')
    ins = ''.join(f"'{x}'," for x in items)
    s = s[:m.end()] + ins + s[m.end():]
print('3. Μενού Καλεσμένων: ok  (' +
      ', '.join(f'{k}:{len(v)}' for k, v in GUEST.items()) + ')')

if not APPLY:
    print('\nΔοκιμή μόνο. Τρέξε με --apply για να γραφτούν οι αλλαγές.')
    sys.exit(0)

# ── εγγραφή ─────────────────────────────────────────────────────
io.open(HTML, 'w', encoding='utf-8').write(s)
print(f'\n✅ index.html: {before:,} → {len(s):,} χαρακτήρες (+{(len(s)-before)/1024:.0f} KB)')

for i in ids:
    shutil.copy2(os.path.join(IMGS, i + '.jpg'), os.path.join(ROOT, 'images', i + '.jpg'))
print(f'✅ Αντιγράφηκαν {len(ids)} εικόνες στο images/')

de = json.load(io.open(DEJ, encoding='utf-8'))
de['meals'].update(de_new)
io.open(DEJ, 'w', encoding='utf-8').write(
    json.dumps(de, ensure_ascii=False, indent=1) + '\n')
print(f'✅ lang/de.json: {len(de["meals"])} συνταγές')
