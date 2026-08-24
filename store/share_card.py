# -*- coding: utf-8 -*-
"""Εικόνες κοινοποίησης με QR — για Instagram, Facebook, εκτυπώσεις,
δηλαδή όπου ο σύνδεσμος δεν πατιέται.
Δεν ζωγραφίζουμε ψεύτικο κουμπί: σε εικόνα δεν πατιέται τίποτα, οπότε η
προτροπή είναι το QR και η διεύθυνση."""
from PIL import Image, ImageDraw, ImageFont
import os, qrcode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, 'store')
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
URL = 'georgebokos.github.io/install.html'

T = {'el': {'tag': 'Τι μαγειρεύουμε σήμερα;',
            'sub': '376 ελληνικές συνταγές · μία πρόταση κάθε μέρα',
            'act': 'Σκάναρε τον κωδικό',
            'free': 'Δωρεάν στο Google Play'},
     'en': {'tag': 'What are we cooking today?',
            'sub': '376 Greek recipes · one idea every day',
            'act': 'Scan the code',
            'free': 'Free on Google Play'}}

def qr_img(px):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    q.add_data('https://' + URL); q.make(fit=True)
    return q.make_image(fill_color=(42, 27, 6), back_color='white').convert('RGB').resize((px, px), Image.NEAREST)

def build(lang, W, H, name):
    t = T[lang]
    im = Image.new('RGB', (W, H)); p = im.load()
    for y in range(0, H, 3):
        for x in range(0, W, 3):
            f = (x / W) * .55 + (y / H) * .45
            c = (round(152 - 46 * f), round(95 - 31 * f), round(7 - 6 * f))
            for dy in range(3):
                for dx in range(3):
                    if x + dx < W and y + dy < H: p[x + dx, y + dy] = c
    d = ImageDraw.Draw(im)
    S = min(W, H)

    # Το μπλοκ υπολογίζεται και σμικρύνεται μέχρι να χωρέσει με περιθώριο.
    # Χωρίς αυτό, στο τετράγωνο πλαίσιο κοβόταν το εικονίδιο και η τελευταία γραμμή.
    def layout(k):
        F = lambda f, r: ImageFont.truetype(f, max(10, round(S * r * k)))
        fn = {'name': F(FB, .095), 'tag': F(FB, .050), 'sub': F(FR, .032),
              'act': F(FB, .036), 'url': F(FB, .030)}
        D = round(S * .20 * k)
        Q = round(S * .30 * k)
        pad = round(S * .045 * k)
        lh = lambda f: round(f.size * 1.30)
        gaps = [round(S * g * k) for g in (.045, .030, .022, .065, .028, .016, .028)]
        h = (D + gaps[0] + lh(fn['name']) + gaps[1] + lh(fn['tag']) + gaps[2] + lh(fn['sub'])
             + gaps[3] + Q + pad * 2 + gaps[4] + lh(fn['act']) + gaps[5] + lh(fn['url'])
             + gaps[6] + lh(fn['sub']))
        return fn, D, Q, pad, gaps, lh, h

    k = 1.0
    fn, D, Q, pad, gaps, lh, h = layout(k)
    while h > H * 0.90 and k > 0.4:
        k -= 0.02
        fn, D, Q, pad, gaps, lh, h = layout(k)

    ctr = lambda txt, f, y, col: d.text(((W - d.textlength(txt, font=f)) / 2, y), txt, font=f, fill=col)

    ic = Image.open(os.path.join(ROOT, 'icon-512.png')).convert('RGB').crop((118, 88, 394, 364)).resize((D, D), Image.LANCZOS)
    m = Image.new('L', (D * 4, D * 4), 0); ImageDraw.Draw(m).ellipse([0, 0, D * 4, D * 4], fill=255)
    ic.putalpha(m.resize((D, D), Image.LANCZOS))
    plate = Image.new('RGB', (Q + pad * 2, Q + pad * 2), (255, 255, 255))
    plate.paste(qr_img(Q), (pad, pad))

    y = (H - h) // 2
    im.paste(ic, ((W - D) // 2, y), ic);                 y += D + gaps[0]
    ctr('FoodDaily', fn['name'], y, (255, 253, 248));    y += lh(fn['name']) + gaps[1]
    ctr(t['tag'], fn['tag'], y, (255, 250, 240));        y += lh(fn['tag']) + gaps[2]
    ctr(t['sub'], fn['sub'], y, (238, 210, 160));        y += lh(fn['sub']) + gaps[3]
    im.paste(plate, ((W - plate.width) // 2, y));        y += plate.height + gaps[4]
    ctr(t['act'], fn['act'], y, (255, 252, 246));        y += lh(fn['act']) + gaps[5]
    ctr(URL, fn['url'], y, (233, 178, 74));              y += lh(fn['url']) + gaps[6]
    ctr(t['free'], fn['sub'], y, (216, 190, 150))

    path = os.path.join(OUT, f'share-{name}-{lang}.png')
    im.save(path, 'PNG', optimize=True)
    print(f'  ✓ share-{name}-{lang}.png  {W}×{H}  κλίμακα {k:.2f}  {os.path.getsize(path)//1024} KB')

for lang in ('el', 'en'):
    build(lang, 1080, 1080, 'tetragono')   # Instagram, Facebook, Viber
    build(lang, 1080, 1920, 'story')       # Stories, Shorts, WhatsApp status
