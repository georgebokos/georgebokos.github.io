# -*- coding: utf-8 -*-
"""Λεζάντα και hashtags για ανάρτηση συνταγής σε Reels / TikTok / Shorts.
Χρήση: python3 ads/captions.py <id_συνταγής>"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ΔΕΝ μπαίνει διεύθυνση στη λεζάντα. Μετρήθηκε σε 29 ημέρες και 55 βίντεο:
# 30.677 προβολές, 104 επισκέψεις προφίλ, ΜΗΔΕΝ κλικ σε σύνδεσμο. Στο TikTok
# οι λεζάντες δεν είναι κλικαρίσιμες — ο θεατής βλέπει μια τεράστια διεύθυνση
# που θα έπρεπε να πληκτρολογήσει, και δεν το κάνει ποτέ. Μένει η οδηγία που
# εκτελείται με το χέρι σε δύο δευτερόλεπτα.
CTA = 'Γράψε FoodDaily στο Google Play — δωρεάν'

BASE = ['#συνταγες','#ελληνικηκουζινα','#μαγειρικη','#φαγητο','#greekfood',
        '#σπιτικοφαγητο','#τιμαγειρευουμεσημερα','#fooddaily']

# Η πρώτη γραμμή είναι το ΜΟΝΟ που διαβάζεται πριν το «περισσότερα».
# Τα τρία βίντεο με τη μεγαλύτερη ολοκλήρωση ήταν και τα τρία ΕΡΩΤΗΣΗ ή
# προσωπική φράση — 52%, 48%, 42%. Τα γενικά «Ανακάλυψε το FoodDaily»
# έμειναν κάτω από 8%. Γι' αυτό η λεζάντα ξεκινά πάντα με ερώτηση.
ASK = {
 'meat':      'Πόσες φορές φέτος το έφαγες έξω ενώ μπορούσες να το κάνεις σπίτι;',
 'seafood':   'Φοβάσαι να μαγειρέψεις ψάρι; Δεν είσαι ο μόνος.',
 'pasta':     'Βαρέθηκες τα ίδια μακαρόνια κάθε βδομάδα;',
 'legumes':   'Θυμάσαι πότε έφαγες τελευταία φορά σπιτικά όσπρια;',
 'vegetables':'Λαδερό που δεν βαριέσαι — υπάρχει;',
 'soups':     'Κρυώνεις και δεν ξέρεις τι να βάλεις στην κατσαρόλα;',
 'salads':    'Σαλάτα που χορταίνει. Σου φαίνεται παράξενο;',
 'pites':     'Πίτα σπιτική χωρίς να πάθεις νευρικό κλονισμό;',
 'desserts':  'Γλυκό που δεν σου βγάζει την ψυχή. Ναι, υπάρχει.',
 'pizza':     'Πίτσα σπίτι που δεν ζηλεύει την ντελίβερι;',
 'sauces':    'Η σάλτσα κάνει τη διαφορά. Την κάνεις σωστά;',
}
# Στο τέλος μπαίνει ερώτηση που απαντιέται με μία λέξη: τα σχόλια είναι το
# φθηνότερο καύσιμο για να ξαναδείξει το TikTok το βίντεο.
POKE = {
 'meat':      'Εσύ πώς το κάνεις — κατσαρόλα ή φούρνο;',
 'seafood':   'Ποιο ψάρι φοβάσαι πιο πολύ;',
 'pasta':     'Ποια είναι η αγαπημένη σου μακαρονάδα;',
 'legumes':   'Φακές ή φασολάδα; Διάλεξε.',
 'vegetables':'Με φέτα ή χωρίς;',
 'soups':     'Αυγολέμονο ή κόκκινη;',
 'salads':    'Τι βάζεις εσύ μέσα που δεν βάζει κανείς;',
 'pites':     'Φύλλο έτοιμο ή σπιτικό; Πες την αλήθεια.',
 'desserts':  'Ζεστό ή από το ψυγείο;',
 'pizza':     'Ανανάς στην πίτσα: ναι ή όχι;',
 'sauces':    'Με τι τη συνοδεύεις;',
}
CAT = {'meat':['#κρεας','#κυριωςπιατο'],'seafood':['#θαλασσινα','#ψαρι'],
       'pasta':['#ζυμαρικα','#μακαρονια'],'legumes':['#οσπρια','#νηστισιμο'],
       'vegetables':['#λαχανικα','#χορτοφαγικο'],'soups':['#σουπα','#ζεστοπιατο'],
       'salads':['#σαλατα'],'pites':['#πιτα','#ζυμη'],'desserts':['#γλυκο','#ζαχαροπλαστικη'],
       'pizza':['#πιτσα'],'sauces':['#σαλτσα']}

def load(rid):
    js = r'''
const fs=require('fs'),vm=require('vm');
const b=fs.readFileSync(process.argv[1],'utf8').match(/<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/)[1];
const g=(o,c)=>{const i=b.indexOf(o),j=b.indexOf(c,i);return b.slice(i,j+c.length)};
const ctx={};vm.createContext(ctx);new vm.Script(g('const MEALS={','\n};')).runInContext(ctx);
const M=vm.runInContext('MEALS',ctx);
if(!M[process.argv[2]]){console.error('x');process.exit(1)}
console.log(JSON.stringify(M[process.argv[2]]));'''
    p = subprocess.run(['node','-e',js,os.path.join(ROOT,'index.html'),rid],
                       capture_output=True, text=True)
    if p.returncode: sys.exit('Δεν βρέθηκε: '+rid)
    return json.loads(p.stdout)

def total_meals():
    """Πόσες συνταγές έχει η εφαρμογή αυτή τη στιγμή.

    Ο αριθμός ΔΕΝ γράφεται με το χέρι: η λεζάντα λέει «άλλες N», δηλαδή όλες
    εκτός από αυτή του βίντεο, και ένα χειρόγραφο νούμερο ξεχνιέται και μένει
    λάθος κατά ένα για πάντα."""
    js = (r'const fs=require("fs"),vm=require("vm");'
          r'const b=fs.readFileSync(process.argv[1],"utf8")'
          r'.match(/<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/)[1];'
          r'const i=b.indexOf("const MEALS={"),j=b.indexOf("\n};",i);'
          r'const c={};vm.createContext(c);new vm.Script(b.slice(i,j+3)).runInContext(c);'
          r'console.log(Object.keys(vm.runInContext("MEALS",c)).length);')
    p = subprocess.run(['node','-e',js,os.path.join(ROOT,'index.html')],
                       capture_output=True, text=True)
    return int(p.stdout.strip()) if p.returncode == 0 else 0

def caption(rid):
    m = load(rid)
    tags = BASE + CAT.get(m['cats'][0], [])
    cps = (m.get('cps') or m.get('cost') or '').strip()
    # Η πρώτη γραμμή είναι η μόνη που φαίνεται πριν το «περισσότερα», και
    # επαναλαμβάνει το hook του βίντεο: αν η λεζάντα λέει άλλο πράγμα από την
    # εικόνα, το μήνυμα διχάζεται.
    from reel import pick_hook
    lbl, big, small = pick_hook(m, m['ing'], m['steps'], rid, True)
    head = f'{lbl}: {big} {small}' if lbl else f'{big} {small}'
    rest = max(0, total_meals() - 1)
    c = m['cats'][0]
    ask = ASK.get(c, 'Τι θα φάμε σήμερα; Η πιο κουραστική ερώτηση της ημέρας.')
    poke = POKE.get(c, 'Εσύ πώς το φτιάχνεις;')
    return f"""{ask}

{m['n']} — {head.lower()}
⏱ {m['time']}′  ·  🔥 {m['cal']} θερμίδες  ·  💰 {cps} τη μερίδα

Υλικά και βήματα, μαζί με άλλες {rest} ελληνικές συνταγές και 12 προτάσεις
κάθε μέρα. 👉 {poke}

📲 {CTA}

{' '.join(tags)}"""

if __name__ == '__main__':
    print(caption(sys.argv[1] if len(sys.argv) > 1 else 'moussaka'))
