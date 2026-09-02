# -*- coding: utf-8 -*-
"""Λεζάντα και hashtags για ανάρτηση συνταγής σε Reels / TikTok / Shorts.
Χρήση: python3 ads/captions.py <id_συνταγής>"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINK = 'fooddaily.github.io'

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

def caption(rid):
    m = load(rid)
    tags = BASE + CAT.get(m['cats'][0], [])
    cps = (m.get('cps') or m.get('cost') or '').strip()
    return f"""{m['n']} 🍽️

⏱ {m['time']}′  ·  🔥 {m['cal']} θερμίδες  ·  👥 {m['srv']} μερίδες  ·  💰 {cps} η μερίδα

Τα υλικά και όλα τα βήματα βήμα-βήμα είναι στην εφαρμογή.
Μαζί με άλλες 375 ελληνικές συνταγές — και μία πρόταση φαγητού κάθε μέρα.

📲 {LINK}
(σύνδεσμος και στο προφίλ)

{' '.join(tags)}"""

if __name__ == '__main__':
    print(caption(sys.argv[1] if len(sys.argv) > 1 else 'moussaka'))
