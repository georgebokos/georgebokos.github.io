#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Αναζήτηση εικόνων στο Wikimedia Commons για τις νέες συνταγές.

Δεν κατεβάζει τίποτα — μόνο αναφέρει τι υπάρχει και με ποια άδεια, ώστε να
αποφασιστεί ποιες συνταγές έχουν εικόνα πριν γραφτεί μία γραμμή συνταγής.

Δέχονται **μόνο** άδειες που επιτρέπουν εμπορική χρήση και παραγώγων:
public domain, CC0, CC BY, CC BY-SA. Οτιδήποτε NC, ND ή «fair use» κόβεται.
"""
import json, sys, urllib.parse, urllib.request

API = 'https://commons.wikimedia.org/w/api.php'
UA  = 'FoodDailyRecipeImageCheck/1.0 (https://georgebokos.github.io)'

OK_PREFIX = ('cc0', 'cc-zero', 'public domain', 'pd-', 'cc-by-1', 'cc-by-2',
             'cc-by-3', 'cc-by-4', 'cc-by-sa')
BAD_PART  = ('-nc', 'nc-', 'noncommercial', '-nd', 'nd-', 'noderiv', 'fair use')

def api(params):
    params.update({'action': 'query', 'format': 'json'})
    url = API + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)

def licence_ok(lic):
    l = (lic or '').lower()
    if any(b in l for b in BAD_PART):
        return False
    return any(l.startswith(p) for p in OK_PREFIX)

def search(term, limit=8):
    """Επιστρέφει [(τίτλος, άδεια, πλάτος, ύψος, url)] μόνο με αποδεκτή άδεια."""
    try:
        d = api({'generator': 'search', 'gsrsearch': f'filetype:bitmap {term}',
                 'gsrnamespace': 6, 'gsrlimit': limit,
                 'prop': 'imageinfo', 'iiprop': 'url|size|extmetadata',
                 'iiextmetadatafilter': 'LicenseShortName|License'})
    except Exception as e:
        print(f'  ! σφάλμα δικτύου: {e}')
        return []
    out = []
    for p in (d.get('query', {}).get('pages') or {}).values():
        ii = (p.get('imageinfo') or [{}])[0]
        meta = ii.get('extmetadata') or {}
        lic = (meta.get('LicenseShortName', {}).get('value')
               or meta.get('License', {}).get('value') or '')
        if not licence_ok(lic):
            continue
        if ii.get('width', 0) < 640:          # πολύ μικρή για 1000px πλάτος
            continue
        out.append((p['title'], lic, ii.get('width'), ii.get('height'), ii.get('url')))
    return out

if __name__ == '__main__':
    terms = json.load(open(sys.argv[1], encoding='utf-8'))
    found = {}
    for key, queries in terms.items():
        print(f'\n=== {key}')
        hits = []
        for q in queries:
            for h in search(q):
                if h[0] not in [x[0] for x in hits]:
                    hits.append(h)
        if not hits:
            print('  ✗ ΚΑΜΙΑ ελεύθερη εικόνα')
        for t, lic, w, h, u in hits[:6]:
            print(f'  ✓ {lic:<18} {w}×{h}  {t}')
        found[key] = [{'title': t, 'lic': l, 'w': w, 'h': h, 'url': u}
                      for t, l, w, h, u in hits]
    json.dump(found, open(sys.argv[2], 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    miss = [k for k, v in found.items() if not v]
    print(f'\nΣΥΝΟΛΟ: {len(found)-len(miss)}/{len(found)} με εικόνα')
    if miss:
        print('ΧΩΡΙΣ ΕΙΚΟΝΑ: ' + ', '.join(miss))
