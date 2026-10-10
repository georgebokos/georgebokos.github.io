# -*- coding: utf-8 -*-
"""Διαφημίσεις Facebook — φτιαγμένες για πληρωμένη προβολή, όχι για ανάρτηση.

Διαφέρουν από το `ads/feature_ads.py`: εκεί ο αναγνώστης έχει ήδη σταματήσει
και διαβάζει. Εδώ ο θεατής κυλάει το feed και έχει **ένα δευτερόλεπτο**. Γι'
αυτό κάθε σχέδιο έχει ΜΙΑ μεγάλη υπόσχεση που διαβάζεται χωρίς προσπάθεια, και
οι λειτουργίες έρχονται από κάτω — ποτέ πρώτες.

Τέσσερις προσεγγίσεις, ώστε να διαλέξει ο χρήστης:
  1  Η ΕΡΩΤΗΣΗ   — «Τι θα φάμε σήμερα;» και η απάντηση. Ελάχιστες λέξεις.
  2  ΤΑ ΝΟΥΜΕΡΑ   — 397 / 12 / 3 / 0€. Διαβάζονται χωρίς ανάγνωση.
  3  Η ΟΘΟΝΗ      — ένα όφελος που δεν το έχει κανείς: η οθόνη δεν σβήνει.
  4  Η ΜΕΡΑ ΣΟΥ   — από την ιδέα στο τραπέζι, σε τέσσερα βήματα.

Χρήση:  python3 ads/fb_ad.py [el|en] [1 2 3 4]
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_ads import (REST, N, LANGS, FB, FR, CREAM, WARM, GOLD, BRICK, INK,
                         PANEL, IMGS, emoji, photo, wrap, fit, badge, logo)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, 'ads', 'fb-ads')
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1350          # 4:5 — το μεγαλύτερο ύψος που δέχεται το feed
PAD  = 64

T = {
 'el': {
  'q1': '«Τι θα φάμε',  'q2': 'σήμερα;»',
  'ans': '12 απαντήσεις. Κάθε πρωί.',
  'three': [('🛒', 'Λίστα αγορών με ένα κλικ'),
            ('🍳', 'Η οθόνη δεν σβήνει ενώ μαγειρεύεις'),
            ('📴', f'{N} συνταγές, και χωρίς ίντερνετ')],
  'nums_h': 'Όλη η κουζίνα\nστο κινητό σου',
  'nums': [(str(N), 'ελληνικές\nσυνταγές'), ('12', 'προτάσεις\nκάθε μέρα'),
           ('3', 'γλώσσες'), ('0€', 'για πάντα')],
  'scr_h1': 'Τα χέρια σου είναι λερωμένα.',
  'scr_h2': 'Η οθόνη δεν σβήνει.',
  'scr_sub': 'Cook Mode: βήμα-βήμα, με χρονόμετρο που χτυπάει μόνο του',
  'scr_side': [('🔔', '12 προτάσεις τη μέρα'), ('🛒', 'Λίστα αγορών'),
               ('⏱️', 'Χρονόμετρο στο βήμα'), ('🧊', 'Τι έχεις στο ψυγείο')],
  'day_h': 'Από την ιδέα\nστο τραπέζι',
  'day': [('07:30', 'Σου προτείνει 12 πιάτα', 'kotopoulo'),
          ('18:00', 'Σου φτιάχνει τη λίστα', 'horiatiki'),
          ('19:15', 'Σε οδηγεί βήμα-βήμα', 'moussaka'),
          ('20:00', 'Και το μοιράζεσαι', 'baklava')],
  'cta': 'Δωρεάν στο Google Play',
  'langs_lbl': 'Ελληνικά · English · Deutsch',
  'more': 'Και ακόμα',
 },
 'en': {
  'q1': '"What are we', 'q2': 'eating today?"',
  'ans': '12 answers. Every morning.',
  'three': [('🛒', 'Shopping list in one tap'),
            ('🍳', 'The screen stays on while you cook'),
            ('📴', f'{N} recipes, and no internet needed')],
  'nums_h': 'The whole kitchen\nin your pocket',
  'nums': [(str(N), 'Greek\nrecipes'), ('12', 'ideas\nevery day'),
           ('3', 'languages'), ('0€', 'forever')],
  'scr_h1': 'Your hands are covered in flour.',
  'scr_h2': 'The screen stays on.',
  'scr_sub': 'Cook Mode: step by step, with a timer that rings by itself',
  'scr_side': [('🔔', '12 ideas a day'), ('🛒', 'Shopping list'),
               ('⏱️', 'Timer on each step'), ('🧊', "What's in the fridge")],
  'day_h': 'From the idea\nto the table',
  'day': [('07:30', 'It suggests 12 dishes', 'kotopoulo'),
          ('18:00', 'It builds your list', 'horiatiki'),
          ('19:15', 'It walks you through it', 'moussaka'),
          ('20:00', 'And you share it', 'baklava')],
  'cta': 'Free on Google Play',
  'langs_lbl': 'Ελληνικά · English · Deutsch',
  'more': 'Plus',
 },
}

# --- κοινά -----------------------------------------------------------------
def cover(rid, w, h, dy=0.5):
    im = Image.open(os.path.join(ROOT, IMGS[rid])).convert('RGB')
    r = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    x = (im.width - w) // 2
    y = round((im.height - h) * dy)
    return im.crop((x, y, x + w, y + h))

def vgrad(im, stops):
    """Σκοτείνιασμα κατά ζώνες: [(y, alpha), ...] με γραμμική παρεμβολή."""
    g = Image.new('L', (1, im.height)); px = g.load()
    for y in range(im.height):
        a = stops[0][1]
        for (y0, a0), (y1, a1) in zip(stops, stops[1:]):
            if y0 <= y <= y1:
                a = a0 + (a1 - a0) * (y - y0) / max(1, y1 - y0); break
            if y > y1: a = a1
        px[0, y] = round(255 * a)
    return Image.composite(Image.new('RGB', im.size, INK), im, g.resize(im.size))

def brand(im, lang, y=56, light=True):
    d = ImageDraw.Draw(im)
    L = logo(84); im.paste(L, (PAD, y), L)
    d.text((PAD + 104, y + 2), 'FoodDaily', font=ImageFont.truetype(FB, 44),
           fill=CREAM if light else INK)
    d.text((PAD + 106, y + 52), T[lang]['langs_lbl'], font=ImageFont.truetype(FB, 25), fill=GOLD)
    return y + 96

def cta(im, y, lang, center=False, dark_strip=False):
    d = ImageDraw.Draw(im)
    if dark_strip:
        d.rectangle([0, y - 28, W, H], fill=INK)
    gp = badge(300)
    f = ImageFont.truetype(FB, 33)
    tw = d.textlength(T[lang]['cta'], font=f)
    x = round((W - (gp.width + 26 + tw)) / 2) if center else PAD
    im.paste(gp, (x, y), gp)
    d.text((x + gp.width + 26, y + (gp.height - 42) // 2), T[lang]['cta'], font=f, fill=WARM)

def save(im, name, lang):
    p = os.path.join(OUT, f'fb-{name}-{lang}.png')
    im.save(p, 'PNG', optimize=True)
    print(f'  ✓ fb-{name}-{lang}.png  {im.width}×{im.height}  {os.path.getsize(p)//1024} KB')

# --- 1 · Η ΕΡΩΤΗΣΗ ---------------------------------------------------------
def ad1(lang):
    t = T[lang]
    im = vgrad(cover('giouvetsi', W, H, .45),
               [(0, .72), (380, .34), (640, .40), (900, .88), (H, .96)])
    d = ImageDraw.Draw(im)
    brand(im, lang)

    # Η ερώτηση είναι ο λόγος που θα σταματήσει κάποιος. Παίρνει όλο τον χώρο.
    f_q = ImageFont.truetype(FB, 96)
    y = 210
    for ln in (t['q1'], t['q2']):
        d.text((PAD, y), ln, font=f_q, fill=CREAM); y += 108

    d.line([PAD, y + 26, PAD + 150, y + 26], fill=GOLD, width=7)
    d.text((PAD, y + 62), t['ans'], font=fit(d, t['ans'], W - PAD * 2, 62), fill=GOLD)

    yy = 952
    for e, txt in t['three']:
        ic = emoji(e, 46); im.paste(ic, (PAD, yy - 6), ic)
        d.text((PAD + 68, yy), txt, font=fit(d, txt, W - PAD * 2 - 80, 36, 24, bold=False),
               fill=CREAM)
        yy += 70
    cta(im, 1212, lang)
    save(im, '1-erotisi', lang)

# --- 2 · ΤΑ ΝΟΥΜΕΡΑ --------------------------------------------------------
def ad2(lang):
    t = T[lang]
    im = Image.new('RGB', (W, H), INK)
    band = 330
    im.paste(vgrad(cover('souvlakia', W, band, .5),
                   [(0, .50), (band, .92)]), (0, 0))
    d = ImageDraw.Draw(im)
    brand(im, lang)
    y = 196
    for ln in t['nums_h'].split('\n'):
        d.text((PAD, y), ln, font=ImageFont.truetype(FB, 60), fill=CREAM); y += 70

    # Τέσσερα νούμερα. Το μάτι τα πιάνει χωρίς να διαβάσει λέξη — γι' αυτό
    # είναι το πιο αποτελεσματικό σχέδιο για πληρωμένη προβολή.
    gx, gy = PAD, 400
    cw, ch = (W - PAD * 2 - 24) // 2, 220
    for i, (num, lbl) in enumerate(t['nums']):
        cx = gx + (i % 2) * (cw + 24)
        cy = gy + (i // 2) * (ch + 24)
        d.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=28, fill=PANEL)
        f_n = ImageFont.truetype(FB, 96 if len(num) <= 3 else 84)
        d.text((cx + (cw - d.textlength(num, font=f_n)) / 2, cy + 28), num, font=f_n, fill=GOLD)
        f_l = ImageFont.truetype(FR, 30)
        ly = cy + 148
        for ln in lbl.split('\n'):
            d.text((cx + (cw - d.textlength(ln, font=f_l)) / 2, ly), ln, font=f_l, fill=(226, 208, 184))
            ly += 36

    d.text((PAD, 900), t['more'], font=ImageFont.truetype(FB, 30), fill=GOLD)
    items = REST[lang][:12]
    colw = (W - PAD * 2) // 3
    for i, (e, n) in enumerate(items):
        cx = PAD + (i % 3) * colw
        cy = 948 + (i // 3) * 46
        ic = emoji(e, 28); im.paste(ic, (cx, cy + 2), ic)
        d.text((cx + 38, cy + 3), n, font=fit(d, n, colw - 46, 22, 15, bold=False),
               fill=(222, 204, 180))
    cta(im, 1206, lang)
    save(im, '2-noumera', lang)

# --- 3 · Η ΟΘΟΝΗ -----------------------------------------------------------
def ad3(lang):
    t = T[lang]
    im = Image.new('RGB', (W, H), (26, 16, 6)); px = im.load()
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            dd = (((x - W / 2) / 640) ** 2 + ((y - 760) / 620) ** 2) ** .5
            v = max(0.0, 1 - dd) ** 2
            c = (round(26 + 66 * v), round(16 + 38 * v), round(6 + 11 * v))
            for oy in (0, 1):
                for ox in (0, 1):
                    if x + ox < W and y + oy < H: px[x + ox, y + oy] = c
    d = ImageDraw.Draw(im)
    brand(im, lang)

    # Ένα όφελος, όχι λίστα. Αυτό δεν το λέει καμία άλλη εφαρμογή συνταγών.
    d.text((PAD, 184), t['scr_h1'], font=fit(d, t['scr_h1'], W - PAD * 2, 48, 30), fill=(214, 192, 166))
    d.text((PAD, 242), t['scr_h2'], font=fit(d, t['scr_h2'], W - PAD * 2, 62, 40), fill=CREAM)
    d.text((PAD, 322), t['scr_sub'], font=fit(d, t['scr_sub'], W - PAD * 2, 29, 20, bold=False),
           fill=GOLD)

    PW, PH, R = 316, 606, 42
    dev = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
    ImageDraw.Draw(dev).rounded_rectangle([0, 0, PW, PH], radius=R, fill=(12, 8, 3, 255))
    scr = cover('moussaka', PW - 18, PH - 18, .5).convert('RGBA')
    ov = Image.new('RGBA', scr.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).rectangle([0, scr.height - 300, scr.width, scr.height], fill=(16, 10, 3, 224))
    scr = Image.alpha_composite(scr, ov)
    sd = ImageDraw.Draw(scr)
    base = scr.height - 278
    sd.text((26, base), 'ΒΗΜΑ 4 / 8' if lang == 'el' else 'STEP 4 / 8',
            font=ImageFont.truetype(FB, 23), fill=GOLD)
    step = ('Στρώνεις τις πατάτες και από πάνω τον κιμά' if lang == 'el'
            else 'Layer the potatoes, then the mince on top')
    f_s = ImageFont.truetype(FR, 27); yy = base + 40
    for ln in wrap(sd, step, f_s, scr.width - 52)[:3]:
        sd.text((26, yy), ln, font=f_s, fill=CREAM); yy += 36
    sd.rounded_rectangle([26, scr.height - 96, 196, scr.height - 36], radius=30, fill=BRICK)
    tm = emoji('⏱️', 32); scr.paste(tm, (44, scr.height - 82), tm)
    sd.text((90, scr.height - 81), '12:00', font=ImageFont.truetype(FB, 31), fill=(255, 255, 255))
    m = Image.new('L', scr.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, scr.width, scr.height], radius=R - 8, fill=255)
    dev.paste(scr.convert('RGB'), (9, 9), m)
    sh = Image.new('RGBA', (PW + 130, PH + 130), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([65, 76, 65 + PW, 76 + PH], radius=R, fill=(0, 0, 0, 160))
    sh = sh.filter(ImageFilter.GaussianBlur(28))
    im.paste(sh, ((W - sh.width) // 2, 398 - 65), sh)
    im.paste(dev, ((W - PW) // 2, 398), dev)

    # Δύο ετικέτες αριστερά, δύο δεξιά — μετρημένες ώστε να μην κόβονται.
    lx, rx = (W - PW) // 2 - 26, (W + PW) // 2 + 26
    def side(items, x, right):
        avail = (x - 46 - 50) if right else (W - 46 - x - 50)
        yy = 476
        for e, n in items:
            f = fit(d, n, avail, 29, 20)
            ic = emoji(e, 38)
            if right:
                im.paste(ic, (x - 38, yy), ic)
                d.text((x - 50 - d.textlength(n, font=f), yy + 6), n, font=f, fill=CREAM)
            else:
                im.paste(ic, (x, yy), ic)
                d.text((x + 50, yy + 6), n, font=f, fill=CREAM)
            yy += 230
    side(t['scr_side'][:2], lx, True)
    side(t['scr_side'][2:], rx, False)

    d.text((PAD, 1066), t['more'], font=ImageFont.truetype(FB, 28), fill=GOLD)
    items = REST[lang][:9]
    colw = (W - PAD * 2) // 3
    for i, (e, n) in enumerate(items):
        cx = PAD + (i % 3) * colw
        cy = 1110 + (i // 3) * 42
        ic = emoji(e, 26); im.paste(ic, (cx, cy + 2), ic)
        d.text((cx + 36, cy + 2), n, font=fit(d, n, colw - 44, 21, 15, bold=False),
               fill=(222, 204, 180))
    cta(im, 1250, lang, center=True)
    save(im, '3-othoni', lang)

# --- 4 · Η ΜΕΡΑ ΣΟΥ --------------------------------------------------------
def ad4(lang):
    t = T[lang]
    im = Image.new('RGB', (W, H), INK)
    d = ImageDraw.Draw(im)
    brand(im, lang)
    y = 176
    for ln in t['day_h'].split('\n'):
        d.text((PAD, y), ln, font=ImageFont.truetype(FB, 68), fill=CREAM); y += 78

    # Τέσσερις μεγάλες φωτογραφίες: στη διαφήμιση το φαγητό πουλά, όχι το κείμενο.
    D_, gap = 196, 20
    gy = 352
    for i, (hhmm, txt, rid) in enumerate(t['day']):
        cx = PAD + (i % 2) * (D_ * 2 + gap * 2 + 8)
        cy = gy + (i // 2) * (D_ + 112)
        cw = D_ * 2 + gap
        thumb = cover(rid, cw, D_, .5)
        mk = Image.new('L', (cw, D_), 0)
        ImageDraw.Draw(mk).rounded_rectangle([0, 0, cw, D_], radius=24, fill=255)
        im.paste(thumb, (cx, cy), mk)
        d.rounded_rectangle([cx + 14, cy + 14, cx + 14 + 116, cy + 14 + 46], radius=23,
                            fill=(16, 10, 3, 255))
        d.text((cx + 30, cy + 22), hhmm, font=ImageFont.truetype(FB, 27), fill=GOLD)
        d.text((cx, cy + D_ + 16), txt, font=fit(d, txt, cw, 31, 20), fill=CREAM)

    d.text((PAD, 1004), t['more'], font=ImageFont.truetype(FB, 28), fill=GOLD)
    items = REST[lang][:12]
    colw = (W - PAD * 2) // 3
    for i, (e, n) in enumerate(items):
        cx = PAD + (i % 3) * colw
        cy = 1048 + (i // 3) * 42
        ic = emoji(e, 26); im.paste(ic, (cx, cy + 2), ic)
        d.text((cx + 36, cy + 2), n, font=fit(d, n, colw - 44, 21, 15, bold=False),
               fill=(222, 204, 180))
    cta(im, 1232, lang)
    save(im, '4-mera', lang)

ADS = {'1': ad1, '2': ad2, '3': ad3, '4': ad4}

if __name__ == '__main__':
    args = sys.argv[1:]
    lang = next((a for a in args if a in ('el', 'en')), 'el')
    keys = [a for a in args if a in ADS] or list(ADS)
    print(f'Διαφημίσεις Facebook ({lang}) — {N} συνταγές')
    for k in keys:
        ADS[k](lang)
