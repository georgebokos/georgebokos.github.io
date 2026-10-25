# -*- coding: utf-8 -*-
"""Reels «ΣΥΝΤΑΓΗ» — τρίτη μορφή, δίπλα στα reel.py και reel_lathos.py.

Το `reel.py` ξεκινά με ένα μεγάλο νούμερο και μετά δείχνει λίστες. Λειτουργεί,
αλλά είναι ήσυχο: η εικόνα στέκεται και ο θεατής διαβάζει.

Εδώ η λογική είναι άλλη — **τίποτα δεν στέκεται ποτέ**. Η φωτογραφία κινείται
σε όλη τη διάρκεια, τα υλικά πέφτουν ένα-ένα με ρυθμό, τα βήματα περνούν
γρήγορα σαν αντίστροφη μέτρηση. Ο θεατής δεν προλαβαίνει να βαρεθεί.

Η σκηνή που λείπει από τις άλλες μορφές: **«ΤΙ ΠΑΙΡΝΕΙΣ»**. Πριν το Google
Play, λέει ρητά τι κερδίζει κάποιος αν κατεβάσει — αλλιώς το σήμα στο τέλος
είναι απλώς ένα λογότυπο χωρίς λόγο.

Χρήση:  python3 ads/reel_syntagi.py <id> [id ...]
"""
import os, re, sys, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reel import load, cover, wrap, W, H, FPS, FB, FR, SAFE_B, SAFE_R

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT    = os.path.join(ROOT, 'ads', 'reels')
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
PAD    = 74
COLW   = W - PAD - SAFE_R

CREAM = (255, 253, 248)
GOLD  = (247, 198, 104)
BRICK = (214, 74, 32)
INK   = (18, 10, 2)

PLAY = 'play.google.com/store/apps/details?id=com.fooddaily.app'

# Η σκηνή «τι παίρνεις»: τέσσερα οφέλη, όχι λίστα λειτουργιών. Κάθε γραμμή
# απαντά στο «και τι με νοιάζει;» — γι' αυτό καμία δεν λέει όνομα λειτουργίας.
PERKS = [('🍽️', '{N} συνταγές με φωτογραφία'),
         ('🔔', '12 προτάσεις κάθε πρωί'),
         ('🛒', 'Λίστα αγορών με ένα κλικ'),
         ('🍳', 'Η οθόνη δεν σβήνει όσο μαγειρεύεις')]

def total_meals():
    js = (r'const fs=require("fs"),vm=require("vm");'
          r'const b=fs.readFileSync(process.argv[1],"utf8")'
          r'.match(/<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/)[1];'
          r'const i=b.indexOf("const MEALS={"),j=b.indexOf("\n};",i);'
          r'const c={};vm.createContext(c);new vm.Script(b.slice(i,j+3)).runInContext(c);'
          r'console.log(Object.keys(vm.runInContext("MEALS",c)).length);')
    r = subprocess.run(['node', '-e', js, os.path.join(ROOT, 'index.html')],
                       capture_output=True, text=True)
    return int(r.stdout.strip()) if r.returncode == 0 else 0

N_MEALS = total_meals()

_ec = {}
def emoji(ch, px):
    """Το NotoColorEmoji υπάρχει μόνο στα 109px — ζωγραφίζεται εκεί και μικραίνει."""
    if (ch, px) not in _ec:
        f = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf', 109)
        im = Image.new('RGBA', (150, 150), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((12, 10), ch, font=f, embedded_color=True)
        im = im.crop(im.getbbox())
        s = px / max(im.size)
        _ec[(ch, px)] = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    return _ec[(ch, px)]

def scrim(src, base, peak, top=0):
    g = Image.new('L', (1, H)); px = g.load()
    for y in range(H):
        f = 0 if y < top else (y - top) / max(1, H - top)
        px[0, y] = round(255 * (base + (peak - base) * min(1.0, f) ** 1.4))
    return Image.composite(Image.new('RGB', (W, H), INK), src, g.resize((W, H)))

def ease(p): return 1 - (1 - min(1.0, max(0.0, p))) ** 3

def fade(layer, a):
    if a >= .99: return layer
    l = layer.copy()
    l.putalpha(l.split()[3].point(lambda v: round(v * a)))
    return l

def over(fr, draw_fn, a):
    """Ζωγραφίζει σε διάφανο στρώμα και το περνά με διαφάνεια a."""
    if a <= .02: return fr
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_fn(ov, ImageDraw.Draw(ov))
    return Image.alpha_composite(fr.convert('RGBA'), fade(ov, a)).convert('RGB')

def badge(w):
    b = Image.open(os.path.join(ROOT, 'ads', 'google-play-badge.png')).convert('RGBA')
    b = b.crop(b.split()[3].getbbox())
    return b.resize((w, round(b.height * w / b.width)), Image.LANCZOS)

def logo(d_):
    ic = Image.open(os.path.join(ROOT, 'icon-512.png')).convert('RGB') \
              .crop((118, 88, 394, 364)).resize((d_, d_), Image.LANCZOS)
    m = Image.new('L', (d_ * 4, d_ * 4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, d_ * 4, d_ * 4], fill=255)
    ic.putalpha(m.resize((d_, d_), Image.LANCZOS))
    return ic

def tag(d, x, y, txt, fill, size=34):
    f = ImageFont.truetype(FB, size)
    tw = d.textlength(txt, font=f)
    d.rounded_rectangle([x, y, x + tw + 40, y + size + 22], radius=(size + 22) // 2, fill=fill)
    d.text((x + 20, y + 10), txt, font=f, fill=(255, 255, 255))
    return y + size + 22

def short_step(s):
    """Μόνο ο τίτλος του βήματος. Το σώμα δεν διαβάζεται σε ένα δευτερόλεπτο."""
    head = s.split(':', 1)[0].strip()
    return head if 0 < len(head) <= 34 else re.sub(r'\s+', ' ', s)[:34].rsplit(' ', 1)[0]

def build(rid):
    data = load(rid); m = data['m']
    ings  = m['ing'][:8]
    steps = [short_step(s) for s in m['steps']][:7]
    photo = Image.open(os.path.join(ROOT, data['img'])).convert('RGB')
    bg    = cover(photo, W, H)
    blur  = bg.filter(ImageFilter.GaussianBlur(20))

    scenes = [('hook', 2.6), ('ing', 3.4), ('steps', 3.8), ('perks', 3.0), ('cta', 3.2)]
    out = os.path.join(OUT, f'syntagi-{rid}-el.mp4')
    proc = subprocess.Popen(
        [FFMPEG, '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
         '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21',
         '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    f_name = ImageFont.truetype(FB, 84)
    f_meta = ImageFont.truetype(FB, 40)
    f_item = ImageFont.truetype(FR, 42)
    f_num  = ImageFont.truetype(FB, 40)
    f_step = ImageFont.truetype(FB, 44)
    f_perk = ImageFont.truetype(FB, 40)

    total = sum(s for _, s in scenes)
    el_t = 0.0
    for kind, secs in scenes:
        n = max(1, round(secs * FPS))
        for i in range(n):
            p = i / max(1, n - 1)
            # Η φωτογραφία ΖΟΥΜΑΡΕΙ ΣΥΝΕΧΩΣ σε όλο το βίντεο, χωρίς να
            # επανέρχεται: ακίνητο καρέ σημαίνει «τελείωσε, φεύγω».
            gp = (el_t + p * secs) / total
            z = 1.0 + .16 * gp
            cw, ch = round(W / z), round(H / z)
            crop = lambda src: src.crop(((W - cw) // 2, (H - ch) // 2,
                                         (W - cw) // 2 + cw, (H - ch) // 2 + ch)).resize((W, H), Image.LANCZOS)
            if kind == 'hook':
                fr = scrim(crop(bg), .26, .90, int(H * .26))
            elif kind in ('ing', 'steps'):
                fr = scrim(crop(blur), .60, .84)
            else:
                fr = scrim(crop(blur), .74, .90)

            if kind == 'hook':
                nm = wrap(ImageDraw.Draw(fr), m['n'], f_name, COLW)[:2]
                def dh(ov, d, nm=nm):
                    y = 980 - len(nm) * 96
                    for k, ln in enumerate(nm):
                        d.text((PAD, y + k * 96), ln, font=f_name, fill=CREAM)
                    d.text((PAD, y + len(nm) * 96 + 26),
                           f"{m['time']}′  ·  {m['srv']} μερίδες  ·  {m.get('cps') or m.get('cost') or ''}/μερίδα",
                           font=f_meta, fill=GOLD)
                fr = over(fr, dh, ease(p / .18))
            elif kind == 'ing':
                def di(ov, d):
                    y = tag(d, PAD, 420, 'ΥΛΙΚΑ', BRICK) + 34
                    for k, it in enumerate(ings):
                        a = ease((p * secs - .25 - k * .22) / .30)
                        if a <= .02: break
                        row = Image.new('RGBA', (W, 70), (0, 0, 0, 0))
                        rd = ImageDraw.Draw(row)
                        rd.ellipse([0, 26, 14, 40], fill=GOLD)
                        rd.text((34, 8), it, font=f_item, fill=CREAM)
                        ov.alpha_composite(fade(row, a), (PAD + round(26 * (1 - a)), y + k * 70))
                fr = over(fr, di, 1.0)
            elif kind == 'steps':
                def ds(ov, d):
                    y = tag(d, PAD, 400, 'ΕΚΤΕΛΕΣΗ', (36, 122, 54)) + 34
                    for k, st in enumerate(steps):
                        a = ease((p * secs - .15 - k * .24) / .26)
                        if a <= .02: break
                        row = Image.new('RGBA', (W, 76), (0, 0, 0, 0))
                        rd = ImageDraw.Draw(row)
                        rd.text((0, 8), f'{k+1}', font=f_num, fill=GOLD)
                        rd.text((58, 4), st, font=f_step, fill=CREAM)
                        ov.alpha_composite(fade(row, a), (PAD + round(22 * (1 - a)), y + k * 76))
                fr = over(fr, ds, 1.0)
            elif kind == 'perks':
                def dp(ov, d):
                    d.text((PAD, 400), 'ΤΙ ΠΑΙΡΝΕΙΣ', font=ImageFont.truetype(FB, 36), fill=GOLD)
                    y = 480
                    for k, (e, txt) in enumerate(PERKS):
                        a = ease((p * secs - .1 - k * .30) / .34)
                        if a <= .02: break
                        row = Image.new('RGBA', (W, 104), (0, 0, 0, 0))
                        rd = ImageDraw.Draw(row)
                        ic = emoji(e, 50); row.paste(ic, (0, 10), ic)
                        for j, ln in enumerate(wrap(rd, txt.replace('{N}', str(N_MEALS)), f_perk, COLW - 80)[:2]):
                            rd.text((76, 4 + j * 48), ln, font=f_perk, fill=CREAM)
                        ov.alpha_composite(fade(row, a), (PAD, y + k * 104))
                fr = over(fr, dp, 1.0)
            else:
                def dc(ov, d):
                    ctr = lambda t_, f_, yy, c_: d.text(((W - d.textlength(t_, font=f_)) / 2, yy), t_, font=f_, fill=c_)
                    D_ = 126; L_ = logo(D_)
                    ov.paste(L_, ((W - D_) // 2, 470), L_)
                    ctr('FoodDaily', ImageFont.truetype(FB, 66), 618, CREAM)
                    ctr('Δωρεάν · χωρίς banner', ImageFont.truetype(FB, 40), 700, GOLD)
                    ctr('Ελληνικά · English · Deutsch', ImageFont.truetype(FR, 34), 762, (214, 192, 166))
                    gp2 = badge(304); ov.paste(gp2, ((W - 304) // 2, 826), gp2)
                    ctr(PLAY, ImageFont.truetype(FR, 25), 944, (190, 168, 140))
                fr = over(fr, dc, ease(p / .18))

            proc.stdin.write(fr.tobytes())
        el_t += secs

    proc.stdin.close(); proc.wait()
    print(f'  ✓ syntagi-{rid}-el.mp4  {total:.1f}s  {os.path.getsize(out)//1024} KB  «{m["n"]}»')

if __name__ == '__main__':
    ids = sys.argv[1:] or ['mosaiko']
    print(f'Reels «ΣΥΝΤΑΓΗ» — {len(ids)} βίντεο')
    for rid in ids:
        build(rid)
