# -*- coding: utf-8 -*-
"""Εικόνες για την ομάδα Facebook: εικόνα προφίλ και εξώφυλλο.

Δύο περιορισμοί καθορίζουν τη σχεδίαση:

1. **Η εικόνα προφίλ κόβεται σε κύκλο.** Ό,τι βγαίνει έξω από τον εγγεγραμμένο
   κύκλο χάνεται, οπότε όλο το περιεχόμενο μένει μέσα σε ακτίνα 0.42·πλάτους.
2. **Το εξώφυλλο κόβεται διαφορετικά σε κινητό και υπολογιστή.** Στο κινητό
   χάνονται τα πλάγια, οπότε τίποτα σημαντικό δεν πάει στο 18% κάθε πλευράς.

Χρήση: python3 ads/fb_images.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, 'ads')
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

BG   = (18, 12, 8)
GOLD = (233, 178, 74)
CREAM= (255, 253, 248)
WARM = (238, 222, 196)

def logo(size):
    im = Image.open(os.path.join(ROOT, 'icon-512.png')).convert('RGB') \
              .crop((118, 88, 394, 364)).resize((size, size), Image.LANCZOS)
    m = Image.new('L', (size*4, size*4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size*4, size*4], fill=255)
    im.putalpha(m.resize((size, size), Image.LANCZOS))
    return im

def badge(w):
    b = Image.open(os.path.join(ROOT, 'ads', 'google-play-badge.png')).convert('RGBA')
    b = b.crop(b.split()[3].getbbox())
    return b.resize((w, round(b.height * w / b.width)), Image.LANCZOS)

def ctr(d, t, f, y, w, col):
    d.text(((w - d.textlength(t, font=f)) / 2, y), t, font=f, fill=col)

def profile(path=os.path.join(OUT, 'fb-profile.png')):
    """1024×1024, με όλο το περιεχόμενο μέσα στον κύκλο που κόβει το Facebook."""
    S = 1024
    im = Image.new('RGB', (S, S), BG)
    d = ImageDraw.Draw(im)
    # Συμμετρική, απαλή λάμψη στο κέντρο. Σε μικρό μέγεθος η εικόνα προφίλ
    # πρέπει να διαβάζεται ως ένα σχήμα, όχι ως σύνθεση.
    for i in range(26):
        r = S//2 - i*9
        v = 26 - i
        d.ellipse([S//2-r, S//2-r, S//2+r, S//2+r], fill=(18+v//2, 12+v//3, 8))

    L = logo(460)
    im.paste(L, ((S - 460)//2, 140), L)

    f1 = ImageFont.truetype(FB, 96)
    ctr(d, 'FoodDaily', f1, 636, S, CREAM)

    # Μόνο το σήμα, χωρίς δεύτερη γραμμή κειμένου: σε 40 pixels στη ροή του
    # Facebook δύο σειρές κειμένου γίνονται μουτζούρα.
    gp = badge(330)
    im.paste(gp, ((S - 330)//2, 772), gp)
    im.save(path, 'PNG')
    return path

def cover(path=os.path.join(OUT, 'fb-cover.png')):
    """1640×856. Όλα κεντραρισμένα: στο κινητό κόβονται τα πλάγια."""
    W, H = 1640, 856
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    # Διακριτική λάμψη πίσω από το κείμενο
    for i in range(24):
        r = 520 - i*14
        v = 30 - i
        d.ellipse([W//2 - r, H//2 - r, W//2 + r, H//2 + r], fill=(18+v//3, 12+v//4, 8))

    L = logo(150)
    im.paste(L, ((W - 150)//2, 96), L)

    f1 = ImageFont.truetype(FB, 78)
    f2 = ImageFont.truetype(FR, 40)
    f3 = ImageFont.truetype(FB, 32)
    ctr(d, 'Τι μαγειρεύουμε σήμερα;', f1, 282, W, CREAM)
    ctr(d, '376 ελληνικές συνταγές — μία πρόταση κάθε μέρα', f2, 394, W, WARM)
    ctr(d, 'Ελληνικά  ·  English  ·  Deutsch', f3, 468, W, GOLD)

    gp = badge(320)
    im.paste(gp, ((W - 320)//2, 562), gp)

    im.save(path, 'PNG')
    return path

if __name__ == '__main__':
    for p in (profile(), cover()):
        print(f'  ✓ {os.path.basename(p)}  {os.path.getsize(p)//1024} KB')
