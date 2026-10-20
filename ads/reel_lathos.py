# -*- coding: utf-8 -*-
"""Reels «ΤΟ ΛΑΘΟΣ» — δεύτερη μορφή βίντεο, δίπλα στο ads/reel.py.

Τα 81 πρώτα Reels έχουν όλα το ίδιο σχήμα: μεγάλο νούμερο, υλικά, βήματα,
CTA. Όποιος είδε τρία ξέρει τι θα δει στο τέταρτο, και ο αλγόριθμος το ίδιο.

Εδώ το πρώτο καρέ δεν λέει «να μια συνταγή» — λέει **«το κάνεις λάθος»**, που
αφορά κάποιον ο οποίος ΗΔΗ μαγειρεύει το πιάτο. Τα βίντεο αυτής της μορφής
αποθηκεύονται και σχολιάζονται («εγώ το κάνω αλλιώς»), και τα δύο μετράνε
περισσότερο από τις σκέτες προβολές.

Το υλικό υπάρχει ήδη: 348 από τις 397 συνταγές έχουν μέσα σημείωση
«ΣΗΜΑΝΤΙΚΟ:», με τη μορφή

    «Τίτλος: η ενέργεια. ΣΗΜΑΝΤΙΚΟ: το γιατί.»

Από εκεί βγαίνουν μόνα τους τα δύο μεσαία καρέ. Το πρώτο καρέ (η απαγόρευση)
γράφεται με το χέρι στο HOOKS, γιατί πρέπει να είναι τεσσάρων-πέντε λέξεων
και καμία αυτόματη περικοπή δεν το πετυχαίνει.

ΔΕΝ υπάρχει λογότυπο στο πρώτο καρέ — η μάρκα έρχεται αφού κερδηθεί ο θεατής.

Χρήση:  python3 ads/reel_lathos.py [id ...]
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
INK   = (20, 11, 2)

# Η απαγόρευση του πρώτου καρέ, γραμμένη με το χέρι. Λίγες λέξεις, προστακτική,
# και πάντα κάτι που ο θεατής πιθανότατα ΚΑΝΕΙ λάθος αυτή τη στιγμή.
HOOKS = {
 'keftedes':     'Μη ζυμώνεις πολύ\nτον κιμά',
 'kalamaria':    'Μη βάλεις βρεγμένα\nκαλαμάρια στο λάδι',
 'aglio':        'Μη χύνεις το νερό\nτων μακαρονιών',
 'taramosalata': 'Μην αφήσεις νερό\nστο ψωμί',
 'htapodi':      'Μη ρίξεις νερό\nστο χταπόδι',
}
# Τι να κάνει αντ' αυτού — μία αράδα, στο τρίτο καρέ.
FIX = {
 'keftedes':     'Ζύμωσε 2-3 λεπτά και σταμάτα',
 'kalamaria':    'Στέγνωσέ τα καλά με χαρτί κουζίνας',
 'aglio':        'Κράτα μια κούπα πριν στραγγίσεις',
 'taramosalata': 'Στύψε το ψωμί με τα χέρια',
 'htapodi':      'Βράσ’ το στα δικά του υγρά',
}
L = {'bad': 'ΤΟ ΛΑΘΟΣ', 'why': 'ΓΙΑΤΙ', 'fix': 'ΚΑΝΕ ΑΥΤΟ'}

def tip_parts(m):
    """Σπάει τη σημείωση σε (ενέργεια, γιατί). Επιστρέφει '' όπου λείπει."""
    step = next((s for s in m.get('steps', []) if 'ΣΗΜΑΝΤΙΚΟ' in s), '')
    if not step: return '', ''
    head, _, why = step.partition('ΣΗΜΑΝΤΙΚΟ')
    why = why.lstrip(': ').strip()
    # Ο τίτλος του βήματος («Ζύμωμα:») δεν χρειάζεται στο βίντεο
    head = re.sub(r'^[^:]{0,28}:\s*', '', head).strip()
    return head, why

def reason_only(txt):
    """Κρατά ΜΟΝΟ την αιτία, πετώντας την επανάληψη της απαγόρευσης.

    Η σημείωση ξεκινά συνήθως ξαναλέγοντας το λάθος: «Μη ζυμώνεις υπερβολικά,
    γιατί ο κιμάς σφίγγει...». Το πρώτο καρέ το έχει ήδη πει, οπότε στο
    δεύτερο μένει σκέτη η αιτία, με κεφαλαίο στην αρχή."""
    t = txt.strip()
    for w in ('γιατί ', 'καθώς ', 'επειδή ', 'διότι '):
        i = t.lower().find(w)
        if 0 < i < 110:
            t = t[i + len(w):].strip()
            break
    return (t[0].upper() + t[1:]) if t else t

def first_sentence(txt, limit=170):
    """Η πρώτη ολοκληρωμένη πρόταση — το «γιατί» είναι συχνά δύο-τριών
    προτάσεων και στο βίντεο δεν προλαβαίνει να διαβαστεί καμία."""
    t = txt.strip()
    for end in ('. ', '· ', '— '):
        i = t.find(end)
        if 40 <= i <= limit: return t[:i + 1].strip()
    return (t[:limit].rsplit(' ', 1)[0] + '…') if len(t) > limit else t

def scrim(src, base, peak, top=0):
    g = Image.new('L', (1, H)); px = g.load()
    for y in range(H):
        f = 0 if y < top else (y - top) / max(1, H - top)
        px[0, y] = round(255 * (base + (peak - base) * min(1.0, f) ** 1.4))
    return Image.composite(Image.new('RGB', (W, H), INK), src, g.resize((W, H)))

def ease(p): return 1 - (1 - min(1.0, max(0.0, p))) ** 3

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

def tag(im, d, x, y, txt, fill):
    """Μικρή έγχρωμη ετικέτα πάνω από το κείμενο."""
    f = ImageFont.truetype(FB, 36)
    tw = d.textlength(txt, font=f)
    d.rounded_rectangle([x, y, x + tw + 44, y + 58], radius=29, fill=fill)
    d.text((x + 22, y + 10), txt, font=f, fill=(255, 255, 255))
    return y + 58

def build(rid):
    data = load(rid); m = data['m']
    hook = HOOKS.get(rid)
    if not hook:
        print(f'  ✗ {rid}: λείπει το κείμενο της απαγόρευσης από το HOOKS'); return
    action, why = tip_parts(m)
    why = first_sentence(reason_only(why))
    fix = FIX.get(rid) or first_sentence(action, 90)

    photo = Image.open(os.path.join(ROOT, data['img'])).convert('RGB')
    bg   = cover(photo, W, H)
    blur = bg.filter(ImageFilter.GaussianBlur(22))

    scenes = [('bad', 3.0), ('why', 3.4), ('fix', 2.4), ('cta', 1.9)]
    out = os.path.join(OUT, f'lathos-{rid}-el.mp4')
    proc = subprocess.Popen(
        [FFMPEG, '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
         '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21',
         '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    f_hook = ImageFont.truetype(FB, 78)
    f_body = ImageFont.truetype(FR, 44)
    f_fix  = ImageFont.truetype(FB, 54)

    for kind, secs in scenes:
        n = max(1, round(secs * FPS))
        for i in range(n):
            p = i / max(1, n - 1)
            if kind == 'bad':
                # Η φωτογραφία κινείται από το πρώτο καρέ — ακίνητο καρέ
                # διαβάζεται ως «δεν συμβαίνει τίποτα».
                z = 1.0 + .08 * p
                cw, ch = round(W / z), round(H / z)
                fr = bg.crop(((W - cw) // 2, (H - ch) // 2,
                              (W - cw) // 2 + cw, (H - ch) // 2 + ch)).resize((W, H), Image.LANCZOS)
                fr = scrim(fr, .30, .92, int(H * .22))
            else:
                fr = scrim(blur, .56, .80)
            d = ImageDraw.Draw(fr)

            if kind == 'bad':
                y = tag(fr, d, PAD, 470, L['bad'], BRICK) + 44
                for k, ln in enumerate(hook.split('\n')):
                    a = ease((p - .04 - k * .10) / .26)
                    if a <= .02: continue
                    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                    ImageDraw.Draw(ov).text((PAD, y + k * 96 + round(22 * (1 - a))), ln,
                                            font=f_hook, fill=CREAM)
                    fr = Image.alpha_composite(fr.convert('RGBA'),
                        ov if a >= .99 else _fade(ov, a)).convert('RGB')
            elif kind == 'why':
                y = tag(fr, d, PAD, 540, L['why'], (120, 78, 24)) + 40
                a = ease(p / .16)
                ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                od = ImageDraw.Draw(ov)
                for k, ln in enumerate(wrap(od, why, f_body, COLW)[:5]):
                    od.text((PAD, y + k * 60), ln, font=f_body, fill=CREAM)
                fr = Image.alpha_composite(fr.convert('RGBA'), _fade(ov, a)).convert('RGB')
            elif kind == 'fix':
                y = tag(fr, d, PAD, 560, L['fix'], (36, 122, 54)) + 44
                a = ease(p / .18)
                ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                od = ImageDraw.Draw(ov)
                for k, ln in enumerate(wrap(od, fix, f_fix, COLW)[:3]):
                    od.text((PAD, y + k * 72), ln, font=f_fix, fill=GOLD)
                od.text((PAD, y + 250), m['n'], font=ImageFont.truetype(FR, 40), fill=(206, 186, 158))
                fr = Image.alpha_composite(fr.convert('RGBA'), _fade(ov, a)).convert('RGB')
            else:
                a = ease(p / .22)
                ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                od = ImageDraw.Draw(ov)
                D_ = 128; L_ = logo(D_)
                ov.paste(L_, ((W - D_) // 2, 560), L_)
                f1 = ImageFont.truetype(FB, 64)
                od.text(((W - od.textlength('FoodDaily', font=f1)) / 2, 712), 'FoodDaily', font=f1, fill=CREAM)
                f2 = ImageFont.truetype(FR, 38)
                sub = 'Όλη η συνταγή στην εφαρμογή'
                od.text(((W - od.textlength(sub, font=f2)) / 2, 792), sub, font=f2, fill=GOLD)
                gp = badge(300); ov.paste(gp, ((W - 300) // 2, 866), gp)
                fr = Image.alpha_composite(fr.convert('RGBA'), _fade(ov, a)).convert('RGB')

            proc.stdin.write(fr.tobytes())

    proc.stdin.close(); proc.wait()
    dur = sum(s for _, s in scenes)
    print(f'  ✓ lathos-{rid}-el.mp4  {dur:.1f}s  {os.path.getsize(out)//1024} KB  «{hook.replace(chr(10)," ")}»')

def _fade(layer, a):
    if a >= .99: return layer
    l = layer.copy()
    l.putalpha(l.split()[3].point(lambda v: round(v * a)))
    return l

if __name__ == '__main__':
    ids = sys.argv[1:] or list(HOOKS)
    print(f'Reels «ΤΟ ΛΑΘΟΣ» — {len(ids)} βίντεο')
    for rid in ids:
        build(rid)
