# -*- coding: utf-8 -*-
"""Κατακόρυφο βίντεο συνταγής για Reels / TikTok / Shorts, από τα δεδομένα της
εφαρμογής. ΔΕΝ είναι διαφήμιση: είναι συνταγή. Η εφαρμογή αναφέρεται μόνο στο
τέλος, γιατί περιεχόμενο που μοιάζει με διαφήμιση δεν το βλέπει κανείς.
Χρήση: python3 ads/reel.py <id_συνταγής> [el|en]
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, re, sys, subprocess
import json, imageio_ffmpeg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, 'ads', 'reels')
os.makedirs(OUT, exist_ok=True)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
W, H, FPS = 1080, 1920, 25

def load(rid):
    """Διαβάζει MEALS/MEAL_IMAGES από το index.html μέσω node."""
    js = r'''
const fs=require('fs'),vm=require('vm');
const b=fs.readFileSync(process.argv[1],'utf8').match(/<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/)[1];
const g=(o,c)=>{const i=b.indexOf(o),j=b.indexOf(c,i);return b.slice(i,j+c.length)};
const ctx={};vm.createContext(ctx);
new vm.Script(g('const MEALS={','\n};')+'\n'+g('const MEAL_IMAGES={','\n};')).runInContext(ctx);
const {MEALS,MEAL_IMAGES}=vm.runInContext('({MEALS,MEAL_IMAGES})',ctx);
const id=process.argv[2];
if(!MEALS[id]){console.error('ΑΓΝΩΣΤΟ ID');process.exit(1);}
console.log(JSON.stringify({m:MEALS[id],img:MEAL_IMAGES[id]}));
'''
    p = subprocess.run(['node','-e',js,os.path.join(ROOT,'index.html'),rid],
                       capture_output=True, text=True)
    if p.returncode: sys.exit('Δεν βρέθηκε η συνταγή: '+rid)
    return json.loads(p.stdout)

def cover(im, w, h):
    r = max(w/im.width, h/im.height)
    im = im.resize((round(im.width*r), round(im.height*r)), Image.LANCZOS)
    return im.crop(((im.width-w)//2,(im.height-h)//2,(im.width-w)//2+w,(im.height-h)//2+h))

def wrap(d, txt, f, maxw):
    out, cur = [], ''
    for w_ in txt.split():
        t = (cur+' '+w_).strip()
        if d.textlength(t, font=f) <= maxw or not cur: cur = t
        else: out.append(cur); cur = w_
    if cur: out.append(cur)
    return out

# --- Ασφαλής περιοχή TikTok/Reels -------------------------------------------
# Το κάτω μέρος το σκεπάζει η λεζάντα και το όνομα χρήστη, τα δεξιά τα κουμπιά.
# Ό,τι πρέπει να διαβαστεί μένει μέσα σε αυτά τα όρια.
SAFE_B = 380     # κάτω
SAFE_R = 170     # δεξιά
TOP    = 268     # κάτω από την υπογραφή και το badge γλωσσών
AREA   = H - SAFE_B - TOP   # ελεύθερο ύψος για κάθετο κεντράρισμα

def hook_words(el=True):
    """Οι λέξεις του hook, χωριστά από τη build(), ώστε να τις χρησιμοποιεί
    και το captions.py: η πρώτη γραμμή της λεζάντας πρέπει να επαναλαμβάνει
    αυτό που λέει το βίντεο, αλλιώς το μήνυμα διχάζεται."""
    return {'cost':'η μερίδα' if el else 'per serving',
            'time':'και έτοιμο' if el else "and it's ready",
            'ing' :'υλικά. Τίποτα άλλο.' if el else "ingredients. That's all.",
            'cal' :'θερμίδες η μερίδα' if el else 'calories per serving',
            'tbl' :'για {n} άτομα' if el else 'for {n} people',
            'step':'βήματα. Τόσο απλά.' if el else 'steps. That simple.',
            'occ' :'Κυριακή' if el else 'Sunday',
            'occ2':'Το πιάτο της ημέρας' if el else 'The dish of the day'}


def pick_hook(m, ings, steps, rid, el=True):
    """Πέντε τύποι hook, με επιλογή ΜΟΝΟ ανάμεσα σε όσους ισχύουν για τη
    συγκεκριμένη συνταγή.

    Παλιότερα η επιλογή γινόταν με `var % 3` και κάθε εξαίρεση κατέληγε στο
    κόστος: 21 από τα 30 βίντεο έβγαζαν το ίδιο hook. Τώρα φτιάχνεται πρώτα η
    λίστα των έγκυρων και ο δείκτης πέφτει πάνω της, ώστε η κατανομή να μένει
    ισορροπημένη και τα βίντεο να μη μοιάζουν μεταξύ τους."""
    W_ = hook_words(el)
    var = sum(ord(c) for c in rid)
    num = lambda v: re.sub(r'[~\s]', '', str(v or '')).strip()
    def eur(v):
        try: return float(re.sub(r'[^\d.]', '', str(v or '')))
        except ValueError: return None
    sweet = 'desserts' in (m.get('cats') or [])
    opts = []
    # Κάθε αριθμός μπαίνει ΜΟΝΟ όταν παίζει υπέρ του πιάτου. Ένα νούμερο που
    # εκθέτει το πιάτο κάνει ζημιά: «8.75€ η μερίδα», ή «380 θερμίδες» πάνω σε
    # γλυκό, διώχνουν τον θεατή αντί να τον κρατήσουν.
    cps = eur(m.get('cps'))
    if cps is not None and cps <= 2.50:
        opts.append((num(m['cps']), W_['cost']))            # φθηνή μερίδα
    # Ο χρόνος πουλά μόνο όταν είναι μικρός: «100′ και έτοιμο» διώχνει.
    if m.get('time') and m['time'] <= 40:
        opts.append((f"{m['time']}′", W_['time']))
    # Λίγα υλικά = υπόσχεση απλότητας, και είναι νούμερο: διαβάζεται ακαριαία.
    # Ο τίτλος βήματος δοκιμάστηκε και δεν λειτουργεί ως hook — «Γέμισμα
    # λαχανικών» δεν σταματά κανέναν.
    if len(ings) <= 7:
        opts.append((str(len(ings)), W_['ing']))
    # Οι θερμίδες πουλάνε φαγητό, όχι γλυκό.
    if m.get('cal') and m['cal'] <= 400 and not sweet:
        opts.append((str(m['cal']), W_['cal']))
    # Το συνολικό κόστος για παρέα — αλλά μόνο αν βγαίνει φθηνά κατ' άτομο.
    tot = eur(m.get('cost'))
    if tot is not None and m.get('srv') and m['srv'] >= 4 and tot/m['srv'] <= 2.50:
        opts.append((num(m['cost']), W_['tbl'].format(n=m['srv'])))
    if opts:
        return opts[var % len(opts)]
    # Ακριβά, αργά ή πλούσια πιάτα: κανένας αριθμός δεν τα ευνοεί. Εκεί το
    # επιχείρημα δεν είναι το νούμερο αλλά η περίσταση.
    if len(steps) <= 7:
        return str(len(steps)), W_['step']
    return W_['occ'], W_['occ2']


def build(rid, lang='el'):
    data = load(rid); m = data['m']; imgp = data['img']
    el = lang == 'el'
    name  = m['n'] if el else (m.get('en') or m.get('n_en') or m['n'])
    ings  = m['ing'] if el else (m.get('ing_en') or m['ing'])
    steps = m['steps'] if el else (m.get('steps_en') or m['steps'])
    L = {'ing':'ΥΛΙΚΑ' if el else 'INGREDIENTS',
         'how':'ΕΚΤΕΛΕΣΗ' if el else 'METHOD',
         'serv':'μερίδες' if el else 'servings',
         'q':'Τι μαγειρεύουμε σήμερα;' if el else 'What are we cooking today?',
         'b1':'Πρόταση φαγητού κάθε μέρα' if el else 'A meal suggestion every day',
         'b2':'Υπενθύμιση τι να ετοιμάσεις' if el else 'Reminders of what to prep',
         'b3':'376 ελληνικές συνταγές' if el else '376 Greek recipes',
         'more':'Όλη η συνταγή στην εφαρμογή' if el else 'Full recipe in the app',
         'get':'Σύνδεσμος στο προφίλ' if el else 'Link in bio',
         'url':'fooddaily.github.io',
         'free':'Δωρεάν στο Google Play' if el else 'Free on Google Play',
         'langs':'376 συνταγές · recipes · Rezepte',
         'langs2':'Ελληνικά · English · Deutsch'}

    var = sum(ord(c) for c in rid)
    zoom_in = (var // 5) % 2 == 0

    hook_big, hook_small = pick_hook(m, ings, steps, rid, el)

    # Δύο ακόμη άξονες διαφοροποίησης, ώστε 30 βίντεο στη σειρά να μη δείχνουν
    # πανομοιότυπα: ο τόνος του μεγάλου νούμερου και η στοίχιση του hook.
    TONES = [(255,214,120), (255,168,92), (255,245,225)]
    tone  = TONES[(var // 7) % 3]
    hook_centered = (var // 11) % 2 == 0

    # Και η φράση του CTA εναλλάσσεται, για τον ίδιο λόγο.
    QS = ([L['q'], 'Η απάντηση κάθε μεσημέρι', 'Τέλος το «τι μαγειρεύουμε;»'] if el
          else [L['q'], 'The answer, every day', 'No more "what shall we cook?"'])
    L['q'] = QS[(var // 13) % 3]

    photo = Image.open(os.path.join(ROOT, imgp)).convert('RGB')
    bg = cover(photo, W, H)
    blur = bg.filter(ImageFilter.GaussianBlur(20))

    def scrim(src, top, base=.30, peak=.95):
        g = Image.new('L',(1,H)); px=g.load()
        for y in range(H):
            f = 0 if y<top else (y-top)/max(1,H-top)
            px[0,y] = round(255*(base+(peak-base)*min(1.,f)**1.5))
        return Image.composite(Image.new('RGB',(W,H),(20,11,2)), src, g.resize((W,H)))

    f_meta = ImageFont.truetype(FB, 40)
    f_hdr  = ImageFont.truetype(FB, 52)
    f_item = ImageFont.truetype(FR, 42)
    f_num  = ImageFont.truetype(FB, 60)
    f_cta  = ImageFont.truetype(FB, 62)
    f_sub  = ImageFont.truetype(FR, 38)
    f_lang  = ImageFont.truetype(FB, 30)
    f_lang2 = ImageFont.truetype(FR, 28)

    D = 118
    logo = Image.open(os.path.join(ROOT,'icon-512.png')).convert('RGB').crop((118,88,394,364)).resize((D,D), Image.LANCZOS)
    mk = Image.new('L',(D*4,D*4),0); ImageDraw.Draw(mk).ellipse([0,0,D*4,D*4],fill=255)
    logo.putalpha(mk.resize((D,D), Image.LANCZOS))

    # Επίσημο badge της Google. Το κενό περιθώριο του αρχείου κόβεται, ώστε να
    # ελέγχουμε εμείς την απόσταση από τα υπόλοιπα στοιχεία.
    gp = Image.open(os.path.join(ROOT, 'ads', 'google-play-badge.png')).convert('RGBA')
    gp = gp.crop(gp.split()[3].getbbox())
    GPW = 268
    gp = gp.resize((GPW, round(gp.height * GPW / gp.width)), Image.LANCZOS)

    # Μικρό λογότυπο για τη μόνιμη υπογραφή
    DS = 62
    logo_s = logo.resize((DS,DS), Image.LANCZOS)
    f_wm  = ImageFont.truetype(FB, 34)
    f_wm2 = ImageFont.truetype(FR, 26)

    def stamp(fr, d):
        """Μόνιμη υπογραφή σε ΚΑΘΕ καρέ, πάνω αριστερά.

        Ο μέσος θεατής φεύγει πριν φτάσει σε οποιαδήποτε σκηνή CTA. Αν η
        επωνυμία υπάρχει μόνο στο τέλος, δεν τη βλέπει κανείς — γι' αυτό
        μπαίνει από το πρώτο καρέ και δεν φεύγει ποτέ."""
        x, y = 40, 40
        d.rounded_rectangle([x-14, y-12, x+DS+272, y+DS+12], radius=42, fill=(24,14,4))
        fr.paste(logo_s, (x, y), logo_s)
        d.text((x+DS+18, y+4),  'FoodDaily', font=f_wm,  fill=(255,253,248))
        d.text((x+DS+18, y+40), L['url'],    font=f_wm2, fill=(233,178,74))

        # Η ένδειξη γλωσσών ανεβαίνει ΕΔΩ, κάτω από την υπογραφή και σε κάθε
        # καρέ. Στο κάτω μέρος χανόταν: το βίντεο είναι στα ελληνικά, και ο
        # ξένος θεατής πρέπει να καταλάβει μέσα στο πρώτο δευτερόλεπτο ότι η
        # εφαρμογή μιλά και τη δική του γλώσσα, αλλιώς κάνει swipe.
        by = y + DS + 26
        w1 = d.textlength(L['langs'],  font=f_lang)
        w2 = d.textlength(L['langs2'], font=f_lang2)
        bw = max(w1, w2) + 40
        d.rounded_rectangle([x-14, by, x-14+bw, by+96], radius=26, fill=(24,14,4))
        d.text((x+6, by+12), L['langs'],  font=f_lang,  fill=(233,178,74))
        d.text((x+6, by+54), L['langs2'], font=f_lang2, fill=(238,222,196))

    def shorten(st):
        head, body = (st.split(':', 1) + [''])[:2] if ':' in st[:60] else ('', st)
        body = body.strip()
        cut = body.find('. ')
        if cut > 30: body = body[:cut+1]
        if len(body) > 90: body = body[:87].rsplit(' ', 1)[0] + '…'
        return head.strip(), body

    # --- Δομή -----------------------------------------------------------------
    # Το φαγητό είναι καθαρό και κινείται από το καρέ 0: αυτό σταματά το scroll,
    # όχι το κείμενο. Συνολική διάρκεια ~11 δευτ., ώστε το βίντεο να κάνει loop
    # δύο φορές μέσα στον ίδιο χρόνο θέασης — το loop μετράει στο watch time.
    scenes = [
        ('hit',   2.8, None),
        ('ing',   2.4, None),
        ('steps', 4.2, [st.split(':', 1)[0].strip() for st in steps[:8]]),
        ('cta',   1.8, None),
    ]

    out = os.path.join(OUT, f'reel-{rid}-{lang}.mp4')
    proc = subprocess.Popen([FFMPEG,'-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),
        '-i','-','-c:v','libx264','-preset','medium','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',out],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    n_all = sum(round(s*FPS) for _,s,_ in scenes); FADE = round(FPS*.4); total = 0
    pad = 74
    colw = W - pad - SAFE_R          # πλάτος κειμένου εκτός των κουμπιών

    for kind, secs, extra in scenes:
        n = round(secs*FPS)
        for i in range(n):
            p = i/max(1,n-1)
            if kind == 'hit':
                # ΚΑΘΑΡΟ πιάτο, ήδη σε κίνηση από το πρώτο καρέ. Καμία θόλωση,
                # καμία ακινησία: το ακίνητο καρέ διαβάζεται ως «δεν συμβαίνει
                # τίποτα» και φεύγει ο θεατής μέσα στο πρώτο δευτερόλεπτο.
                z = (1.0+.08*p) if zoom_in else (1.08-.08*p)
                cw, ch = round(W/z), round(H/z)
                fr = bg.crop(((W-cw)//2,(H-ch)//2,(W-cw)//2+cw,(H-ch)//2+ch)).resize((W,H), Image.LANCZOS)
                fr = scrim(fr, int(H*.46), .10, .92)
            else:
                fr = scrim(blur, 0, .62, .80)
            d = ImageDraw.Draw(fr)

            if kind == 'hit':
                # Το σήμα του Google Play κάτω από τις γλώσσες: αναγνωρίζεται
                # χωρίς διάβασμα και λέει αμέσως πού βρίσκεται η εφαρμογή.
                fr.paste(gp, (26, 240), gp)
                # Ένα μεγάλο νούμερο και μία λέξη. Το μάτι το πιάνει χωρίς
                # ανάγνωση — γι' αυτό δουλεύει μέσα στο πρώτο δευτερόλεπτο.
                f_h1 = ImageFont.truetype(FB, 148 if len(hook_big) <= 6 else 96)
                f_h2 = ImageFont.truetype(FR, 52)
                f_nm = ImageFont.truetype(FB, 64)
                nlines = wrap(d, name, f_nm, colw)[:2]
                blk = f_h1.size + 16 + f_h2.size + 46 + len(nlines)*76 + 54
                y = H - SAFE_B - blk
                # Άλλοτε κεντραρισμένο, άλλοτε στοιχισμένο αριστερά. Στο κέντρο
                # λαμβάνεται υπόψη μόνο η ωφέλιμη στήλη, όχι όλο το πλάτος:
                # δεξιά κάθονται τα κουμπιά του TikTok.
                def put(t, f, yy, col):
                    x = pad + (colw - d.textlength(t, font=f))/2 if hook_centered else pad
                    d.text((x, yy), t, font=f, fill=col)
                put(hook_big, f_h1, y, tone);            y += f_h1.size + 16
                put(hook_small, f_h2, y, (255,250,240));  y += f_h2.size + 46
                for ln in nlines:
                    put(ln, f_nm, y, (255,253,248)); y += 76
                y += 12
                # Χωρίς emoji: η DejaVuSans δεν τα περιέχει και βγαίνουν κενά
                # κουτάκια — φαίνεται σαν ελάττωμα, όχι σαν εικονίδιο.
                meta = f"{m['time']}′  ·  {m['cal']} kcal  ·  {m.get('srv','')} {L['serv']}"
                put(meta, f_meta, y, (240,206,150))
            elif kind == 'ing':
                # Το μπλοκ κεντράρεται κάθετα στον ελεύθερο χώρο: αν ξεκινά
                # ψηλά, τα δύο τρίτα της οθόνης μένουν άδεια και το βίντεο
                # δείχνει φτωχό στο κινητό.
                shown = ings[:9]
                lh_i = 76 if len(shown) <= 7 else 66
                fs_i = 52 if len(shown) <= 7 else 46
                f_it = ImageFont.truetype(FR, fs_i)
                blk  = 76 + len(shown)*lh_i
                y = TOP + max(0, (AREA - blk)//2)
                d.text((pad, y), L['ing'], font=f_hdr, fill=(233,178,74)); y += 76
                for k, it in enumerate(shown):
                    vis = min(1.0, max(0.0, p*len(shown)*1.6 - k))
                    if vis <= 0: continue
                    c = tuple(round(20+(252-20)*vis) for _ in range(3))
                    for ln in wrap(d, '· '+it, f_it, colw)[:1]:
                        d.text((pad, y), ln, font=f_it, fill=c)
                    y += lh_i
            elif kind == 'steps':
                titles = extra
                lh = 104 if len(titles) <= 5 else (92 if len(titles) <= 6 else 80)
                fs = 56 if len(titles) <= 5 else (50 if len(titles) <= 6 else 44)
                f_t = ImageFont.truetype(FR, fs)
                f_n = ImageFont.truetype(FB, fs + 6)
                blk = 96 + len(titles)*lh
                y = TOP + max(0, (AREA - blk)//2)
                d.text((pad, y), L['how'], font=f_hdr, fill=(233,178,74)); y += 96
                for k, ttl in enumerate(titles):
                    vis = min(1.0, max(0.0, p * len(titles) * 2.4 - k))
                    if vis <= 0: continue
                    d.text((pad, y), str(k+1), font=f_n,
                           fill=(round(60+(200-60)*vis), round(24+(80-24)*vis), round(8+(26-8)*vis)))
                    c = round(20+(250-20)*vis)
                    for ln in wrap(d, ttl, f_t, colw-72)[:1]:
                        d.text((pad+72, y+3), ln, font=f_t, fill=(c, c, c))
                    y += lh
                # Μία γραμμή μόνο: η υπογραφή είναι ήδη μόνιμα στην οθόνη.
                f_more = ImageFont.truetype(FB, 46)
                d.text((pad, H - SAFE_B + 24), '→ ' + L['more'], font=f_more, fill=(255,214,120))
            else:  # cta
                ctr = lambda t,f,yy,c: d.text(((W-d.textlength(t,font=f))/2, yy), t, font=f, fill=c)
                f_q   = ImageFont.truetype(FB, 54)
                f_bul = ImageFont.truetype(FR, 40)
                f_url = ImageFont.truetype(FB, 40)
                bul   = [L['b1'], L['b2'], L['b3']]
                bul   = bul[var % 3:] + bul[:var % 3]
                bh, bw = 118, round(d.textlength(L['get'], font=f_sub)) + 170
                block = (f_cta.size + 30 + f_q.size + 36 + len(bul)*56 + 40
                         + bh + 26 + f_sub.size + 16 + f_url.size)
                y = (H - SAFE_B - block) // 2 + 120
                ctr('FoodDaily', f_cta, y, (255,253,248)); y += f_cta.size + 30
                ctr(L['q'], f_q, y, (255,250,240)); y += f_q.size + 36
                wmax = max(d.textlength(t_, font=f_bul) for t_ in bul)
                bx0 = round((W - wmax) / 2)
                for t_ in bul:
                    d.ellipse([bx0-36, y+16, bx0-20, y+32], fill=(233,178,74))
                    d.text((bx0, y), t_, font=f_bul, fill=(243,225,192))
                    y += 56
                y += 40
                bx = (W-bw)//2
                d.rounded_rectangle([bx,y,bx+bw,y+bh], radius=bh//2, fill=(200,80,26))
                ax, ay = bx+62, y+bh//2
                d.polygon([(ax, ay-26), (ax-20, ay-2), (ax-8, ay-2), (ax-8, ay+26),
                           (ax+8, ay+26), (ax+8, ay-2), (ax+20, ay-2)], fill=(255,255,255))
                d.text((bx+108, y+(bh-38)//2-4), L['get'], font=f_sub, fill=(255,255,255))
                y += bh + 26
                ctr(L['free'], f_sub, y, (232,204,162)); y += f_sub.size + 16
                ctr(L['url'], f_url, y, (233,178,74))

            stamp(fr, d)

            # Κανένα fade — ούτε στην αρχή ούτε στο τέλος. Μαύρη έναρξη χαλάει
            # το κρίσιμο πρώτο δευτερόλεπτο, και μαύρο τέλος σπάει το loop:
            # το βίντεο πρέπει να ξαναρχίζει καθαρά, γιατί τα replays μετράνε
            # στον χρόνο θέασης.
            proc.stdin.write(fr.tobytes()); total += 1

    proc.stdin.close(); proc.wait()
    print(f'  ✓ {os.path.basename(out)}  {total/FPS:.1f}s  {os.path.getsize(out)//1024} KB  hook={hook_big!r}')
    return out

if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv)>1 else 'moussaka',
          sys.argv[2] if len(sys.argv)>2 else 'el')
