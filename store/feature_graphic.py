#!/usr/bin/env python3
"""Feature graphic 1024×500 για το Play Store (ελληνικά και αγγλικά).
Χωρίς διαφάνεια, χωρίς πλαίσια συσκευών — όπως το θέλει η Google.
Το σημαντικό περιεχόμενο μένει μακριά από τις άκρες, γιατί το Play
περικόπτει το γραφικό σε κάποιες θέσεις."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

W, H = 1024, 500
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

TXT = {
 'el': {'tag':'Τι μαγειρεύουμε σήμερα;',
        'sub':'376 ελληνικές συνταγές',
        'b':['Πρόταση φαγητού κάθε μέρα','Μαγείρεψε ό,τι έχεις στο ψυγείο','Κόστος ανά μερίδα & λίστα αγορών']},
 'en': {'tag':'What are we cooking today?',
        'sub':'376 authentic Greek recipes',
        'b':['A meal suggestion every day','Cook with what you already have','Cost per serving & shopping list']},
}
DISHES = ['giouvetsi', 'pastitsio', 'souvlakia']

def gradient(a, b):
    im = Image.new('RGB', (W, H)); p = im.load()
    for y in range(H):
        for x in range(W):
            f = (x / W) * .65 + (y / H) * .35
            p[x, y] = tuple(round(a[i] + (b[i] - a[i]) * f) for i in range(3))
    return im

def circle(path, d):
    im = Image.open(os.path.join(ROOT, path)).convert('RGB')
    s = min(im.size); im = im.crop(((im.width-s)//2, (im.height-s)//2,
                                   (im.width+s)//2, (im.height+s)//2)).resize((d, d), Image.LANCZOS)
    m = Image.new('L', (d*4, d*4), 0); ImageDraw.Draw(m).ellipse([0, 0, d*4, d*4], fill=255)
    im.putalpha(m.resize((d, d), Image.LANCZOS))
    return im

def build(lang):
    t = TXT[lang]
    im = gradient((150, 94, 6), (100, 61, 0))
    d = ImageDraw.Draw(im)

    # Φωτογραφίες πιάτων δεξιά, σε κύκλους
    import re
    html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    imgs = dict(re.findall(r"(\w+):'(images/[\w.\-]+)'", html))
    spots = [(838, 158, 194), (714, 356, 128), (912, 372, 116)]
    for name, (cx, cy, dia) in zip(DISHES, spots):
        p = imgs.get(name)
        if not p or not os.path.exists(os.path.join(ROOT, p)):
            continue
        ph = circle(p, dia)
        ring = Image.new('RGBA', (dia+12, dia+12), (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse([0, 0, dia+11, dia+11], fill=(252, 245, 232, 235))
        im.paste(ring, (cx-dia//2-6, cy-dia//2-6), ring)
        im.paste(ph, (cx-dia//2, cy-dia//2), ph)

    # Έμβλημα εφαρμογής
    # Το ίδιο το εικονίδιο χάνεται πάνω στο καφέ φόντο· κρατάμε μόνο το πιάτο,
    # που είναι ανοιχτόχρωμο και ξεχωρίζει.
    ic = Image.open(os.path.join(ROOT, 'icon-512.png')).convert('RGB').crop((118, 88, 394, 364))
    D2 = 104
    ic = ic.resize((D2, D2), Image.LANCZOS)
    m = Image.new('L', (D2*4, D2*4), 0); ImageDraw.Draw(m).ellipse([0, 0, D2*4, D2*4], fill=255)
    ic.putalpha(m.resize((D2, D2), Image.LANCZOS))
    im.paste(ic, (64, 56), ic)

    d.text((188, 76), 'FoodDaily', font=ImageFont.truetype(F, 52), fill=(255, 252, 246))
    d.text((64, 196), t['tag'], font=ImageFont.truetype(F, 44), fill=(255, 250, 240))
    d.text((64, 256), t['sub'], font=ImageFont.truetype(FR, 21), fill=(242, 220, 176))

    y = 316
    for b in t['b']:
        d.ellipse([66, y+7, 80, y+21], fill=(233, 178, 74))
        d.text((96, y), b, font=ImageFont.truetype(FR, 23), fill=(252, 242, 226))
        y += 42

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'feature-graphic-1024x500-{lang}.png')
    im.save(out, 'PNG', optimize=True)
    print(f'  ✓ {os.path.basename(out)}  {os.path.getsize(out)//1024} KB')

for l in ('el', 'en'):
    build(l)
