# -*- coding: utf-8 -*-
"""Διαφημιστικές εικόνες που δείχνουν ΤΙ ΚΑΝΕΙ η εφαρμογή, όχι μόνο ότι υπάρχει.

Οι προηγούμενες εικόνες (`ads/images.py`) λένε «397 συνταγές» και τίποτα άλλο:
δουλεύουν ως υπενθύμιση σε όποιον ξέρει ήδη την εφαρμογή, αλλά δεν πείθουν
κανέναν που τη βλέπει πρώτη φορά. Εδώ γράφεται ρητά **κάθε** λειτουργία.

Και τα τέσσερα σχέδια δείχνουν ΟΛΟΚΛΗΡΗ τη λίστα, με την ίδια δομή:
  έξι κύριες λειτουργίες με εξήγηση  +  όλες οι υπόλοιπες ως ετικέτες.
Αλλάζει μόνο ο τρόπος που παρουσιάζονται:

  A  πλακίδια   — φωτογραφία πάνω, οι κύριες σε πλέγμα
  B  τηλέφωνο   — συσκευή σε Cook Mode, οι κύριες γύρω της
  C  λίστα      — ανοιχτό φόντο, η μία κάτω από την άλλη
  D  μια μέρα   — χρονογραμμή: πρωί → σούπερ μάρκετ → κουζίνα → τραπέζι

Η τριγλωσσία μπαίνει ξεχωριστά, σε δική της λωρίδα κάτω από το λογότυπο: δεν
είναι μία λειτουργία ανάμεσα σε άλλες, είναι ο λόγος που την κατεβάζει κάποιος
εκτός Ελλάδας.

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
PANEL = (38, 25, 12)

# Ο αριθμός συνταγών ΔΕΝ γράφεται με το χέρι — διαβάζεται από το index.html,
# όπως και στο captions.py, αλλιώς μένει πίσω με την πρώτη προσθήκη.
_html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
IMGS  = dict(re.findall(r"(\w+):'(images/[\w.\-]+)'", _html))

def n_meals():
    i = _html.index('const MEALS={')
    j = _html.index('\n};', i)
    return len(re.findall(r'^\s{0,2}(\w+)\s*:\s*\{', _html[i:j], re.M))

N = n_meals()

# --- Οι κύριες λειτουργίες --------------------------------------------------
# Εικονίδιο, τίτλος, μία σειρά εξήγησης, και σύντομη εκδοχή του τίτλου για
# όπου ο χώρος είναι στενός. Η εξήγηση λέει ΤΙ κερδίζει ο χρήστης, όχι πώς
# λέγεται η λειτουργία.
HERO = {
 'el': [
  ('🔔', '12 προτάσεις κάθε μέρα', 'Μία ξεχωρίζει για σήμερα — και με ένα κλικ, 12 νέες', '12 προτάσεις τη μέρα'),
  ('🛒', 'Λίστα αγορών με ένα κλικ', 'Τσεκάρεις τα υλικά και τα στέλνεις', 'Λίστα αγορών'),
  ('🍳', 'Cook Mode', 'Βήμα-βήμα, χωρίς να σβήνει η οθόνη', 'Cook Mode'),
  ('⏱️', 'Χρονόμετρο σε κάθε βήμα', 'Χτυπάει μόνο του στην ώρα του', 'Χρονόμετρο στο βήμα'),
  ('✍️', 'Ανέβασε τη δική σου συνταγή', 'Η συνταγή της γιαγιάς, παντού', 'Η δική σου συνταγή'),
  ('🧊', 'Τι έχεις στο ψυγείο;', 'Βάζεις ό,τι περίσσεψε, βρίσκει πιάτο', 'Τι έχεις στο ψυγείο'),
 ],
 'en': [
  ('🔔', '12 ideas every day', 'One stands out for today — one tap, 12 new ones', '12 ideas a day'),
  ('🛒', 'Shopping list in one tap', 'Tick the items and send them off', 'Shopping list'),
  ('🍳', 'Cook Mode', 'Step by step, screen never sleeps', 'Cook Mode'),
  ('⏱️', 'A timer on every step', 'It rings by itself, right on time', 'Timer on each step'),
  ('✍️', 'Upload your own recipe', "Grandma's recipe, shared with all", 'Your own recipe'),
  ('🧊', "What's in your fridge?", 'Type the leftovers, get a dish', "What's in the fridge"),
 ],
}

# --- Όλες οι υπόλοιπες ------------------------------------------------------
# Δεκαέξι, ώστε να πέφτουν καθαρά σε πλέγμα 2×8 ή 4×4 χωρίς κενά κελιά.
REST = {
 'el': [
  ('📅', 'Εβδομαδιαίο πλάνο'),  ('👥', 'Μενού καλεσμένων'),
  ('🎉', 'Εορτές με έθιμα'),    ('🌿', 'Οδηγός εποχής'),
  ('➕', 'Μερίδες που αλλάζουν'), ('💰', 'Κόστος ανά μερίδα'),
  ('🔊', 'Σου τη διαβάζει'),    ('⏰', 'Μαγειρεύω απόψε'),
  ('🍷', 'Κρασί & σερβίρισμα'), ('🥗', 'Συνοδευτικά'),
  ('🧪', 'Θρεπτικά & vegan'),   ('📤', 'Κοινοποίηση'),
  ('📝', 'Προσωπικές σημειώσεις'), ('❤️', 'Αγαπημένα'),
  ('🚫', 'Κρύβει ό,τι δεν τρως'), ('📴', 'Χωρίς ίντερνετ'),
 ],
 'en': [
  ('📅', 'Weekly meal plan'),  ('👥', 'Menu for guests'),
  ('🎉', 'Feasts & customs'),  ('🌿', "What's in season"),
  ('➕', 'Servings that scale'), ('💰', 'Cost per serving'),
  ('🔊', 'It reads it out'),   ('⏰', 'Reminds you to start'),
  ('🍷', 'Wine & plating'),    ('🥗', 'Side dishes'),
  ('🧪', 'Nutrition & vegan'), ('📤', 'Share as a card'),
  ('📝', 'Private notes'),     ('❤️', 'Favourites'),
  ('🚫', 'Hides what you avoid'), ('📴', 'Works offline'),
 ],
}

LANGS = 'Ελληνικά · English · Deutsch'

T = {
 'el': {'title': 'Τι μαγειρεύουμε\nσήμερα;',
        'kicker': f'{N} ελληνικές συνταγές',
        'lead': 'Δεν είναι απλώς συνταγές —\nείναι όλη η κουζίνα στο κινητό σου',
        'cta': 'Δωρεάν στο Google Play',
        'rest_hdr': 'Και όλα αυτά μαζί',
        'langline': 'Σε τρεις γλώσσες',
        'day': ['07:30', '18:00', '19:15', '20:00'],
        'daytxt': [('Οι 12 προτάσεις', 'Σήμερα ξεχωρίζει: Γιουβέτσι αρνί'),
                   ('Το σούπερ μάρκετ', 'Η λίστα αγορών, έτοιμη στο κινητό'),
                   ('Η κουζίνα', 'Cook Mode — η οθόνη δεν σβήνει'),
                   ('Το τραπέζι', 'Και η συνταγή φεύγει στην παρέα')],
        'dayt': 'Μια μέρα με το FoodDaily',
        'allt': 'Όλες οι λειτουργίες'},
 'en': {'title': 'What are we\ncooking today?',
        'kicker': f'{N} Greek recipes',
        'lead': 'Not just recipes —\nthe whole kitchen in your pocket',
        'cta': 'Free on Google Play',
        'rest_hdr': 'And all of this too',
        'langline': 'In three languages',
        'day': ['07:30', '18:00', '19:15', '20:00'],
        'daytxt': [('The 12 ideas', 'Today it picks: Lamb giouvetsi'),
                   ('The supermarket', 'The shopping list, ready on your phone'),
                   ('The kitchen', 'Cook Mode — the screen stays on'),
                   ('The table', 'And the recipe goes to your friends')],
        'dayt': 'A day with FoodDaily',
        'allt': 'Everything it does'},
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

def fit(d, txt, avail, start, low=15, bold=True):
    """Η μεγαλύτερη γραμματοσειρά που χωρά στον διαθέσιμο χώρο.

    Κάθε ετικέτα μετριέται πριν ζωγραφιστεί· χωρίς αυτό οι μεγάλοι ελληνικοί
    τίτλοι έβγαιναν έξω από την εικόνα και κόβονταν στη μέση."""
    path = FB if bold else FR
    for sz in range(start, low - 1, -1):
        f = ImageFont.truetype(path, sz)
        if d.textlength(txt, font=f) <= avail: return f
    return ImageFont.truetype(path, low)

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

def cta_bar(im, y, lang, pad=56, center=False):
    d = ImageDraw.Draw(im)
    gp = badge(286)
    f = ImageFont.truetype(FB, 32)
    tw = d.textlength(T[lang]['cta'], font=f)
    x = round((W - (gp.width + 24 + tw)) / 2) if center else pad
    im.paste(gp, (x, y), gp)
    d.text((x + gp.width + 24, y + (gp.height - 40) // 2), T[lang]['cta'], font=f, fill=WARM)
    return y + gp.height

def header(im, lang, y=52, pad=56, dark_text=False):
    d = ImageDraw.Draw(im)
    L = logo(88)
    im.paste(L, (pad, y), L)
    d.text((pad + 110, y + 2), 'FoodDaily', font=ImageFont.truetype(FB, 46),
           fill=INK if dark_text else CREAM)
    d.text((pad + 112, y + 54), T[lang]['kicker'], font=ImageFont.truetype(FR, 28), fill=GOLD)
    return y + 100

def lang_pill(im, y, lang, pad=56, x=None, light_bg=False):
    """Η τριγλωσσία σε δική της λωρίδα — είναι επιχείρημα, όχι υποσημείωση."""
    d = ImageDraw.Draw(im)
    f1 = ImageFont.truetype(FB, 26)
    f2 = ImageFont.truetype(FB, 27)
    ic = emoji('🌍', 32)
    txt = T[lang]['langline'] + ':  '
    w = 26 + ic.width + 14 + d.textlength(txt, font=f1) + d.textlength(LANGS, font=f2) + 26
    x = pad if x is None else round(x - w / 2)
    h = 58
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2,
                        fill=(60, 40, 18) if not light_bg else (246, 234, 214))
    im.paste(ic, (x + 24, y + 13), ic)
    cx = x + 24 + ic.width + 14
    col = WARM if not light_bg else (122, 86, 40)
    d.text((cx, y + 16), txt, font=f1, fill=col)
    d.text((cx + d.textlength(txt, font=f1), y + 15), LANGS, font=f2,
           fill=GOLD if not light_bg else (168, 92, 24))
    return y + h

def rest_block(im, y, lang, cols=3, pad=56, light=False, title=True, rowh=40, fsz=22):
    """Οι υπόλοιπες λειτουργίες ως πλέγμα από εικονίδιο + ετικέτα."""
    d = ImageDraw.Draw(im)
    if title:
        d.text((pad, y), T[lang]['rest_hdr'], font=ImageFont.truetype(FB, 28),
               fill=GOLD if not light else (168, 92, 24))
        y += 44
    items = REST[lang]
    colw = (W - pad * 2) // cols
    rows = (len(items) + cols - 1) // cols
    for i, (e, n) in enumerate(items):
        cx = pad + (i % cols) * colw
        cy = y + (i // cols) * rowh
        ic = emoji(e, 28); im.paste(ic, (cx, cy + 2), ic)
        f = fit(d, n, colw - 46, fsz, 15, bold=False)
        d.text((cx + 38, cy + 3), n, font=f, fill=(222, 204, 180) if not light else (84, 58, 30))
    return y + rows * rowh

def save(im, name, lang):
    p = os.path.join(OUT, f'{name}-{lang}.png')
    im.save(p, 'PNG', optimize=True)
    print(f'  ✓ {os.path.basename(p)}  {im.width}×{im.height}  {os.path.getsize(p)//1024} KB')

# --- A: φωτογραφία πάνω, κύριες σε πλακίδια, υπόλοιπες από κάτω -------------
def draft_a(lang):
    im = Image.new('RGB', (W, H), INK)
    ph = 430
    p = photo('giouvetsi', W, ph)
    g = Image.new('L', (1, ph)); px = g.load()
    for y in range(ph):
        f = max(0.0, (y - ph * .40) / (ph * .60))
        px[0, y] = round(255 * (0.26 + 0.74 * f ** 1.4))
    im.paste(Image.composite(Image.new('RGB', (W, ph), INK), p, g.resize((W, ph))), (0, 0))
    d = ImageDraw.Draw(im)
    header(im, lang)

    f_t = ImageFont.truetype(FB, 62)
    y = 216
    for ln in T[lang]['title'].split('\n'):
        d.text((56, y), ln, font=f_t, fill=CREAM); y += 72
    lang_pill(im, 372, lang)

    cw, ch_, gap = (W - 56 * 2 - 20) // 2, 150, 14
    gy = 462
    for i, (e, n, desc, _s) in enumerate(HERO[lang]):
        cx = 56 + (i % 2) * (cw + 20)
        cy = gy + (i // 2) * (ch_ + gap)
        d.rounded_rectangle([cx, cy, cx + cw, cy + ch_], radius=24, fill=PANEL)
        ic = emoji(e, 46); im.paste(ic, (cx + 24, cy + 20), ic)
        d.text((cx + 24, cy + 78), n, font=fit(d, n, cw - 48, 30), fill=GOLD)
        f_d = ImageFont.truetype(FR, 23)
        yy = cy + 112
        for ln in wrap(d, desc, f_d, cw - 48)[:2]:
            d.text((cx + 24, yy), ln, font=f_d, fill=(222, 204, 180)); yy += 28

    rest_block(im, 968, lang)
    cta_bar(im, 1254, lang)
    save(im, 'A-plakidia', lang)

# --- B: τηλέφωνο στο κέντρο -------------------------------------------------
def draft_b(lang):
    im = Image.new('RGB', (W, H), (26, 16, 6)); gp_ = im.load()
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            dd = (((x - W / 2) / 600) ** 2 + ((y - 640) / 560) ** 2) ** .5
            v = max(0.0, 1 - dd) ** 2
            c = (round(26 + 62 * v), round(16 + 36 * v), round(6 + 10 * v))
            for oy in (0, 1):
                for ox in (0, 1):
                    if x + ox < W and y + oy < H: gp_[x + ox, y + oy] = c
    d = ImageDraw.Draw(im)
    header(im, lang)

    f_t = ImageFont.truetype(FB, 44)
    y = 176
    for ln in T[lang]['lead'].split('\n'):
        d.text(((W - d.textlength(ln, font=f_t)) / 2, y), ln, font=f_t, fill=CREAM); y += 54
    lang_pill(im, 294, lang, x=W / 2)

    # Η συσκευή δείχνει ό,τι βλέπει ο χρήστης σε Cook Mode: βήμα και χρονόμετρο.
    PW, PH, R = 324, 566, 40
    dev = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
    ImageDraw.Draw(dev).rounded_rectangle([0, 0, PW, PH], radius=R, fill=(12, 8, 3, 255))
    scr = photo('moussaka', PW - 18, PH - 18).convert('RGBA')
    ov = Image.new('RGBA', scr.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).rectangle([0, scr.height - 282, scr.width, scr.height], fill=(16, 10, 3, 220))
    scr = Image.alpha_composite(scr, ov)
    sd = ImageDraw.Draw(scr)
    base = scr.height - 262
    sd.text((24, base), 'ΒΗΜΑ 4 / 8' if lang == 'el' else 'STEP 4 / 8',
            font=ImageFont.truetype(FB, 22), fill=GOLD)
    step = ('Στρώνεις τις πατάτες και από πάνω τον κιμά' if lang == 'el'
            else 'Layer the potatoes, then the mince on top')
    f_s = ImageFont.truetype(FR, 25)
    yy = base + 38
    for ln in wrap(sd, step, f_s, scr.width - 48)[:3]:
        sd.text((24, yy), ln, font=f_s, fill=CREAM); yy += 34
    sd.rounded_rectangle([24, scr.height - 94, 182, scr.height - 38], radius=28, fill=BRICK)
    tm = emoji('⏱️', 30); scr.paste(tm, (40, scr.height - 81), tm)
    sd.text((82, scr.height - 80), '12:00', font=ImageFont.truetype(FB, 29), fill=(255, 255, 255))
    m = Image.new('L', scr.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, scr.width, scr.height], radius=R - 8, fill=255)
    dev.paste(scr.convert('RGB'), (9, 9), m)
    sh = Image.new('RGBA', (PW + 120, PH + 120), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([60, 70, 60 + PW, 70 + PH], radius=R, fill=(0, 0, 0, 150))
    im.paste(sh.filter(ImageFilter.GaussianBlur(26)), ((W - sh.width) // 2, 378 - 60),
             sh.filter(ImageFilter.GaussianBlur(26)))
    im.paste(dev, ((W - PW) // 2, 378), dev)

    # Τρεις κύριες αριστερά, τρεις δεξιά — μόνο οι τίτλοι, στη σύντομη εκδοχή.
    MARG, GAPX = 48, 44
    lx, rx = (W - PW) // 2 - GAPX, (W + PW) // 2 + GAPX
    def side(items, x, right):
        avail = (x - MARG - 52) if right else (W - MARG - x - 52)
        yy = 424
        for e, n, _dsc, s in items:
            f_n = fit(d, s, avail, 26)
            ic = emoji(e, 38)
            if right:
                im.paste(ic, (x - 38, yy), ic)
                d.text((x - 52 - d.textlength(s, font=f_n), yy + 6), s, font=f_n, fill=CREAM)
            else:
                im.paste(ic, (x, yy), ic)
                d.text((x + 52, yy + 6), s, font=f_n, fill=CREAM)
            yy += 174
    side([HERO[lang][i] for i in (0, 2, 3)], lx, True)
    side([HERO[lang][i] for i in (1, 5, 4)], rx, False)

    rest_block(im, 962, lang)
    cta_bar(im, 1248, lang, center=True)
    save(im, 'B-tilefono', lang)

# --- C: καθαρή λίστα --------------------------------------------------------
def draft_c(lang):
    im = Image.new('RGB', (W, H), (250, 245, 236))
    d = ImageDraw.Draw(im)
    band = 286
    p = photo('souvlakia', W, band).convert('RGBA')
    ov = Image.new('RGBA', (W, band), (20, 12, 3, 155))
    im.paste(Image.alpha_composite(p, ov).convert('RGB'), (0, 0))
    header(im, lang, y=40)
    d.text((56, 160), T[lang]['allt'], font=ImageFont.truetype(FB, 54), fill=CREAM)
    lang_pill(im, band + 26, lang, light_bg=True)

    y = band + 110
    f_d = ImageFont.truetype(FR, 23)
    for e, n, desc, _s in HERO[lang]:
        ic = emoji(e, 42); im.paste(ic, (56, y + 2), ic)
        d.text((122, y), n, font=fit(d, n, W - 190, 31), fill=(58, 34, 10))
        d.text((122, y + 38), wrap(d, desc, f_d, W - 190)[0], font=f_d, fill=(126, 104, 80))
        y += 84
        d.line([122, y - 16, W - 56, y - 16], fill=(228, 216, 198), width=2)

    rest_block(im, y + 6, lang, light=True)
    d.rounded_rectangle([0, H - 136, W, H], fill=INK)
    cta_bar(im, H - 108, lang)
    save(im, 'C-lista', lang)

# --- D: μια μέρα με την εφαρμογή -------------------------------------------
def draft_d(lang):
    im = Image.new('RGB', (W, H), INK)
    d = ImageDraw.Draw(im)
    header(im, lang)
    d.text((56, 172), T[lang]['dayt'], font=ImageFont.truetype(FB, 52), fill=CREAM)
    lang_pill(im, 240, lang)

    shots = ['kotopoulo', 'horiatiki', 'moussaka', 'baklava']
    icons = ['🔔', '🛒', '🍳', '📤']
    y0, step, D_ = 330, 146, 104
    d.line([108, y0 + 52, 108, y0 + step * 3 + 52], fill=(74, 50, 22), width=4)
    for i, ((lbl, txt), rid, e) in enumerate(zip(T[lang]['daytxt'], shots, icons)):
        y = y0 + i * step
        th = photo(rid, D_, D_)
        m = Image.new('L', (D_ * 4, D_ * 4), 0)
        ImageDraw.Draw(m).ellipse([0, 0, D_ * 4, D_ * 4], fill=255)
        th.putalpha(m.resize((D_, D_), Image.LANCZOS))
        d.ellipse([50, y - 6, 56 + D_ + 6, y + D_ + 6], fill=(74, 50, 22))
        im.paste(th, (56, y), th)
        ic = emoji(e, 36); im.paste(ic, (192, y + 2), ic)
        d.text((242, y + 4), T[lang]['day'][i], font=ImageFont.truetype(FB, 27), fill=GOLD)
        d.text((192, y + 46), lbl, font=ImageFont.truetype(FB, 34), fill=CREAM)
        d.text((192, y + 88), wrap(d, txt, ImageFont.truetype(FR, 24), W - 270)[0],
               font=ImageFont.truetype(FR, 24), fill=(198, 176, 148))

    rest_block(im, 912, lang)
    cta_bar(im, 1254, lang)
    save(im, 'D-mia-mera', lang)

if __name__ == '__main__':
    langs = sys.argv[1:] or ['el', 'en']
    for lang in langs:
        print(f'Προσχέδια διαφήμισης ({lang}) — {N} συνταγές, '
              f'{len(HERO[lang])} κύριες + {len(REST[lang])} ακόμα')
        draft_a(lang); draft_b(lang); draft_c(lang); draft_d(lang)
