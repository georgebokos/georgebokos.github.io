# -*- coding: utf-8 -*-
"""Διαφημιστικά βίντεο για Google Ads / YouTube.
Παράγει κατακόρυφο (Shorts), οριζόντιο και τετράγωνο, σε ελληνικά και αγγλικά.
Τα καρέ φτιάχνονται με PIL και περνούν ωμά στο ffmpeg.
Χρήση: python3 ads/video.py [el|en] [portrait|landscape|square]
"""
from PIL import Image, ImageDraw, ImageFont
import os, re, sys, subprocess, imageio_ffmpeg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, 'ads')
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FPS = 25

RATIOS = {'portrait': (1080, 1920), 'landscape': (1920, 1080), 'square': (1080, 1080)}

html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
IMGS = dict(re.findall(r"(\w+):'(images/[\w.\-]+)'", html))

# (τύπος, πηγή, δευτερόλεπτα, κείμενο)
def scenes(lang):
    T = {
     'el': [('Τι μαγειρεύουμε σήμερα;', 'Η απόφαση που κουράζει περισσότερο από το μαγείρεμα'),
            ('Μία πρόταση κάθε μέρα', 'Με φωτογραφία, χρόνο και κόστος'),
            ('376 ελληνικές συνταγές', 'Μουσακάς, γεμιστά, γιουβέτσι, φασολάδα'),
            ('Τι έχεις στο ψυγείο;', 'Βρίσκει τι μπορείς να μαγειρέψεις τώρα'),
            ('Κόστος ανά μερίδα', 'Ξέρεις τι ξοδεύεις πριν τα ψώνια'),
            ('Δωρεάν στο Google Play', 'Χωρίς διαφημίσεις · δουλεύει και εκτός δικτύου')],
     'en': [('What are we cooking today?', 'The decision that tires you more than the cooking'),
            ('One suggestion every day', 'With a photo, the time and the cost'),
            ('376 Greek recipes', 'Moussaka, pastitsio, giouvetsi, bean soup'),
            ("What's in your fridge?", 'It finds what you can cook right now'),
            ('Cost per serving', 'Know what you spend before you shop'),
            ('Free on Google Play', 'No ads · works offline')],
    }[lang]
    sh = f'store/screenshots-{lang}/8-psygeio.png'
    return [
      ('photo',  IMGS['giouvetsi'],  3.4, T[0]),
      ('photo',  IMGS['pastitsio'],  2.8, T[1]),
      ('photo',  IMGS['souvlakia'],  2.8, T[2]),
      ('shot',   sh,                 3.6, T[3]),
      ('photo',  IMGS['moussaka'],   2.8, T[4]),
      ('cta',    None,               3.0, T[5]),
    ]

def cover(im, w, h):
    r = max(w / im.width, h / im.height)
    im = im.resize((max(1, round(im.width * r)), max(1, round(im.height * r))), Image.LANCZOS)
    return im.crop(((im.width - w) // 2, (im.height - h) // 2,
                    (im.width - w) // 2 + w, (im.height - h) // 2 + h))

def scrim_mask(w, h, top, base=.28, peak=.95):
    g = Image.new('L', (1, h), 0); p = g.load()
    for y in range(h):
        f = 0 if y < top else (y - top) / max(1, h - top)
        p[0, y] = round(255 * (base + (peak - base) * min(1., f) ** 1.5))
    return g.resize((w, h))

def wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ''
    for wd in words:
        t = (cur + ' ' + wd).strip()
        if d.textlength(t, font=font) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = wd
    if cur: lines.append(cur)
    return lines

def build(lang, ratio):
    W, H = RATIOS[ratio]
    pad = round(W * .066)
    f_big = ImageFont.truetype(FB, round(W * (.052 if ratio == 'landscape' else .072)))
    f_sub = ImageFont.truetype(FR, round(W * (.028 if ratio == 'landscape' else .038)))
    f_cta = ImageFont.truetype(FB, round(W * (.034 if ratio == 'landscape' else .046)))
    f_logo = ImageFont.truetype(FB, round(W * (.030 if ratio == 'landscape' else .042)))
    dark = Image.new('RGB', (W, H), (24, 13, 2))
    mask = scrim_mask(W, H, int(H * (.20 if ratio == 'landscape' else .34)))

    LD = round(W * (.068 if ratio == 'landscape' else .094))
    logo = Image.open(os.path.join(ROOT, 'icon-512.png')).convert('RGB').crop((118, 88, 394, 364)).resize((LD, LD), Image.LANCZOS)
    lm = Image.new('L', (LD * 4, LD * 4), 0); ImageDraw.Draw(lm).ellipse([0, 0, LD * 4, LD * 4], fill=255)
    logo.putalpha(lm.resize((LD, LD), Image.LANCZOS))

    out = os.path.join(OUT, f'video-{ratio}-{lang}.mp4')
    proc = subprocess.Popen(
        [FFMPEG, '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
         '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21',
         '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    SC = scenes(lang)
    n_all = sum(round(sec * FPS) for _, _, sec, _ in SC)
    FADE = round(FPS * .5)          # μισό δευτερόλεπτο
    total = 0
    for kind, src, secs, (title, sub) in SC:
        n = round(secs * FPS)
        base = None
        if kind != 'cta':
            raw = Image.open(os.path.join(ROOT, src)).convert('RGB')
            # Το στιγμιότυπο δεν περικόπτεται — μπαίνει ολόκληρο πάνω σε θολό φόντο.
            if kind == 'shot':
                bgm = cover(raw, W, H).filter(__import__('PIL.ImageFilter', fromlist=['x']).GaussianBlur(28))
                sc = (min(W * .40 / raw.width, H * .72 / raw.height) if ratio == 'landscape'
                      else min(W * .74 / raw.width, H * .62 / raw.height))
                fg = raw.resize((round(raw.width * sc), round(raw.height * sc)), Image.LANCZOS)
                # Το σκίαστρο μπαίνει ΜΟΝΟ στο θολό φόντο. Αν έπεφτε και πάνω στο
                # στιγμιότυπο, η ίδια η εφαρμογή γινόταν δυσανάγνωστη στη διαφήμιση.
                base = Image.composite(dark, bgm, mask)
                base.paste(fg, ((W - fg.width) // 2, round(H * (.05 if ratio == 'landscape' else .10))))
            else:
                base = cover(raw, round(W * 1.14), round(H * 1.14))
        for i in range(n):
            p = i / max(1, n - 1)
            if kind == 'cta':
                fr = Image.new('RGB', (W, H)); px = fr.load()
                for y in range(0, H, 4):
                    for x in range(0, W, 4):
                        f = (x / W) * .6 + (y / H) * .4
                        c = (round(150 - 45 * f), round(94 - 30 * f), round(6 - 5 * f))
                        for dy in range(4):
                            for dx in range(4):
                                if x + dx < W and y + dy < H: px[x + dx, y + dy] = c
            elif kind == 'shot':
                fr = base.copy()
            else:
                # αργό ζουμ (εφέ Ken Burns)
                z = 1.0 + .06 * p
                cw, ch = round(W / z * 1.14 / 1.14), round(H / z * 1.14 / 1.14)
                x0 = (base.width - cw) // 2; y0 = (base.height - ch) // 2
                fr = base.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.LANCZOS)
                fr = Image.composite(dark, fr, mask)

            d = ImageDraw.Draw(fr)
            if kind == 'cta':
                # ΠΡΟΣΟΧΗ: με σταθερά ποσοστά ύψους, στο οριζόντιο πλαίσιο το όνομα
                # έπεφτε πάνω στο κουμπί. Το μπλοκ υπολογίζεται και κεντράρεται.
                S = min(W, H)
                D  = round(S * .22)
                nm = 'FoodDaily'
                bh = round(S * .105)
                bw = round(d.textlength(title, font=f_cta)) + round(S * .10)
                g1, g2, g3 = round(S * .045), round(S * .055), round(S * .032)
                block = D + g1 + f_big.size + g2 + bh + g3 + f_sub.size
                y0 = (H - block) // 2

                ic = Image.open(os.path.join(ROOT, 'icon-512.png')).convert('RGB').crop((118, 88, 394, 364)).resize((D, D), Image.LANCZOS)
                m2 = Image.new('L', (D * 4, D * 4), 0); ImageDraw.Draw(m2).ellipse([0, 0, D * 4, D * 4], fill=255)
                ic.putalpha(m2.resize((D, D), Image.LANCZOS))
                fr.paste(ic, ((W - D) // 2, y0), ic)

                y = y0 + D + g1
                d.text(((W - d.textlength(nm, font=f_big)) / 2, y), nm, font=f_big, fill=(255, 253, 248))
                y += f_big.size + g2
                bx = (W - bw) // 2
                d.rounded_rectangle([bx, y, bx + bw, y + bh], radius=bh // 2, fill=(200, 80, 26))
                d.text((bx + (bw - d.textlength(title, font=f_cta)) / 2, y + (bh - f_cta.size) / 2 - round(S * .004)), title, font=f_cta, fill=(255, 255, 255))
                y += bh + g3
                d.text(((W - d.textlength(sub, font=f_sub)) / 2, y), sub, font=f_sub, fill=(236, 208, 158))
            else:
                fr.paste(logo, (pad, pad), logo)
                d.text((pad + LD + round(W * .022), pad + (LD - f_logo.size) // 2 - round(W * .005)), 'FoodDaily', font=f_logo, fill=(255, 252, 246))
                tl = wrap(d, title, f_big, W - 2 * pad)
                sl = wrap(d, sub, f_sub, W - 2 * pad)
                lh, sh_ = round(f_big.size * 1.15), round(f_sub.size * 1.35)
                y = H - pad - len(sl) * sh_ - round(f_sub.size * .7) - len(tl) * lh
                for ln in tl: d.text((pad, y), ln, font=f_big, fill=(255, 253, 248)); y += lh
                y += round(f_sub.size * .7)
                for ln in sl: d.text((pad, y), ln, font=f_sub, fill=(240, 214, 166)); y += sh_
            # ΠΡΟΣΟΧΗ: σβήσιμο μόνο στην αρχή και στο τέλος ΤΟΥ ΒΙΝΤΕΟ.
            # Σβήσιμο σε κάθε σκηνή έκανε την εικόνα να μαυρίζει έξι φορές.
            fade = min(1., (total + 1) / FADE, (n_all - total) / FADE)
            if fade < 1.:
                fr = Image.blend(Image.new('RGB', (W, H), (0, 0, 0)), fr, max(0., fade))
            proc.stdin.write(fr.tobytes()); total += 1
    proc.stdin.close(); proc.wait()
    print(f'  ✓ video-{ratio}-{lang}.mp4  {W}×{H}  {total/FPS:.1f}s  {os.path.getsize(out)//1024} KB')

langs  = [sys.argv[1]] if len(sys.argv) > 1 else ['el', 'en']
ratios = [sys.argv[2]] if len(sys.argv) > 2 else list(RATIOS)
for l in langs:
    for r in ratios:
        build(l, r)
