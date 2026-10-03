#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ενημερώνει το πλήθος συνταγών όπου είναι γραμμένο με το χέρι.

Στην εφαρμογή ο αριθμός υπολογίζεται δυναμικά και δεν χρειάζεται τίποτα.
Έξω από αυτήν όμως — στο install.html, στις κάρτες του Play, στα βίντεο και
στα κείμενα προώθησης — είναι γραμμένος κυριολεκτικά, και μένει πίσω κάθε
φορά που προστίθενται συνταγές.

Το σωστό πλήθος διαβάζεται από το ίδιο το index.html, ώστε να μην μπορεί να
γραφτεί λάθος νούμερο.

Χρήση:  python3 _count_update.py            (δείχνει τι θα άλλαζε)
        python3 _count_update.py --apply    (γράφει τις αλλαγές)
"""
import io, json, os, re, subprocess, sys

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPLY = '--apply' in sys.argv

# Αρχεία με χειρόγραφο αριθμό. Λείπουν σκόπιμα δύο: το index.html, όπου ο
# αριθμός είναι ήδη δυναμικός, και το ads/captions.py, που λέει «άλλες N»
# (όλες πλην αυτής του βίντεο) και τον υπολογίζει πλέον μόνο του.
TARGETS = ['install.html', 'CLAUDE.md',
           'ads/ORGANIC.md', 'ads/reels/QUEUE.md', 'ads/reels/ΚΕΙΜΕΝΑ.md',
           'ads/reels/ΤΗΛΕΦΩΝΟ.md', 'ads/call.py', 'ads/reel.py', 'ads/images.py',
           'ads/video.py', 'ads/text_assets.py', 'ads/fb_images.py',
           'store/share_card.py', 'store/feature_graphic.py', 'store/og_preview.py']

def real_count():
    """Το πλήθος όπως το βλέπει η ίδια η εφαρμογή."""
    js = r'''
const fs=require("fs"),vm=require("vm");
const b=fs.readFileSync(process.argv[1],"utf8")
        .match(/<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/)[1];
const i=b.indexOf("const MEALS={"), j=b.indexOf("\n};",i);
const ctx={};vm.createContext(ctx);new vm.Script(b.slice(i,j+3)).runInContext(ctx);
console.log(Object.keys(vm.runInContext("MEALS",ctx)).length);'''
    p = subprocess.run(['node','-e',js,os.path.join(ROOT,'index.html')],
                       capture_output=True, text=True)
    if p.returncode:
        sys.exit('ΣΦΑΛΜΑ: δεν διαβάστηκε το MEALS\n' + p.stderr)
    return int(p.stdout.strip())

def main():
    n = real_count()
    print(f'Πραγματικό πλήθος συνταγών: {n}\n')
    # Κάθε τριψήφιος αριθμός 300-499 δίπλα σε «συνταγές/recipes/Rezepte» ή μόνος
    # του σε φράση πλήθους. Στενό επίτηδες: ευρύτερο μοτίβο θα χτυπούσε
    # θερμίδες, γραμμάρια και χρόνους.
    pat = re.compile(r'\b([34]\d\d)\b(?=\+?\s*(?:ελληνικ[έε]ς\s+)?(?:συνταγ|recipe|Rezept))')
    total = 0
    for rel in TARGETS:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            print(f'  — {rel}: δεν υπάρχει'); continue
        s = io.open(p, encoding='utf-8').read()
        hits = {m.group(1) for m in pat.finditer(s)}
        stale = {h for h in hits if h != str(n)}
        if not stale:
            print(f'  ✓ {rel}: ενημερωμένο'); continue
        new = pat.sub(lambda m: str(n), s)
        cnt = sum(s.count(h) for h in stale)
        print(f'  {"→" if APPLY else "·"} {rel}: {", ".join(sorted(stale))} → {n}')
        total += 1
        if APPLY:
            io.open(p, 'w', encoding='utf-8').write(new)
    print(f'\n{"Ενημερώθηκαν" if APPLY else "Θα ενημερώνονταν"} {total} αρχεία')
    if not APPLY and total:
        print('Τρέξε ξανά με --apply για να γραφτούν.')

if __name__ == '__main__':
    main()
