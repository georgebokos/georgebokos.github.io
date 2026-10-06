# -*- coding: utf-8 -*-
"""Κατακόρυφα βίντεο που λένε ΓΙΑΤΙ να κατεβάσει κάποιος την εφαρμογή.

Διαφέρουν από τα `ads/reel.py`: εκείνα δείχνουν μία συνταγή και αναφέρουν την
εφαρμογή στο τέλος. Εδώ το θέμα είναι η ίδια η εφαρμογή — ξεκινά από το
πρόβλημα («βαρέθηκες να σκέφτεσαι τι θα φάτε»), δείχνει τι κάνει, και κλείνει
στο Google Play.

Τα κείμενα και οι λειτουργίες έρχονται αυτούσια από το `ads/feature_ads.py`,
ώστε εικόνα και βίντεο να μη λένε ποτέ διαφορετικά πράγματα.

Τέσσερα βίντεο, ένα ανά αφήγημα:
  A  «δεν είναι ότι δεν ξέρεις να μαγειρέψεις»
  B  «το ίντερνετ σού δίνει συνταγή όταν ξέρεις ήδη τι θες»
  C  «τι θα φάμε σήμερα;»
  D  μια μέρα με την εφαρμογή — χρονογραμμή

Χρήση:  python3 ads/feature_video.py [el|en] [A B C D]
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, subprocess, sys
import imageio_ffmpeg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_ads import (HERO, REST, T, N, LANGS, FB, FR, CREAM, WARM, GOLD,
                         BRICK, INK, PANEL, emoji, photo, wrap, fit, badge, logo)

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT    = os.path.join(ROOT, 'ads', 'feature-ads')
os.makedirs(OUT, exist_ok=True)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

W, H, FPS = 1080, 1920, 25
# Ασφαλής περιοχή TikTok/Reels: κάτω κάθεται η λεζάντα, δεξιά τα κουμπιά.
SAFE_B, SAFE_R, PAD = 400, 170, 72
COLW = W - PAD - SAFE_R

HOOKS = {
 'el': {
  'A': ['Δεν είναι ότι δεν ξέρεις', 'να μαγειρέψεις.', '', 'Είναι ότι βαρέθηκες', 'να σκέφτεσαι τι.'],
  'B': ['Το ίντερνετ σού δίνει', 'τη συνταγή όταν ξέρεις', 'ήδη τι θες.', '',
        'Το FoodDaily σού λέει', 'τι να φτιάξεις.'],
  'C': ['«Τι θα φάμε', 'σήμερα;»', '', 'Η απάντηση έρχεται', 'μόνη της κάθε πρωί.'],
  'D': ['Μια μέρα', 'με το FoodDaily'],
 },
 'en': {
  'A': ["It's not that you can't", 'cook.', '', "It's that you're tired", 'of deciding what.'],
  'B': ['The internet gives you', 'a recipe once you', 'already know what you want.', '',
        'FoodDaily tells you', 'what to make.'],
  'C': ['"What are we', 'eating today?"', '', 'The answer arrives', 'on its own, every morning.'],
  'D': ['A day', 'with FoodDaily'],
 },
}

VARIANTS = {
 'A': dict(pic='giouvetsi', mid='feats'),
 'B': dict(pic='moussaka',  mid='feats'),
 'C': dict(pic='souvlakia', mid='feats'),
 'D': dict(pic='kotopoulo', mid='day'),
}

def cover(im, w, h):
    r = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    return im.crop(((im.width - w) // 2, (im.height - h) // 2,
                    (im.width - w) // 2 + w, (im.height - h) // 2 + h))

def scrim(src, base, peak, top=0):
    """Σκούρο στρώμα που βαραίνει προς τα κάτω — χωρίς αυτό το κείμενο χάνεται
    πάνω σε φωτεινές φωτογραφίες φαγητού."""
    g = Image.new('L', (1, H)); px = g.load()
    for y in range(H):
        f = 0 if y < top else (y - top) / max(1, H - top)
        px[0, y] = round(255 * (base + (peak - base) * min(1.0, f) ** 1.4))
    return Image.composite(Image.new('RGB', (W, H), INK), src, g.resize((W, H)))

def ease(p):
    """Μαλακή είσοδος: το γραμμικό fade διαβάζεται ως «κολλάει το βίντεο»."""
    return 1 - (1 - min(1.0, max(0.0, p))) ** 3

def blend(dst, layer, a):
    if a <= 0.01: return dst
    if a >= 0.99: return Image.alpha_composite(dst, layer)
    l = layer.copy()
    l.putalpha(l.split()[3].point(lambda v: round(v * a)))
    return Image.alpha_composite(dst, l)

# --- τα στρώματα ------------------------------------------------------------
def layer_feat(lang, i):
    """Μία κύρια λειτουργία ως κάρτα, έτοιμη να μπει με fade + ολίσθηση."""
    e, n, desc, _s = HERO[lang][i]
    h = 150
    l = Image.new('RGBA', (COLW, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(l)
    d.rounded_rectangle([0, 0, COLW, h], radius=26, fill=PANEL + (236,))
    ic = emoji(e, 56); l.paste(ic, (28, 26), ic)
    d.text((110, 28), n, font=fit(d, n, COLW - 150, 40), fill=GOLD)
    f_d = ImageFont.truetype(FR, 28)
    yy = 84
    for ln in wrap(d, desc, f_d, COLW - 150)[:2]:
        d.text((110, yy), ln, font=f_d, fill=(228, 212, 190)); yy += 34
    return l

def layer_day(lang, i):
    (lbl, txt) = T[lang]['daytxt'][i]
    rid = ['kotopoulo', 'horiatiki', 'moussaka', 'baklava'][i]
    e   = ['🔔', '🛒', '🍳', '📤'][i]
    h, D_ = 150, 118
    l = Image.new('RGBA', (COLW, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(l)
    d.rounded_rectangle([0, 0, COLW, h], radius=26, fill=PANEL + (236,))
    th = photo(rid, D_, D_)
    m = Image.new('L', (D_ * 4, D_ * 4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, D_ * 4, D_ * 4], fill=255)
    th.putalpha(m.resize((D_, D_), Image.LANCZOS))
    l.paste(th, (16, 16), th)
    ic = emoji(e, 34); l.paste(ic, (152, 24), ic)
    d.text((198, 26), T[lang]['day'][i], font=ImageFont.truetype(FB, 30), fill=GOLD)
    d.text((152, 70), lbl, font=ImageFont.truetype(FB, 38), fill=CREAM)
    d.text((152, 114), wrap(d, txt, ImageFont.truetype(FR, 25), COLW - 180)[0],
           font=ImageFont.truetype(FR, 25), fill=(206, 186, 160))
    return l

def layer_rest(lang):
    """Οι υπόλοιπες δεκαέξι, σε δύο στήλες."""
    rows, rowh = 8, 48
    h = 56 + rows * rowh
    l = Image.new('RGBA', (COLW, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(l)
    d.text((4, 0), T[lang]['rest_hdr'], font=ImageFont.truetype(FB, 34), fill=GOLD)
    colw = COLW // 2
    for i, (e, n) in enumerate(REST[lang]):
        cx = 4 + (i % 2) * colw
        cy = 56 + (i // 2) * rowh
        ic = emoji(e, 32); l.paste(ic, (cx, cy + 2), ic)
        d.text((cx + 46, cy + 4), n, font=fit(d, n, colw - 60, 27, 15, bold=False),
               fill=(226, 210, 188))
    return l

def layer_cta(lang):
    l = Image.new('RGBA', (COLW, 430), (0, 0, 0, 0))
    d = ImageDraw.Draw(l)
    L = logo(118); l.paste(L, ((COLW - 118) // 2, 0), L)
    f1 = ImageFont.truetype(FB, 62)
    d.text(((COLW - d.textlength('FoodDaily', font=f1)) / 2, 136), 'FoodDaily', font=f1, fill=CREAM)
    f2 = ImageFont.truetype(FR, 34)
    k = T[lang]['kicker']
    d.text(((COLW - d.textlength(k, font=f2)) / 2, 212), k, font=f2, fill=WARM)
    # Η τριγλωσσία παίρνει δική της γραμμή: είναι ο λόγος που την κατεβάζει
    # κάποιος εκτός Ελλάδας, όχι υποσημείωση.
    f3 = ImageFont.truetype(FB, 32)
    d.text(((COLW - d.textlength(LANGS, font=f3)) / 2, 264), LANGS, font=f3, fill=GOLD)
    gp = badge(300); l.paste(gp, ((COLW - 300) // 2, 324), gp)
    return l

# --- η συναρμολόγηση --------------------------------------------------------
def build(key, lang):
    v = VARIANTS[key]
    hook = HOOKS[lang][key]
    src  = Image.open(os.path.join(ROOT, __import__('feature_ads').IMGS[v['pic']])).convert('RGB')
    bg   = cover(src, W, H)
    blur = cover(src, W, H).filter(ImageFilter.GaussianBlur(26))

    feats = [ (layer_day if v['mid'] == 'day' else layer_feat)(lang, i)
              for i in range(4 if v['mid'] == 'day' else 6) ]
    rest  = layer_rest(lang)
    cta   = layer_cta(lang)

    # Ο χρόνος κάθε σκηνής. Το hook κρατά όσο χρειάζεται για να διαβαστεί δύο
    # φορές — αυτό είναι το μόνο καρέ που κρίνει αν θα μείνει ο θεατής.
    t_hook = 3.6
    t_each = 1.15
    t_feat = t_each * len(feats) + 1.0
    t_rest = 3.0
    t_cta  = 3.0
    scenes = [('hook', t_hook), ('feat', t_feat), ('rest', t_rest), ('cta', t_cta)]

    out = os.path.join(OUT, f'video-{key}-{lang}.mp4')
    proc = subprocess.Popen(
        [FFMPEG, '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
         '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21',
         '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    f_h = ImageFont.truetype(FB, 64)
    LH  = 82

    for kind, secs in scenes:
        n = max(1, round(secs * FPS))
        for i in range(n):
            p = i / max(1, n - 1)
            if kind == 'hook':
                # Η φωτογραφία κινείται από το πρώτο καρέ: το ακίνητο καρέ
                # διαβάζεται ως «δεν συμβαίνει τίποτα» και ο θεατής φεύγει.
                z = 1.0 + .07 * p
                cw, chh = round(W / z), round(H / z)
                fr = bg.crop(((W - cw) // 2, (H - chh) // 2,
                              (W - cw) // 2 + cw, (H - chh) // 2 + chh)).resize((W, H), Image.LANCZOS)
                fr = scrim(fr, .34, .90, int(H * .30))
            else:
                fr = scrim(blur, .68, .86)
            fr = fr.convert('RGBA')

            if kind == 'hook':
                d = ImageDraw.Draw(fr)
                blk = len(hook) * LH
                y0 = (H - SAFE_B - blk) // 2 + 60
                # Οι γραμμές μπαίνουν σε δύο δόσεις, χωρισμένες στο κενό: η
                # δεύτερη είναι η ανατροπή και δεν πρέπει να διαβαστεί μαζί.
                cut = hook.index('') if '' in hook else len(hook)
                for k, ln in enumerate(hook):
                    a = ease((p - (0.05 if k < cut else 0.42)) / 0.28)
                    if a <= 0.02 or not ln: continue
                    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                    ImageDraw.Draw(ov).text((PAD, y0 + k * LH + round(26 * (1 - a))), ln,
                                            font=f_h, fill=CREAM)
                    fr = blend(fr, ov, a)
            elif kind == 'feat':
                y = 300
                for k, lay in enumerate(feats):
                    a = ease((p * secs - k * t_each) / 0.5)
                    if a <= 0.02: break
                    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                    ov.paste(lay, (PAD, y + round(34 * (1 - a))), lay)
                    fr = blend(fr, ov, a)
                    y += lay.height + 18
            elif kind == 'rest':
                a = ease(p / 0.22)
                ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                ov.paste(rest, (PAD, (H - SAFE_B - rest.height) // 2 + 70 - round(30 * (1 - a))), rest)
                fr = blend(fr, ov, a)
            else:
                a = ease(p / 0.22)
                ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                ov.paste(cta, (PAD, (H - SAFE_B - cta.height) // 2 + 40), cta)
                fr = blend(fr, ov, a)

            proc.stdin.write(fr.convert('RGB').tobytes())

    proc.stdin.close(); proc.wait()
    dur = sum(s for _, s in scenes)
    print(f'  ✓ video-{key}-{lang}.mp4  {dur:.1f}s  {os.path.getsize(out)//1024} KB')

if __name__ == '__main__':
    args = sys.argv[1:]
    lang = args[0] if args and args[0] in ('el', 'en') else 'el'
    keys = [a for a in args if a in VARIANTS] or ['A', 'B', 'C', 'D']
    print(f'Βίντεο λειτουργιών ({lang}) — {N} συνταγές')
    for k in keys:
        build(k, lang)
