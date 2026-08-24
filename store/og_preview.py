# -*- coding: utf-8 -*-
"""Εικόνα προεπισκόπησης 1200×630 για τον σύνδεσμο.
Όταν κολλάς τον σύνδεσμο σε Viber, WhatsApp, Messenger, Facebook, Telegram ή
Slack, αυτή η εικόνα γίνεται μεγάλη κάρτα — και ΟΛΗ η κάρτα πατιέται.
Γι' αυτό εδώ το ζωγραφισμένο κουμπί δεν είναι παραπλανητικό: το πάτημα όντως
ανοίγει τη σελίδα εγκατάστασης."""
from PIL import Image, ImageDraw, ImageFont
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
W, H = 1200, 630

T = {'el': {'tag': 'Τι μαγειρεύουμε σήμερα;', 'sub': '376 ελληνικές συνταγές · μία πρόταση κάθε μέρα',
            'cta': 'Εγκατάσταση τώρα', 'free': 'Δωρεάν στο Google Play'},
     'en': {'tag': 'What are we cooking today?', 'sub': '376 Greek recipes · one idea every day',
            'cta': 'Install now', 'free': 'Free on Google Play'}}

html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
IMGS = dict(re.findall(r"(\w+):'(images/[\w.\-]+)'", html))

def cover(path, w, h):
    im = Image.open(os.path.join(ROOT, path)).convert('RGB')
    r = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    return im.crop(((im.width - w)//2, (im.height - h)//2, (im.width - w)//2 + w, (im.height - h)//2 + h))

def build(lang):
    t = T[lang]
    im = cover(IMGS['giouvetsi'], W, H)
    # Σκίαστρο από αριστερά: το κείμενο μπαίνει αριστερά, το φαγητό μένει ορατό δεξιά
    g = Image.new('L', (W, 1)); px = g.load()
    for x in range(W):
        f = min(1.0, max(0.0, (x - W * .04) / (W * .78)))
        px[x, 0] = round(255 * (0.955 - 0.80 * f ** 1.7))
    im = Image.composite(Image.new('RGB', (W, H), (26, 15, 2)), im, g.resize((W, H)))
    d = ImageDraw.Draw(im)

    pad = 64
    D = 92
    ic = Image.open(os.path.join(ROOT, 'icon-512.png')).convert('RGB').crop((118, 88, 394, 364)).resize((D, D), Image.LANCZOS)
    m = Image.new('L', (D*4, D*4), 0); ImageDraw.Draw(m).ellipse([0, 0, D*4, D*4], fill=255)
    ic.putalpha(m.resize((D, D), Image.LANCZOS))
    im.paste(ic, (pad, pad), ic)
    f_logo = ImageFont.truetype(FB, 44)
    d.text((pad + D + 22, pad + (D - 44)//2 - 4), 'FoodDaily', font=f_logo, fill=(255, 252, 246))

    f_tag = ImageFont.truetype(FB, 56)
    f_sub = ImageFont.truetype(FR, 27)
    f_cta = ImageFont.truetype(FB, 34)
    f_fr  = ImageFont.truetype(FR, 24)

    bh = 86
    by = H - pad - bh - 46
    y = by - 34 - 27 - 26 - 56
    d.text((pad, y), t['tag'], font=f_tag, fill=(255, 251, 244)); y += 56 + 26
    d.text((pad, y), t['sub'], font=f_sub, fill=(241, 216, 170))

    bw = round(d.textlength(t['cta'], font=f_cta)) + 84
    d.rounded_rectangle([pad, by, pad + bw, by + bh], radius=bh//2, fill=(200, 80, 26))
    # Το τριγωνάκι του Google Play
    cx, cy, s = pad + 40, by + bh//2, 15
    d.polygon([(cx-s*.55, cy-s), (cx-s*.55, cy+s), (cx+s*.75, cy)], fill=(255, 255, 255))
    d.text((pad + 74, by + (bh - 34)//2 - 3), t['cta'], font=f_cta, fill=(255, 255, 255))
    d.text((pad, by + bh + 18), t['free'], font=f_fr, fill=(226, 200, 160))

    # JPEG και όχι PNG: το WhatsApp αγνοεί προεπισκοπήσεις πάνω από ~300 KB.
    p = os.path.join(ROOT, f'og-preview-{lang}.jpg')
    q = 88
    while q > 55:
        im.save(p, 'JPEG', quality=q, optimize=True, progressive=True)
        if os.path.getsize(p) <= 280 * 1024: break
        q -= 4
    print(f'  ✓ og-preview-{lang}.jpg  {W}×{H}  ποιότητα {q}  {os.path.getsize(p)//1024} KB')

for l in ('el', 'en'):
    build(l)
