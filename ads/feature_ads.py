# -*- coding: utf-8 -*-
"""Διαφημιστικές εικόνες που δείχνουν ΤΙ ΚΑΝΕΙ η εφαρμογή, όχι μόνο ότι υπάρχει.

Οι προηγούμενες εικόνες (`ads/images.py`) λένε «397 συνταγές» και τίποτα άλλο:
δουλεύουν ως υπενθύμιση σε όποιον ξέρει ήδη την εφαρμογή, αλλά δεν πείθουν
κανέναν που τη βλέπει πρώτη φορά. Εδώ κάθε λειτουργία γράφεται ρητά.

Τέσσερα προσχέδια, ώστε να διαλέξει ο χρήστης:
  A  πλακίδια   — φωτογραφία πάνω, έξι λειτουργίες σε πλέγμα
  B  τηλέφωνο   — συσκευή στο κέντρο, οι λειτουργίες γύρω της
  C  λίστα      — σκούρο φόντο, δέκα λειτουργίες η μία κάτω από την άλλη
  D  μια μέρα   — χρονογραμμή: πρωί → σούπερ μάρκετ → κουζίνα → τραπέζι

Χρήση:  python3 ads/feature_ads.py [el|en]
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, 'ads', 'feature-ads')
os.makedirs(OUT, exist_ok=True)
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
EMOJI = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'

W, H = 1080, 1350          # 4:5 — η αναλογία που πιάνει το μεγαλύτερο ύψος
                           # στο feed του Instagram και του Facebook

CREAM = (255, 253, 248)
WARM  = (240, 216, 174)
GOLD  = (247, 198, 104)
BRICK = (200, 80, 26)
INK   = (22, 13, 4)

# Ο αριθμός συνταγών ΔΕΝ γράφεται με το χέρι — διαβάζεται από το index.html,
# όπως και στο captions.py, αλλιώς μένει πίσω με την πρώτη προσθήκη.
_html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
IMGS  = dict(re.findall(r"(\w+):'(images/[\w.\-]+)'", _html))

def n_meals():
    i = _html.index('const MEALS={')
    j = _html.index('\n};', i)
    return len(re.findall(r'^\s{0,2}(\w+)\s*:\s*\{', _html[i:j], re.M))

N = n_meals()

# --- Οι λειτουργίες ---------------------------------------------------------
# Κάθε γραμμή: εικονίδιο, τίτλος, μία σειρά εξήγησης. Η εξήγηση λέει ΤΙ
# κερδίζει ο χρήστης, όχι πώς λέγεται η λειτουργία.
FEATS = {
 'el': [
  ('🔔', 'Καθημερινή ειδοποίηση', 'Μια πρόταση φαγητού κάθε μέρα — τέλος το «τι θα φάμε;»'),
  ('🛒', 'Λίστα αγορών με ένα κλικ', 'Τσεκάρεις όσα υλικά σου λείπουν και τα στέλνεις σε όποιον θες'),
  ('🍳', 'Cook Mode', 'Βήμα-βήμα σε πλήρη οθόνη — η οθόνη δεν σβήνει ενώ μαγειρεύεις'),
  ('⏱️', 'Χρονόμετρο σε κάθε βήμα', 'Χτυπάει μόνο του όταν τελειώσει ο χρόνος'),
  ('✍️', 'Ανέβασε τη δική σου συνταγή', 'Η συνταγή της γιαγιάς σου, σε όλη την Ελλάδα'),
  ('🧊', 'Τι έχεις στο ψυγείο;', 'Γράφεις τα υλικά που περίσσεψαν και βρίσκει τι να μαγειρέψεις'),
  ('📅', 'Εβδομαδιαίο πλάνο', 'Μενού για όλη τη βδομάδα με ένα πάτημα'),
  ('👥', 'Μενού για καλεσμένους', 'Έτοιμη πρόταση όταν έχεις τραπέζι'),
  ('📴', 'Δουλεύει χωρίς ίντερνετ', f'Και οι {N} συνταγές διαθέσιμες offline'),
  ('🌍', 'Τρεις γλώσσες', 'Ελληνικά · English · Deutsch'),
  ('❤️', 'Αγαπημένα', 'Οι συνταγές σου πάντα ένα πάτημα μακριά'),
  ('🚫', 'Κρύβει ό,τι δεν τρως', 'Διαλέγεις υλικά που δεν σου αρέσουν και φεύγουν'),
 ],
 'en': [
  ('🔔', 'A reminder every day', 'One meal idea a day — no more "what shall we cook?"'),
  ('🛒', 'Shopping list in one tap', 'Tick what you are missing and send it to anyone'),
  ('🍳', 'Cook Mode', 'Full-screen steps — the screen stays on while you cook'),
  ('⏱️', 'A timer on every step', 'It rings by itself when the time is up'),
  ('✍️', 'Upload your own recipe', "Your grandmother's recipe, shared with everyone"),
  ('🧊', "What's in your fridge?", 'Type what is left over and it finds what to cook'),
  ('📅', 'Weekly meal plan', 'A menu for the whole week in one tap'),
  ('👥', 'Menu for guests', 'A ready suggestion when people are coming over'),
  ('📴', 'Works without internet', f'All {N} recipes available offline'),
  ('🌍', 'Three languages', 'Ελληνικά · English · Deutsch'),
  ('❤️', 'Favourites', 'Your recipes always one tap away'),
  ('🚫', 'Hides what you will not eat', 'Pick the ingredients you dislike and they are gone'),
 ],
}

T = {
 'el': {'title': 'Τι μαγειρεύουμε\nσήμερα;',
        'kicker': f'{N} ελληνικές συνταγές',
        'lead': 'Δεν είναι απλώς συνταγές —\nείναι όλη η κουζίνα στο κινητό σου',
        'cta': 'Δωρεάν στο Google Play',
        'allfeat': 'Και ακόμα: εβδομαδιαίο πλάνο · μενού καλεσμένων · αγαπημένα · τρεις γλώσσες',
        'day': ['07:30', '18:00', '19:15', '20:00'],
        'daytxt': [('Η ειδοποίηση', 'Σήμερα: Γιουβέτσι αρνί'),
                   ('Το σούπερ μάρκετ', 'Η λίστα αγορών, έτοιμη στο κινητό'),
                   ('Η κουζίνα', 'Cook Mode — η οθόνη δεν σβήνει'),
                   ('Το τραπέζι', 'Και η συνταγή φεύγει στην παρέα')],
        'dayt': 'Μια μέρα με το FoodDaily'},
 'en': {'title': 'What are we\ncooking today?',
        'kicker': f'{N} Greek recipes',
        'lead': 'Not just recipes —\nthe whole kitchen in your pocket',
        'cta': 'Free on Google Play',
        'allfeat': 'Plus: weekly plan · menu for guests · favourites · three languages',
        'day': ['07:30', '18:00', '19:15', '20:00'],
        'daytxt': [('The reminder', "Today: Lamb giouvetsi"),
                   ('The supermarket', 'The shopping list, ready on your phone'),
                   ('The kitchen', 'Cook Mode — the screen stays on'),
                   ('The table', 'And the recipe goes to your friends')],
        'dayt': 'A day with FoodDaily'},
}

# ---------------------------------------------------------------------------
_ecache = {}
def emoji(ch, px):
    """Το NotoColorEmoji είναι bitmap και υπάρχει ΜΟΝΟ στα 109px: ζωγραφίζεται
    εκεί και σμικρύνεται, αλλιώς το PIL πετά «invalid pixel size»."""
    key = (ch, px)
    if key not in _ecache:
        f = ImageFont.truetype(EMOJI, 109)
        im = Image.new('RGBA', (140, 140), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((10, 8), ch, font=f, embedded_color=True)
        bb = im.getbbox() or (0, 0, 140, 140)
        im = im.crop(bb)
        s = px / max(im.width, im.height)
        _ecache[key] = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))),
                                 Image.LANCZOS)
    return _ecache[key]

def photo(rid, w, h):
    im = Image.open(os.path.join(ROOT, IMGS[rid])).convert('RGB')
    r = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    return im.crop(((im.width - w) // 2, (im.height - h) // 2,
                    (im.width - w) // 2 + w, (im.height - h) // 2 + h))

def wrap(d, txt, f, maxw):
    out, cur = [], ''
    for w_ in txt.split():
        t = (cur + ' ' + w_).strip()
        if d.textlength(t, font=f) <= maxw or not cur: cur = t
        else: out.append(cur); cur = w_
    if cur: out.append(cur)
    return out

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

def cta_bar(im, y, lang, pad=64):
    """Σήμα Google Play + γραμμή «δωρεάν», κοινό σε όλα τα προσχέδια."""
    d = ImageDraw.Draw(im)
    gp = badge(300)
    im.paste(gp, (pad, y), gp)
    f = ImageFont.truetype(FB, 34)
    d.text((pad + 330, y + (gp.height - 42) // 2), T[lang]['cta'], font=f, fill=WARM)
    return y + gp.height

def header(im, lang, y=56, pad=64, light=True):
    d = ImageDraw.Draw(im)
    L = logo(92)
    im.paste(L, (pad, y), L)
    col = CREAM if light else INK
    d.text((pad + 116, y + 6), 'FoodDaily', font=ImageFont.truetype(FB, 48), fill=col)
    d.text((pad + 118, y + 60), T[lang]['kicker'], font=ImageFont.truetype(FR, 30), fill=GOLD)
    return y + 112

def save(im, name, lang):
    p = os.path.join(OUT, f'{name}-{lang}.png')
    im.save(p, 'PNG', optimize=True)
    print(f'  ✓ {os.path.basename(p)}  {im.width}×{im.height}  {os.path.getsize(p)//1024} KB')

# --- A: φωτογραφία πάνω, έξι λειτουργίες σε πλακίδια ------------------------
SHORT_A = {
 'el': {'Καθημερινή ειδοποίηση': 'Μια πρόταση φαγητού κάθε μέρα',
        'Λίστα αγορών με ένα κλικ': 'Τσεκάρεις τα υλικά και τα στέλνεις',
        'Cook Mode': 'Βήμα-βήμα, χωρίς να σβήνει η οθόνη',
        'Χρονόμετρο σε κάθε βήμα': 'Χτυπάει μόνο του στην ώρα του',
        'Ανέβασε τη δική σου συνταγή': 'Η συνταγή της γιαγιάς, παντού',
        'Τι έχεις στο ψυγείο;': 'Βάζεις ό,τι περίσσεψε, βρίσκει πιάτο'},
 'en': {'A reminder every day': 'One meal idea, every single day',
        'Shopping list in one tap': 'Tick the items and send them off',
        'Cook Mode': 'Step by step, screen never sleeps',
        'A timer on every step': 'It rings by itself, right on time',
        'Upload your own recipe': "Grandma's recipe, shared with all",
        "What's in your fridge?": 'Type the leftovers, get a dish'},
}

def draft_a(lang):
    F = [(e, n, SHORT_A[lang].get(n, dsc)) for e, n, dsc in FEATS[lang][:6]]
    im = Image.new('RGB', (W, H), INK)
    ph = 560
    p = photo('giouvetsi', W, ph)
    # Βαθμίδα προς τα κάτω, ώστε η φωτογραφία να λιώνει μέσα στο σκούρο πάνελ
    g = Image.new('L', (1, ph)); px = g.load()
    for y in range(ph):
        f = max(0.0, (y - ph * .45) / (ph * .55))
        px[0, y] = round(255 * (0.25 + 0.75 * f ** 1.4))
    im.paste(Image.composite(Image.new('RGB', (W, ph), INK), p, g.resize((W, ph))), (0, 0))
    d = ImageDraw.Draw(im)
    header(im, lang)

    f_t = ImageFont.truetype(FB, 72)
    y = 300
    for ln in T[lang]['title'].split('\n'):
        d.text((64, y), ln, font=f_t, fill=CREAM); y += 84

    # Πλέγμα 2×3
    f_n = ImageFont.truetype(FB, 31)
    f_d = ImageFont.truetype(FR, 25)
    gx, gy, cw, ch_ = 56, 572, (W - 56 * 2 - 24) // 2, 186
    for i, (e, n, desc) in enumerate(F):
        cx = gx + (i % 2) * (cw + 24)
        cy = gy + (i // 2) * (ch_ + 18)
        d.rounded_rectangle([cx, cy, cx + cw, cy + ch_], radius=26, fill=(38, 25, 12))
        ic = emoji(e, 54); im.paste(ic, (cx + 26, cy + 24), ic)
        d.text((cx + 26, cy + 92), n, font=f_n, fill=GOLD) if d.textlength(n, font=f_n) <= cw - 52 \
            else d.text((cx + 26, cy + 92), n, font=ImageFont.truetype(FB, 27), fill=GOLD)
        yy = cy + 92 + 40
        for ln in wrap(d, desc, f_d, cw - 52)[:2]:
            d.text((cx + 26, yy), ln, font=f_d, fill=(226, 206, 180)); yy += 32

    d.text((56, 1188), T[lang]['allfeat'], font=ImageFont.truetype(FR, 23), fill=(176, 152, 122))
    cta_bar(im, 1224, lang, pad=56)
    save(im, 'A-plakidia', lang)

# --- B: τηλέφωνο στο κέντρο, λειτουργίες γύρω -------------------------------
def draft_b(lang):
    im = Image.new('RGB', (W, H), (26, 16, 6))
    # Ζεστή λάμψη πίσω από τη συσκευή
    glow = Image.new('RGB', (W, H), (26, 16, 6)); gp_ = glow.load()
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            dd = (((x - W / 2) / 620) ** 2 + ((y - H * .52) / 700) ** 2) ** .5
            v = max(0.0, 1 - dd) ** 2
            c = (round(26 + 62 * v), round(16 + 36 * v), round(6 + 10 * v))
            for oy in (0, 1):
                for ox in (0, 1):
                    if x + ox < W and y + oy < H: gp_[x + ox, y + oy] = c
    im = glow
    d = ImageDraw.Draw(im)
    header(im, lang)

    f_t = ImageFont.truetype(FB, 46)
    y = 200
    for ln in T[lang]['lead'].split('\n'):
        tw = d.textlength(ln, font=f_t)
        d.text(((W - tw) / 2, y), ln, font=f_t, fill=CREAM); y += 58

    # Η συσκευή: φωτογραφία συνταγής με επικάλυψη «βήμα + χρονόμετρο», δηλαδή
    # ακριβώς αυτό που βλέπει ο χρήστης σε Cook Mode.
    PW, PH, R = 372, 744, 46
    dev = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
    dd_ = ImageDraw.Draw(dev)
    dd_.rounded_rectangle([0, 0, PW, PH], radius=R, fill=(12, 8, 3, 255))
    scr = photo('moussaka', PW - 20, PH - 20)
    sc = ImageDraw.Draw(scr)
    sc.rectangle([0, 0, PW, 230], fill=None)
    ov = Image.new('RGBA', scr.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).rectangle([0, PH - 320, PW, PH], fill=(16, 10, 3, 215))
    scr = Image.alpha_composite(scr.convert('RGBA'), ov)
    sd = ImageDraw.Draw(scr)
    sd.text((28, PH - 296), 'ΒΗΜΑ 4 / 8' if lang == 'el' else 'STEP 4 / 8',
            font=ImageFont.truetype(FB, 24), fill=GOLD)
    step = ('Στρώνεις τις πατάτες και από πάνω τον κιμά' if lang == 'el'
            else 'Layer the potatoes, then the mince on top')
    yy = PH - 252
    for ln in wrap(sd, step, ImageFont.truetype(FR, 28), PW - 76)[:3]:
        sd.text((28, yy), ln, font=ImageFont.truetype(FR, 28), fill=CREAM); yy += 38
    sd.rounded_rectangle([28, PH - 118, 196, PH - 54], radius=32, fill=BRICK)
    tm = emoji('⏱️', 34); scr.paste(tm, (46, PH - 109), tm)
    sd.text((92, PH - 106), '12:00', font=ImageFont.truetype(FB, 32), fill=(255, 255, 255))
    m = Image.new('L', scr.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, scr.width, scr.height], radius=R - 8, fill=255)
    dev.paste(scr.convert('RGB'), (10, 10), m)
    sh = Image.new('RGBA', (PW + 120, PH + 120), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([60, 70, 60 + PW, 70 + PH], radius=R, fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(28))
    im.paste(sh, ((W - sh.width) // 2, 400 - 60), sh)
    im.paste(dev, ((W - PW) // 2, 400), dev)

    # Έξι λειτουργίες, τρεις αριστερά και τρεις δεξιά της συσκευής
    SHORT = {'Λίστα αγορών με ένα κλικ':'Λίστα αγορών','Καθημερινή ειδοποίηση':'Καθημερινή πρόταση','Χρονόμετρο σε κάθε βήμα':'Χρονόμετρο στο βήμα','Ανέβασε τη δική σου συνταγή':'Η δική σου συνταγή','Shopping list in one tap':'Shopping list','A reminder every day':'A daily idea','A timer on every step':'Timer on each step','Upload your own recipe':'Your own recipe'}
    short = lambda t: SHORT.get(t, t)
    L = [FEATS[lang][i] for i in (0, 2, 3)]
    R_ = [FEATS[lang][i] for i in (1, 5, 4)]
    MARGIN = 48
    def fit(txt, avail, start=26, low=18):
        """Η μεγαλύτερη γραμματοσειρά που χωρά· καμία ετικέτα δεν κόβεται."""
        for sz in range(start, low - 1, -1):
            f = ImageFont.truetype(FB, sz)
            if d.textlength(txt, font=f) <= avail: return f
        return ImageFont.truetype(FB, low)

    def side(items, x, align_r):
        avail = (x - 56 - MARGIN) if align_r else (W - MARGIN - x - 56)
        yy = 452
        for e, n, _ in items:
            n = short(n)
            f_n = fit(n, avail)
            ic = emoji(e, 42)
            tw = d.textlength(n, font=f_n)
            if align_r:
                im.paste(ic, (x - 42, yy), ic)
                d.text((x - 56 - tw, yy + 6), n, font=f_n, fill=CREAM)
            else:
                im.paste(ic, (x, yy), ic)
                d.text((x + 56, yy + 6), n, font=f_n, fill=CREAM)
            yy += 206
    side(L, 318, True)
    side(R_, 762, False)

    cta = T[lang]['cta']
    gp2 = badge(290)
    tot = gp2.width + 24 + d.textlength(cta, font=ImageFont.truetype(FB, 32))
    x0 = (W - tot) / 2
    im.paste(gp2, (round(x0), 1218), gp2)
    d.text((x0 + gp2.width + 24, 1218 + (gp2.height - 40) // 2), cta,
           font=ImageFont.truetype(FB, 32), fill=WARM)
    save(im, 'B-tilefono', lang)

# --- C: καθαρή λίστα, δέκα λειτουργίες --------------------------------------
def draft_c(lang):
    F = FEATS[lang][:9]
    im = Image.new('RGB', (W, H), (250, 245, 236))
    d = ImageDraw.Draw(im)
    # Λωρίδα φωτογραφίας στην κορυφή, μόνο για να πει «φαγητό» με τη μία
    band = 300
    p = photo('souvlakia', W, band)
    ov = Image.new('RGBA', (W, band), (0, 0, 0, 0))
    ImageDraw.Draw(ov).rectangle([0, 0, W, band], fill=(20, 12, 3, 150))
    im.paste(Image.alpha_composite(p.convert('RGBA'), ov).convert('RGB'), (0, 0))
    header(im, lang, y=46)
    f_t = ImageFont.truetype(FB, 56)
    d.text((64, 176), T[lang]['title'].replace('\n', ' '), font=f_t, fill=CREAM)

    y = band + 46
    f_n = ImageFont.truetype(FB, 32)
    f_d = ImageFont.truetype(FR, 25)
    for e, n, desc in F:
        ic = emoji(e, 46); im.paste(ic, (64, y + 4), ic)
        d.text((136, y), n, font=f_n, fill=(58, 34, 10))
        d.text((136, y + 42), wrap(d, desc, f_d, W - 200)[0], font=f_d, fill=(126, 104, 80))
        y += 96
        if y < H - 210:
            d.line([136, y - 18, W - 64, y - 18], fill=(226, 214, 196), width=2)

    d.rounded_rectangle([0, H - 150, W, H], fill=INK)
    cta_bar(im, H - 120, lang)
    save(im, 'C-lista', lang)

# --- D: μια μέρα με την εφαρμογή --------------------------------------------
def draft_d(lang):
    im = Image.new('RGB', (W, H), INK)
    d = ImageDraw.Draw(im)
    header(im, lang)
    f_t = ImageFont.truetype(FB, 58)
    d.text((64, 190), T[lang]['dayt'], font=f_t, fill=CREAM)
    d.text((64, 262), T[lang]['lead'].replace('\n', ' '),
           font=ImageFont.truetype(FR, 27), fill=(188, 164, 134))

    shots = ['kotopoulo', 'horiatiki', 'moussaka', 'baklava']
    icons = ['🔔', '🛒', '🍳', '📤']
    y0, step = 356, 196
    d.line([116, y0 + 60, 116, y0 + step * 3 + 60], fill=(74, 50, 22), width=4)
    for i, ((lbl, txt), rid, e) in enumerate(zip(T[lang]['daytxt'], shots, icons)):
        y = y0 + i * step
        # Μικρή στρογγυλή φωτογραφία πάνω στη χρονογραμμή
        D_ = 120
        th = photo(rid, D_, D_)
        m = Image.new('L', (D_ * 4, D_ * 4), 0)
        ImageDraw.Draw(m).ellipse([0, 0, D_ * 4, D_ * 4], fill=255)
        th.putalpha(m.resize((D_, D_), Image.LANCZOS))
        d.ellipse([56 - 6, y - 6, 56 + D_ + 6, y + D_ + 6], fill=(74, 50, 22))
        im.paste(th, (56, y), th)
        ic = emoji(e, 44); im.paste(ic, (204, y + 2), ic)
        d.text((266, y + 6), T[lang]['day'][i], font=ImageFont.truetype(FB, 30), fill=GOLD)
        d.text((204, y + 58), lbl, font=ImageFont.truetype(FB, 38), fill=CREAM)
        for k, ln in enumerate(wrap(d, txt, ImageFont.truetype(FR, 27), W - 290)[:2]):
            d.text((204, y + 106 + k * 34), ln, font=ImageFont.truetype(FR, 27), fill=(198, 176, 148))

    d.rounded_rectangle([56, 1120, W - 56, 1216], radius=24, fill=(38, 25, 12))
    d.text((88, 1142), T[lang]['allfeat'], font=ImageFont.truetype(FR, 23), fill=(206, 186, 158))
    d.text((88, 1174), f"{N} " + ('συνταγές · χωρίς ίντερνετ · τρεις γλώσσες' if lang == 'el'
                                  else 'recipes · offline · three languages'),
           font=ImageFont.truetype(FB, 24), fill=GOLD)
    cta_bar(im, 1244, lang, pad=56)
    save(im, 'D-mia-mera', lang)

if __name__ == '__main__':
    lang = sys.argv[1] if len(sys.argv) > 1 else 'el'
    print(f'Προσχέδια διαφήμισης ({lang}) — {N} συνταγές')
    draft_a(lang); draft_b(lang); draft_c(lang); draft_d(lang)
