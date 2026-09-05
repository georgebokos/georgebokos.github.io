# -*- coding: utf-8 -*-
"""Διαφημιστικές εικόνες Google Ads σε όλες τις αναλογίες που δέχεται
μια App campaign: 1.91:1 (οριζόντια), 1:1 (τετράγωνη), 4:5 (κατακόρυφη)."""
from PIL import Image, ImageDraw, ImageFont
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, 'ads')
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

SIZES = {'landscape': (1200, 628), 'square': (1200, 1200), 'portrait': (1200, 1500)}
# Στο οριζόντιο πλαίσιο δεν χωρά δίστιχος τίτλος χωρίς να πέσει πάνω στο λογότυπο.
TXT = {
 'el': {'h': 'Τι μαγειρεύουμε\nσήμερα;', 'h1': 'Τι μαγειρεύουμε σήμερα;',
        's': '376 ελληνικές συνταγές', 'c': 'Δωρεάν στο Google Play'},
 'en': {'h': 'What are we\ncooking today?', 'h1': 'What are we cooking today?',
        's': '376 Greek recipes', 'c': 'Free on Google Play'},
}
HERO = 'giouvetsi'

html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
IMGS = dict(re.findall(r"(\w+):'(images/[\w.\-]+)'", html))

def cover(path, w, h):
    """Γεμίζει το πλαίσιο διατηρώντας τις αναλογίες, με περικοπή στο κέντρο."""
    im = Image.open(os.path.join(ROOT, path)).convert('RGB')
    r = max(w / im.width, h / im.height)
    im = im.resize((max(1, round(im.width * r)), max(1, round(im.height * r))), Image.LANCZOS)
    return im.crop(((im.width - w) // 2, (im.height - h) // 2,
                    (im.width - w) // 2 + w, (im.height - h) // 2 + h))

def scrim(w, h, top):
    """Σκούρα βαθμίδα από κάτω, ώστε το κείμενο να διαβάζεται πάνω στη φωτογραφία.
    Ένα ελαφρύ στρώμα καλύπτει ΟΛΗ την εικόνα — χωρίς αυτό το λογότυπο πάνω αριστερά
    χανόταν σε φωτεινές φωτογραφίες."""
    BASE = 0.30          # σταθερό σκοτείνιασμα παντού
    g = Image.new('L', (1, h), 0); p = g.load()
    for y in range(h):
        f = 0 if y < top else (y - top) / max(1, h - top)
        v = BASE + (0.97 - BASE) * (min(1.0, f) ** 1.5)
        p[0, y] = round(255 * v)
    return Image.new('RGB', (w, h), (24, 13, 2)), g.resize((w, h))

def build(lang, name, w, h):
    t = TXT[lang]
    im = cover(IMGS[HERO], w, h)
    dark, mask = scrim(w, h, int(h * (.22 if name == 'landscape' else .34)))
    im = Image.composite(dark, im, mask)
    d = ImageDraw.Draw(im)

    pad = round(w * .066)
    fh = round(w * (.062 if name == 'landscape' else .082))
    fs = round(w * (.036 if name == 'landscape' else .040))
    hf, sf, cf = ImageFont.truetype(FB, fh), ImageFont.truetype(FR, fs), ImageFont.truetype(FB, round(fs * .95))

    lines = (t['h1'] if name == 'landscape' else t['h']).split('\n')
    lh = round(fh * 1.16)
    cta_h = round(fs * 2.5)
    y = h - pad - cta_h - round(fs * 1.9) - lh * len(lines) - round(fs * .9)
    for ln in lines:
        d.text((pad, y), ln, font=hf, fill=(255, 253, 248)); y += lh
    y += round(fs * .5)
    d.text((pad, y), t['s'], font=sf, fill=(240, 214, 166)); y += round(fs * 1.9)

    cw = round(d.textlength(t['c'], font=cf)) + round(fs * 2.2)
    d.rounded_rectangle([pad, y, pad + cw, y + cta_h], radius=cta_h // 2, fill=(200, 80, 26))
    d.text((pad + round(fs * 1.1), y + (cta_h - fs) // 2 - round(fs * .1)), t['c'], font=cf, fill=(255, 255, 255))

    # Έμβλημα πάνω αριστερά
    D = round(w * .10)
    ic = Image.open(os.path.join(ROOT, 'icon-512.png')).convert('RGB').crop((118, 88, 394, 364)).resize((D, D), Image.LANCZOS)
    m = Image.new('L', (D * 4, D * 4), 0); ImageDraw.Draw(m).ellipse([0, 0, D * 4, D * 4], fill=255)
    ic.putalpha(m.resize((D, D), Image.LANCZOS))
    im.paste(ic, (pad, pad), ic)
    d.text((pad + D + round(w * .022), pad + (D - round(w * .046)) // 2 - round(w*.006)),
           'FoodDaily', font=ImageFont.truetype(FB, round(w * .046)), fill=(255, 252, 246))

    p = os.path.join(OUT, f'ad-{name}-{lang}.png')
    im.save(p, 'PNG', optimize=True)
    print(f'  ✓ ad-{name}-{lang}.png  {w}×{h}  {os.path.getsize(p)//1024} KB')

for lang in ('el', 'en'):
    for name, (w, h) in SIZES.items():
        build(lang, name, w, h)
