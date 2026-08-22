# -*- coding: utf-8 -*-
"""Κείμενα διαφημίσεων Google Ads (App campaign).
Τίτλοι ≤30 χαρακτήρες, περιγραφές ≤90. Το σενάριο σταματά σε υπέρβαση."""
import io, sys

A = {
'el': {
 'headlines': [
   'Τι μαγειρεύουμε σήμερα;',
   '376 ελληνικές συνταγές',
   'Μαγείρεψε ό,τι έχεις',
   'Πόσο κοστίζει η μερίδα;',
   'Μια πρόταση κάθε μέρα',
 ],
 'descriptions': [
   'Σταμάτα να σκέφτεσαι τι θα φάτε. Μια πρόταση κάθε μέρα, με φωτογραφία και κόστος.',
   'Γράψε τι έχεις στο ψυγείο και βρες τι μπορείς να μαγειρέψεις τώρα.',
   'Μουσακάς, γεμιστά, φασολάδα. Βήμα βήμα, με λίστα αγορών και κόστος ανά άτομο.',
   'Μενού για καλεσμένους, εορτές και νηστεία. Δουλεύει και χωρίς ίντερνετ.',
   'Θερμίδες, χρόνος και κόστος σε κάθε συνταγή. Χωρίς διαφημίσεις.',
 ]},
'en': {
 'headlines': [
   'What to cook tonight?',
   '376 Greek recipes',
   'Cook what you have',
   'See the cost per serving',
   'One idea, every day',
 ],
 'descriptions': [
   'Stop deciding what to eat. One dish a day, with a photo, the time and the cost.',
   'Type what is in your fridge and find what you can cook right now.',
   'Moussaka, pastitsio, bean soup. Step by step, with a shopping list.',
   'Menus for guests, feast days and fasting. Works with no connection.',
   'Calories, time and cost on every recipe. No ads, no account.',
 ]},
}
LIM = {'headlines': 30, 'descriptions': 90}
ok = True
out = []
for lang, d in A.items():
    out.append(f'══ {lang.upper()} ══')
    for field in ('headlines', 'descriptions'):
        out.append(f'\n{"ΤΙΤΛΟΙ" if field=="headlines" else "ΠΕΡΙΓΡΑΦΕΣ"} (μέγιστο {LIM[field]})')
        for t in d[field]:
            n = len(t); bad = n > LIM[field]; ok &= not bad
            out.append(f'  [{n:2d}] {t}' + ('   ❌ ΥΠΕΡΒΑΣΗ' if bad else ''))
    out.append('')
txt = '\n'.join(out)
print(txt)
io.open('ads/text-assets.txt', 'w', encoding='utf-8').write(txt)
if not ok:
    sys.exit('❌ υπάρχουν υπερβάσεις — διόρθωσέ τες πριν τα ανεβάσεις')
print('✅ όλα εντός ορίων → ads/text-assets.txt')
