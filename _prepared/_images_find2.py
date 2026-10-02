#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Εύρεση εικόνας ανά συνταγή, με σειρά αξιοπιστίας.

Η ελεύθερη αναζήτηση λέξεων στο Commons επιστρέφει θόρυβο: για «Πιταρούδια
Ρόδου» γύρισε φωτογραφίες του λιμανιού, και για «Μπιάνκο Κέρκυρας» ναούς της
Αιγύπτου. Τα ονόματα αρχείων και οι περιγραφές απλώς περιέχουν τις λέξεις.

Εδώ η αναζήτηση γίνεται με τρεις πηγές, από την πιο αξιόπιστη προς την πιο
χαλαρή, και κάθε υποψήφιο περνά από φίλτρο ονόματος:

1. **Άρθρο Wikipedia** (ελληνικά, μετά αγγλικά) → η κύρια εικόνα του άρθρου.
   Αν υπάρχει άρθρο για το πιάτο, η εικόνα του δείχνει το πιάτο.
2. **Κατηγορία Commons** → τα αρχεία μέσα της. Οι κατηγορίες είναι
   επιμελημένες από ανθρώπους, όχι αποτέλεσμα αναζήτησης.
3. **Αναζήτηση αρχείων**, αλλά μόνο όσα έχουν τη λέξη-κλειδί στον τίτλο.

Χρήση: python3 _images_find2.py terms.json out.json
"""
import json, sys, time, urllib.parse, urllib.request

UA = 'FoodDailyRecipeImageCheck/1.0 (https://georgebokos.github.io)'
OK_PREFIX = ('cc0', 'cc-zero', 'public domain', 'pd-', 'cc-by-1', 'cc-by-2',
             'cc-by-3', 'cc-by-4', 'cc-by-sa')
BAD_PART  = ('-nc', 'nc-', 'noncommercial', '-nd', 'nd-', 'noderiv', 'fair use')
_last = [0.0]

def api(host, params, tries=6):
    params.update({'action': 'query', 'format': 'json'})
    url = f'https://{host}/w/api.php?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    for k in range(tries):
        gap = 4.0 - (time.time() - _last[0])
        if gap > 0: time.sleep(gap)
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                _last[0] = time.time()
                return json.load(r)
        except urllib.error.HTTPError as e:
            _last[0] = time.time()
            if e.code != 429 or k == tries-1: raise
            time.sleep(12*(k+1))

def licence_ok(l):
    l = (l or '').lower()
    return not any(b in l for b in BAD_PART) and any(l.startswith(p) for p in OK_PREFIX)

def safe(fn, *a, **kw):
    """Ένα 429 σε ένα πιάτο δεν πρέπει να ακυρώνει τα υπόλοιπα 21."""
    try:
        return fn(*a, **kw)
    except Exception as e:
        print(f'   ! {fn.__name__}: {e}')
        return []

def info(titles):
    """Άδεια και διαστάσεις για αρχεία του Commons."""
    out = []
    for i in range(0, len(titles), 20):
        try:
            d = api('commons.wikimedia.org',
                    {'titles': '|'.join(titles[i:i+20]), 'prop': 'imageinfo',
                     'iiprop': 'url|size|extmetadata',
                     'iiextmetadatafilter': 'LicenseShortName'})
        except Exception as e:
            print(f'   ! imageinfo: {e}'); continue
        for p in (d.get('query', {}).get('pages') or {}).values():
            ii = (p.get('imageinfo') or [{}])[0]
            lic = ((ii.get('extmetadata') or {}).get('LicenseShortName') or {}).get('value', '')
            if not licence_ok(lic) or ii.get('width', 0) < 640: continue
            out.append({'title': p['title'], 'lic': lic, 'w': ii['width'],
                        'h': ii['height'], 'url': ii['url'], 'src': ''})
    return out

def from_wikipedia(host, title):
    d = api(host, {'titles': title, 'prop': 'pageimages', 'piprop': 'original'})
    out = []
    for p in (d.get('query', {}).get('pages') or {}).values():
        o = (p.get('original') or {}).get('source')
        if o:
            f = 'File:' + urllib.parse.unquote(o.rsplit('/', 1)[-1])
            out.append(f)
    return out

def wiki_search(host, term):
    d = api(host, {'list': 'search', 'srsearch': term, 'srlimit': 3})
    return [r['title'] for r in d.get('query', {}).get('search', [])]

def from_category(cat):
    d = api('commons.wikimedia.org',
            {'list': 'categorymembers', 'cmtitle': 'Category:'+cat,
             'cmtype': 'file', 'cmlimit': 25})
    return [m['title'] for m in d.get('query', {}).get('categorymembers', [])]

def cat_search(term):
    d = api('commons.wikimedia.org',
            {'list': 'search', 'srsearch': term, 'srnamespace': 14, 'srlimit': 3})
    return [r['title'].replace('Category:', '') for r in d.get('query', {}).get('search', [])]

def find(queries, keys):
    """keys: λέξεις που ΠΡΕΠΕΙ να υπάρχουν στον τίτλο του αρχείου."""
    cand, seen = [], set()
    def add(files, src):
        for f in files:
            if f not in seen:
                seen.add(f); cand.append((f, src))
    for q in queries:
        for host in ('el.wikipedia.org', 'en.wikipedia.org'):
            for t in safe(wiki_search, host, q)[:2]:
                add(safe(from_wikipedia, host, t), f'wiki:{host}:{t}')
        for c in safe(cat_search, q):
            add(safe(from_category, c), f'cat:{c}')
    # Φίλτρο ονόματος: κόβει τα ψευδώς θετικά της αναζήτησης
    kl = [k.lower() for k in keys]
    named = [c for c in cand if any(k in c[0].lower() for k in kl)]
    pool = named or cand
    res = info([c[0] for c in pool])
    src = dict(pool)
    for r in res: r['src'] = src.get(r['title'], '')
    return res

if __name__ == '__main__':
    spec = json.load(open(sys.argv[1], encoding='utf-8'))
    out = {}
    for key, cfg in spec.items():
        print(f'\n=== {key}')
        r = safe(find, cfg['q'], cfg['keys'])
        out[key] = r
        json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        if not r: print('  ✗ καμία')
        for x in r[:6]:
            print(f"  ✓ {x['lic']:<16} {x['w']}×{x['h']}  {x['title']}  [{x['src']}]")
    json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    miss = [k for k, v in out.items() if not v]
    print(f'\nΣΥΝΟΛΟ: {len(out)-len(miss)}/{len(out)}')
    if miss: print('ΧΩΡΙΣ: ' + ', '.join(miss))
