# -*- coding: utf-8 -*-
"""Βίντεο διαλόγου: δύο φίλες στο τηλέφωνο.

Δεν είναι διαφήμιση — είναι σκηνή. Η εφαρμογή εμφανίζεται μόνο ως η απάντηση
στο «πώς το έκανες;», γιατί η σύσταση από φίλη περνάει, η διαφήμιση όχι.

Το βίντεο **τελειώνει σκόπιμα** στο «περίμενε να σου τη στείλω»: από εκεί και
πέρα κολλάει η οθόνη του κινητού (κοινοποίηση συνταγής + αποστολή υλικών) που
τραβάει ο χρήστης. Έτσι το αποδεικτικό είναι πραγματικό, όχι σχεδιασμένο.

Χρήση: python3 ads/call.py [el|en]
"""
from PIL import Image, ImageDraw, ImageFont
import os, sys, subprocess, imageio_ffmpeg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, 'ads', 'reels')
os.makedirs(OUT, exist_ok=True)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
W, H, FPS = 1080, 1920, 25

SAFE_B = 380     # το κάτω μέρος το σκεπάζει η λεζάντα
SAFE_R = 170     # τα δεξιά τα σκεπάζουν τα κουμπιά
TOP    = 470     # κάτω από υπογραφή, γλώσσες, σήμα Play και μπάρα κλήσης

# Τα δύο πρόσωπα. Η Μαρία μαγειρεύει, η Ελένη ρωτάει.
A, B = 'Ελένη', 'Μαρία'

# Ο διάλογος. Κάθε γραμμή: (ποιος, κείμενο, παύση πριν σε δευτερόλεπτα).
# Οι παύσεις είναι το μισό αστείο: το «Όχι.» χρειάζεται αέρα πριν και μετά.
def script(el=True):
    if el:
        return [
            (A, 'Τι έφτιαξες σήμερα;', 0.9),
            (B, 'Κόκορα κρασάτο.', 1.5),
            (B, 'Και μιλφέιγ.', 0.9),
            (A, 'Πλάκα κάνεις.', 1.4),
            (A, 'Πώς πρόλαβες;', 1.1),
            (A, 'Είχες τα υλικά;', 1.2),
            (B, 'Όχι.', 1.6),
            (B, 'Τα είδα στο FoodDaily και τα έστειλα στον άντρα μου.', 1.5),
            (B, 'Τα έφερε. Τόσο απλά.', 1.6),
            (A, 'Στείλε μου τη συνταγή.', 1.6),
            (B, 'Περίμενε…', 1.4),
        ]
    return [
        (A, 'What did you cook today?', 0.9),
        (B, 'Coq au vin.', 1.5),
        (B, 'And a mille-feuille.', 0.9),
        (A, "You're kidding.", 1.4),
        (A, 'How did you find the time?', 1.1),
        (A, 'Did you have the ingredients?', 1.2),
        (B, 'No.', 1.6),
        (B, 'I saw them in FoodDaily and sent the list to my husband.', 1.5),
        (B, 'He brought them. That simple.', 1.6),
        (A, 'Send me the recipe.', 1.6),
        (B, 'Hold on…', 1.4),
    ]

def wrap(d, txt, f, maxw):
    out = []
    for para in txt.split('\n'):
        cur = ''
        for w_ in para.split():
            t = (cur + ' ' + w_).strip()
            if d.textlength(t, font=f) <= maxw or not cur: cur = t
            else: out.append(cur); cur = w_
        out.append(cur)
    return out

def build(lang='el'):
    el = lang == 'el'
    L = {'url':'fooddaily.github.io',
         'langs':'376 συνταγές · recipes · Rezepte',
         'langs2':'Ελληνικά · English · Deutsch',
         'call':'Σε κλήση' if el else 'On a call'}

    f_msg  = ImageFont.truetype(FR, 48)
    f_name = ImageFont.truetype(FB, 30)
    f_call = ImageFont.truetype(FB, 34)
    f_tmr  = ImageFont.truetype(FR, 32)
    f_lang  = ImageFont.truetype(FB, 30)
    f_lang2 = ImageFont.truetype(FR, 28)
    f_wm  = ImageFont.truetype(FB, 34)
    f_wm2 = ImageFont.truetype(FR, 26)

    D = 118
    logo = Image.open(os.path.join(ROOT,'icon-512.png')).convert('RGB') \
                .crop((118,88,394,364)).resize((D,D), Image.LANCZOS)
    mk = Image.new('L',(D*4,D*4),0); ImageDraw.Draw(mk).ellipse([0,0,D*4,D*4],fill=255)
    logo.putalpha(mk.resize((D,D), Image.LANCZOS))
    DS = 62
    logo_s = logo.resize((DS,DS), Image.LANCZOS)

    gp = Image.open(os.path.join(ROOT,'ads','google-play-badge.png')).convert('RGBA')
    gp = gp.crop(gp.split()[3].getbbox())
    GPW = 268
    gp = gp.resize((GPW, round(gp.height*GPW/gp.width)), Image.LANCZOS)

    # --- Προετοιμασία των μηνυμάτων -----------------------------------------
    probe = ImageDraw.Draw(Image.new('RGB',(10,10)))
    PAD_X, PAD_Y, LH = 34, 26, 62
    MAXW  = W - 74 - SAFE_R - 120          # πλάτος φούσκας εκτός των κουμπιών
    msgs, t = [], 0.6
    for who, txt, gap in script(el):
        t += gap
        lines = wrap(probe, txt, f_msg, MAXW - 2*PAD_X)
        bw = max(probe.textlength(l, font=f_msg) for l in lines) + 2*PAD_X
        bh = len(lines)*LH + 2*PAD_Y
        msgs.append({'who':who, 'lines':lines, 'w':round(bw), 'h':round(bh), 't':t})
    DUR = t + 1.6                          # λίγος αέρας στο τέλος για το loop

    # Κάθετη θέση κάθε φούσκας μέσα σε μια νοητή στήλη που κυλάει
    GAP_Y, y = 22, 0
    for m in msgs:
        m['y'] = y; y += m['h'] + GAP_Y
    COL_H = y

    PAD_B = 48                 # η τελευταία φούσκα δεν ακουμπά το κάτω όριο
    AREA_T, AREA_B = TOP, H - SAFE_B
    AREA_H = AREA_B - AREA_T

    out = os.path.join(OUT, f'call-fooddaily-{lang}.mp4')
    proc = subprocess.Popen([FFMPEG,'-y','-f','rawvideo','-pix_fmt','rgb24',
        '-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-preset','medium',
        '-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',out],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    BG   = (18, 12, 8)
    BUB_A = (44, 36, 30)        # Ελένη — αριστερά, ουδέτερη
    BUB_B = (176, 70, 22)       # Μαρία — δεξιά, στο χρώμα της εφαρμογής
    off = None                  # τρέχουσα κύλιση, με ομαλοποίηση
    n = round(DUR*FPS)

    for i in range(n):
        now = i/FPS
        fr = Image.new('RGB', (W,H), BG)
        d  = ImageDraw.Draw(fr)

        vis = [m for m in msgs if now >= m['t']]
        # Η τελευταία φούσκα κάθεται ΠΑΝΤΑ στο κάτω μέρος της περιοχής, όπως σε
        # πραγματική συνομιλία. Αν στοιβάζονταν από πάνω, τα δύο τρίτα της
        # οθόνης θα έμεναν άδεια στα πρώτα δευτερόλεπτα — εκεί ακριβώς που
        # κρίνεται αν θα μείνει ο θεατής.
        if vis:
            bot = vis[-1]['y'] + vis[-1]['h']
            target = float(bot + PAD_B - AREA_H)
        else:
            target = float(PAD_B - AREA_H)
        off = target if off is None else off + (target-off)*0.18

        # Οι φούσκες ζωγραφίζονται σε ξεχωριστό στρώμα και κόβονται στα όρια
        # της περιοχής: αλλιώς, καθώς κυλούν, περνούν πάνω από τη μπάρα κλήσης
        # και την υπογραφή.
        ch  = Image.new('RGB', (W, AREA_H), BG)
        dch = ImageDraw.Draw(ch)
        for idx, m in enumerate(vis):
            age = now - m['t']
            app = min(1.0, age/0.22)        # εμφάνιση: ανεβαίνει και ξεθωριάζει μέσα
            rise = round((1-app)**2 * 26)
            by = m['y'] - round(off) + rise
            if by > AREA_H or by + m['h'] < -40: continue
            right = m['who'] == B
            bx = (W - SAFE_R - 74 - m['w']) if right else 74
            col = BUB_B if right else BUB_A
            col = tuple(round(BG[k] + (col[k]-BG[k])*app) for k in range(3))
            dch.rounded_rectangle([bx, by, bx+m['w'], by+m['h']], radius=34, fill=col)
            # Όνομα πάνω από την πρώτη φούσκα κάθε ομιλητή
            if idx == 0 or vis[idx-1]['who'] != m['who']:
                nm = m['who']
                nx = bx + m['w'] - probe.textlength(nm, font=f_name) if right else bx
                c = round(150*app)
                dch.text((nx, by-40), nm, font=f_name, fill=(c,c,c))
            tc = round(255*app)
            for k, ln in enumerate(m['lines']):
                dch.text((bx+PAD_X, by+PAD_Y+k*LH), ln, font=f_msg,
                         fill=(tc, round(tc*.99), round(tc*.96)))
        fr.paste(ch, (0, AREA_T))

        # --- Μπάρα κλήσης ----------------------------------------------------
        cy = 360
        d.rounded_rectangle([74, cy, W-SAFE_R-74, cy+82], radius=41, fill=(34,26,20))
        d.ellipse([96, cy+29, 120, cy+53], fill=(90, 210, 120))
        d.text((136, cy+22), f"{L['call']} · {A} — {B}", font=f_call, fill=(238,222,196))
        mm, ss = divmod(int(now)+184, 60)
        tt = f'{mm:02d}:{ss:02d}'
        d.text((W-SAFE_R-100-probe.textlength(tt, font=f_tmr), cy+24), tt,
               font=f_tmr, fill=(150,140,130))

        # --- Μόνιμη υπογραφή, ίδια με τα υπόλοιπα βίντεο ---------------------
        x, y0 = 40, 40
        d.rounded_rectangle([x-14, y0-12, x+DS+272, y0+DS+12], radius=42, fill=(24,14,4))
        fr.paste(logo_s, (x, y0), logo_s)
        d.text((x+DS+18, y0+4),  'FoodDaily', font=f_wm,  fill=(255,253,248))
        d.text((x+DS+18, y0+40), L['url'],    font=f_wm2, fill=(233,178,74))
        by = y0 + DS + 26
        bw = max(probe.textlength(L['langs'], font=f_lang),
                 probe.textlength(L['langs2'], font=f_lang2)) + 40
        d.rounded_rectangle([x-14, by, x-14+bw, by+96], radius=26, fill=(24,14,4))
        d.text((x+6, by+12), L['langs'],  font=f_lang,  fill=(233,178,74))
        d.text((x+6, by+54), L['langs2'], font=f_lang2, fill=(238,222,196))
        fr.paste(gp, (x-14, by+96+16), gp)

        proc.stdin.write(fr.tobytes())

    proc.stdin.close(); proc.wait()
    print(f'  ✓ {os.path.basename(out)}  {n/FPS:.1f}s  {os.path.getsize(out)//1024} KB')
    return out

if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else 'el')
