# -*- coding: utf-8 -*-
"""Λεζάντα και hashtags για ανάρτηση συνταγής σε Reels / TikTok / Shorts.
Χρήση: python3 ads/captions.py <id_συνταγής>"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Απευθείας η σελίδα του Google Play, όχι το site: ο θεατής πρέπει να
# καταλήγει στην εγκατάσταση με ένα βήμα, όχι σε ενδιάμεση σελίδα.
LINK = 'play.google.com/store/apps/details?id=com.fooddaily.app'

BASE = ['#συνταγες','#ελληνικηκουζινα','#μαγειρικη','#φαγητο','#greekfood',
        '#σπιτικοφαγητο','#τιμαγειρευουμεσημερα','#fooddaily']
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
    return f"""{head} — {m['n']} 🍽️

⏱ {m['time']}′  ·  🔥 {m['cal']} θερμίδες  ·  👥 {m['srv']} μερίδες  ·  💰 κόστος υλικών {cps}/μερίδα

Το φτιάχνεις μόνος σου — τα υλικά και όλα τα βήματα είναι στην εφαρμογή.
Μαζί με άλλες {rest} ελληνικές συνταγές — και μία πρόταση φαγητού κάθε μέρα.

📲 {LINK}
(σύνδεσμος και στο προφίλ)

{' '.join(tags)}"""

if __name__ == '__main__':
    print(caption(sys.argv[1] if len(sys.argv) > 1 else 'moussaka'))
