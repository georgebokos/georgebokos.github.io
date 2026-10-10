# -*- coding: utf-8 -*-
"""Κάρτες κοινοποίησης με QR — για Instagram, Facebook, εκτυπώσεις, δηλαδή
όπου ο σύνδεσμος δεν πατιέται.

Δεν ζωγραφίζουμε ψεύτικο κουμπί: σε εικόνα δεν πατιέται τίποτα, οπότε η
προτροπή είναι το QR, το επίσημο σήμα του Google Play και η διεύθυνση.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, qrcode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, 'store')
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

# Το QR οδηγεί ΑΠΕΥΘΕΙΑΣ στο Google Play, όχι στο site: όποιος σκανάρει θέλει
# να εγκαταστήσει, και μια ενδιάμεση σελίδα χάνει τους μισούς. Η διεύθυνση του
# site είχε και το επώνυμο του δημιουργού μέσα της.
QR_URL = 'https://play.google.com/store/apps/details?id=com.fooddaily.app'
URL    = 'play.google.com/store/apps/details?id=com.fooddaily.app'

CREAM = (255, 253, 248)
GOLD  = (240, 190, 92)
WARM  = (240, 216, 174)
MUTED = (206, 174, 128)

T = {'el': {'tag': 'Τι μαγειρεύουμε σήμερα;',
            'sub': '397 ελληνικές συνταγές · 12 προτάσεις κάθε μέρα',
            'act': 'Σκάναρε και κατέβασέ το',
            'langs': 'Ελληνικά · English · Deutsch'},
     'en': {'tag': 'What are we cooking today?',
            'sub': '397 Greek recipes · one idea every day',
            'act': 'Scan and download',
            'langs': 'Ελληνικά · English · Deutsch'}}

def qr_img(px):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=0)
    q.add_data(QR_URL); q.make(fit=True)
    return q.make_image(fill_color=(34, 22, 6), back_color='white').convert('RGB').resize((px, px), Image.NEAREST)

def badge(w):
    """Επίσημο σήμα Google Play, με κομμένο το κενό περιθώριο του αρχείου."""
    b = Image.open(os.path.join(ROOT, 'ads', 'google-play-badge.png')).convert('RGBA')
    b = b.crop(b.split()[3].getbbox())
    return b.resize((w, round(b.height * w / b.width)), Image.LANCZOS)

def background(W, H):
    """Ζεστό καφέ ντεγκραντέ με απαλή λάμψη πίσω από το κέντρο.

    Η λάμψη δεν είναι διακόσμηση: τραβά το μάτι εκεί όπου κάθεται το QR και
    κάνει την κάρτα να διαβάζεται ως μία σύνθεση αντί για λίστα από γραμμές.
    """
    im = Image.new('RGB', (W, H)); px = im.load()
    cx, cy = W / 2, H * 0.46
    maxd = (cx ** 2 + cy ** 2) ** 0.5
    for y in range(H):
        for x in range(W):
            f = (x / W) * .5 + (y / H) * .5
            dd = (((x - cx) / maxd) ** 2 + ((y - cy) / maxd) ** 2) ** 0.5
            g = max(0.0, 1 - dd * 1.9) ** 2
            px[x, y] = (round(120 - 56 * f + 48 * g),
                        round(72 - 36 * f + 30 * g),
                        round(15 - 11 * f + 8 * g))
    return im

def card(qr_px, pad, radius=46):
    """Λευκή κάρτα με στρογγυλεμένες γωνίες και απαλή σκιά κάτω από το QR."""
    S = qr_px + pad * 2
    blur = 26
    canvas = Image.new('RGBA', (S + blur * 2, S + blur * 2), (0, 0, 0, 0))
    sh = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        [blur, blur + 12, blur + S, blur + S + 12], radius=radius, fill=(0, 0, 0, 125))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur / 2)))
    plate = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle([0, 0, S, S], radius=radius, fill=(255, 255, 255, 255))
    plate.paste(qr_img(qr_px), (pad, pad))
    canvas.alpha_composite(plate, (blur, blur))
    return canvas

def build(lang, W, H, name):
    t = T[lang]
    im = background(W, H)
    d = ImageDraw.Draw(im)
    S = min(W, H)

    # Το μπλοκ υπολογίζεται και σμικρύνεται μέχρι να χωρέσει με περιθώριο.
    # Χωρίς αυτό, στο τετράγωνο πλαίσιο κόβεται το σήμα και η τελευταία γραμμή.
    def layout(k):
        F = lambda f, r: ImageFont.truetype(f, max(10, round(S * r * k)))
        fn = {'name': F(FB, .098), 'tag': F(FB, .048), 'sub': F(FR, .030),
              'act': F(FB, .034), 'url': F(FR, .018), 'lang': F(FR, .026)}
        D   = round(S * .19 * k)
        Q   = round(S * .29 * k)
        pad = round(S * .032 * k)
        BW  = round(S * .34 * k)
        bh  = badge(BW).height
        lh  = lambda f: round(f.size * 1.28)
        g   = [round(S * v * k) for v in (.038, .024, .016, .020, .046, .024, .030, .020)]
        h = (D + g[0] + lh(fn['name']) + g[1] + lh(fn['tag']) + g[2] + lh(fn['sub'])
             + g[3] + lh(fn['lang']) + g[4] + (Q + pad * 2) + g[5] + lh(fn['act'])
             + g[6] + bh + g[7] + lh(fn['url']))
        return fn, D, Q, pad, BW, bh, g, lh, h

    k = 1.0
    fn, D, Q, pad, BW, bh, g, lh, h = layout(k)
    while h > H * 0.90 and k > 0.4:
        k -= 0.02
        fn, D, Q, pad, BW, bh, g, lh, h = layout(k)

    ctr = lambda txt, f, y, col: d.text(((W - d.textlength(txt, font=f)) / 2, y), txt, font=f, fill=col)

    ic = Image.open(os.path.join(ROOT, 'icon-512.png')).convert('RGB') \
              .crop((118, 88, 394, 364)).resize((D, D), Image.LANCZOS)
    m = Image.new('L', (D * 4, D * 4), 0); ImageDraw.Draw(m).ellipse([0, 0, D * 4, D * 4], fill=255)
    ic.putalpha(m.resize((D, D), Image.LANCZOS))

    plate = card(Q, pad)
    gp    = badge(BW)

    y = (H - h) // 2
    im.paste(ic, ((W - D) // 2, y), ic);                 y += D + g[0]
    ctr('FoodDaily', fn['name'], y, CREAM);              y += lh(fn['name']) + g[1]
    ctr(t['tag'], fn['tag'], y, (255, 247, 233));        y += lh(fn['tag']) + g[2]
    ctr(t['sub'], fn['sub'], y, WARM);                   y += lh(fn['sub']) + g[3]
    ctr(t['langs'], fn['lang'], y, GOLD);                y += lh(fn['lang']) + g[4]
    # Η σκιά της κάρτας έχει δικό της περιθώριο, γι' αυτό αφαιρείται εδώ
    im.paste(plate, ((W - plate.width) // 2, y - 26), plate)
    y += (Q + pad * 2) + g[5]
    ctr(t['act'], fn['act'], y, CREAM);                  y += lh(fn['act']) + g[6]
    im.paste(gp, ((W - BW) // 2, y), gp);                y += bh + g[7]
    ctr(URL, fn['url'], y, MUTED)

    path = os.path.join(OUT, f'share-{name}-{lang}.png')
    im.save(path, 'PNG', optimize=True)
    print(f'  ✓ share-{name}-{lang}.png  {W}×{H}  κλίμακα {k:.2f}  {os.path.getsize(path)//1024} KB')

if __name__ == '__main__':
    for lang in ('el', 'en'):
        build(lang, 1080, 1080, 'tetragono')   # Instagram, Facebook, Viber, προφίλ
        build(lang, 1080, 1920, 'story')       # Stories, Shorts, WhatsApp status
