# -*- coding: utf-8 -*-
"""Ενώνει το βίντεο διαλόγου (ads/call.py) με την πραγματική οθόνη του κινητού.

Δύο δουλειές:

1. **Θολώνει τα ονόματα επαφών** στο φύλλο κοινοποίησης του Android. Η σειρά
   των προσώπων (φωτογραφία + όνομα) είναι προσωπικά δεδομένα τρίτων και δεν
   έχει καμία θέση σε δημόσιο βίντεο. Η από κάτω σειρά των εφαρμογών
   (Messenger, Viber, Outlook…) μένει καθαρή: αυτή είναι που δείχνει τι κάνει
   η λειτουργία.

   Η θέση της σειράς **δεν είναι σταθερή** — το φύλλο ανεβαίνει με κίνηση.
   Γι' αυτό σε κάθε καρέ εντοπίζεται η κορυφή του σκούρου φύλλου και η ζώνη
   θόλωσης μετριέται από εκεί, αλλιώς στα καρέ της κίνησης τα ονόματα
   ξεφεύγουν από το ορθογώνιο.

2. **Κολλάει τα δύο μέρη** σε ενιαίο 1080×1920, με μαύρο γέμισμα στα πλάγια
   αντί για κόψιμο: η οθόνη του κινητού έχει άλλη αναλογία, και το κόψιμο θα
   έτρωγε την κεφαλίδα της εφαρμογής.

Χρήση: python3 ads/merge_call.py <εγγραφή_οθόνης.mp4> [έξοδος.mp4]
"""
from PIL import Image, ImageFilter
import os, sys, subprocess, numpy as np, imageio_ffmpeg

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT    = os.path.join(ROOT, 'ads', 'reels')
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
PART1  = os.path.join(OUT, 'call-fooddaily-el.mp4')
W, H   = 1080, 1920

# Η ζώνη των επαφών, μετρημένη από την κορυφή του φύλλου κοινοποίησης.
DY0, DY1 = 275, 478
BG = (18, 12, 8)          # ίδιο φόντο με το πρώτο μέρος

# Ποια κομμάτια της εγγραφής κρατιούνται (δευτερόλεπτα). Κόβονται οι νεκροί
# χρόνοι — πληκτρολόγηση και επαναλαμβανόμενο κύλισμα — ώστε το βίντεο να μένει
# κάτω από τα 40΄΄. Οι ΔΥΟ σκηνές κοινοποίησης μένουν ακέραιες: αυτές είναι το
# αποδεικτικό, όχι διακοσμητικό.
SEGMENTS = [(0.0, 2.6),      # αρχική οθόνη, γραμμένη αναζήτηση, το αποτέλεσμα
            (7.4, 9.4),      # άνοιγμα της συνταγής
            (10.6, 16.1),    # υλικά → «Κοινοποίηση υλικών» → φύλλο κοινοποίησης
            (18.2, 22.7)]    # κοινοποίηση της ίδιας της συνταγής

def probe(path):
    p = subprocess.run([FFMPEG,'-i',path], stderr=subprocess.PIPE, text=True)
    import re
    m = re.search(r'(\d{2,5})x(\d{2,5})', p.stderr.split('Video:')[1])
    fps = float(re.search(r'([\d.]+) fps', p.stderr).group(1))
    dur = re.search(r'Duration: (\d+):(\d+):([\d.]+)', p.stderr)
    secs = int(dur.group(1))*3600 + int(dur.group(2))*60 + float(dur.group(3))
    return int(m.group(1)), int(m.group(2)), fps, secs

def panel_top(gray, h):
    """Κορυφή του σκούρου φύλλου κοινοποίησης, ή None αν δεν υπάρχει."""
    rows = gray[int(h*0.42):h, 40:-40].mean(axis=1)
    d = rows < 70
    for y in range(len(d)-40):
        if d[y:y+40].all():
            return int(h*0.42) + y
    return None

def scan_tops(src, w, h):
    """Πρώτο πέρασμα: η κορυφή του σκούρου φύλλου σε κάθε καρέ.

    Σκούρο φύλλο δεν σημαίνει φύλλο κοινοποίησης — το ίδιο ανιχνεύεται και στο
    πληκτρολόγιο, που εμφανίζεται νωρίτερα στην εγγραφή. Το φύλλο κοινοποίησης
    σταθεροποιείται γύρω στο 0.46·h· μόνο εκεί θολώνουμε, και στα λίγα καρέ
    της κίνησης που γειτονεύουν χρονικά με αυτά.
    """
    p = subprocess.Popen([FFMPEG,'-i',src,'-f','rawvideo','-pix_fmt','gray','-'],
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    tops = []
    while True:
        raw = p.stdout.read(w*h)
        if len(raw) < w*h: break
        tops.append(panel_top(np.frombuffer(raw, dtype=np.uint8).reshape(h, w), h))
    p.stdout.close(); p.wait()
    lo, hi = round(h*0.44), round(h*0.50)
    core = [t is not None and lo <= t <= hi for t in tops]
    use  = list(core)
    for i, c in enumerate(core):                # επέκταση στα καρέ της κίνησης
        if c:
            for j in range(max(0,i-8), min(len(core), i+9)):
                if tops[j] is not None: use[j] = True
    return tops, use

def blur_contacts(src, dst):
    w, h, fps, dur = probe(src)
    tops, use = scan_tops(src, w, h)
    dec = subprocess.Popen([FFMPEG,'-i',src,'-f','rawvideo','-pix_fmt','rgb24','-'],
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    enc = subprocess.Popen([FFMPEG,'-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}',
        '-r',str(fps),'-i','-','-i',src,'-map','0:v','-map','1:a?','-c:v','libx264',
        '-preset','medium','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-shortest',dst],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    size, n, hit = w*h*3, 0, 0
    while True:
        raw = dec.stdout.read(size)
        if len(raw) < size: break
        a = np.frombuffer(raw, dtype=np.uint8).reshape(h, w, 3)
        top = tops[n] if n < len(tops) and use[n] else None
        if top is not None:
            y0, y1 = min(h, top+DY0), min(h, top+DY1)
            if y1 > y0:
                im = Image.fromarray(a)
                band = im.crop((0, y0, w, y1))
                # Πρώτα υποδειγματοληψία και μετά θόλωση: τα γράμματα
                # καταστρέφονται οριστικά, δεν «καθαρίζουν» με επεξεργασία.
                band = band.resize((max(1,w//22), max(1,(y1-y0)//22)), Image.BILINEAR) \
                           .resize((w, y1-y0), Image.NEAREST) \
                           .filter(ImageFilter.GaussianBlur(9))
                im.paste(band, (0, y0))
                a = np.asarray(im)
                hit += 1
        enc.stdin.write(a.tobytes()); n += 1
    dec.stdout.close(); enc.stdin.close(); enc.wait()
    print(f'  ✓ θολώθηκαν {hit} από {n} καρέ')
    return dst

def cut(src, dst, segs):
    """Κρατά μόνο τα κομμάτια της λίστας, ενωμένα σε ένα αρχείο."""
    parts = []
    for k, (a, b) in enumerate(segs):
        parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{k}];"
                     f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS[a{k}];")
    tags = ''.join(f'[v{k}][a{k}]' for k in range(len(segs)))
    fc = ''.join(parts) + f'{tags}concat=n={len(segs)}:v=1:a=1[v][a]'
    subprocess.run([FFMPEG,'-y','-i',src,'-filter_complex',fc,'-map','[v]','-map','[a]',
        '-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-c:a','aac',dst],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return dst

def join(blurred, out):
    """Ενιαίο 1080×1920: το πρώτο μέρος όπως είναι, το δεύτερο με γέμισμα."""
    hx = f'{BG[0]:02x}{BG[1]:02x}{BG[2]:02x}'
    # Το πρώτο μέρος δεν έχει ήχο. Η σιωπή πρέπει να έχει ΡΗΤΗ διάρκεια: το
    # anullsrc είναι ατέρμονο και το concat περιμένει για πάντα να τελειώσει,
    # συνεχίζοντας να γράφει αρχείο μέχρι να γεμίσει ο δίσκος.
    d1 = probe(PART1)[3]
    fc = (f"[0:v]scale={W}:{H},setsar=1,fps=30[v0];"
          f"[1:v]scale={W}:{H}:force_original_aspect_ratio=decrease,"
          f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x{hx},setsar=1,fps=30[v1];"
          f"anullsrc=channel_layout=stereo:sample_rate=48000,"
          f"atrim=0:{d1:.3f},asetpts=N/SR/TB[s0];"
          f"[s0][1:a]concat=n=2:v=0:a=1[a];"
          f"[v0][v1]concat=n=2:v=1:a=0[v]")
    subprocess.run([FFMPEG,'-y','-i',PART1,'-i',blurred,'-filter_complex',fc,
        '-map','[v]','-map','[a]','-c:v','libx264','-preset','medium','-crf','21',
        '-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',out],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out

if __name__ == '__main__':
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(OUT, 'call-full-el.mp4')
    tmp = os.path.join(OUT, '_blurred.mp4')
    # Η θόλωση είναι το ακριβό βήμα (καρέ-καρέ): αν υπάρχει ήδη αποτέλεσμα πιο
    # πρόσφατο από την εγγραφή, δεν ξαναγίνεται.
    if not (os.path.exists(tmp) and os.path.getmtime(tmp) > os.path.getmtime(src)):
        blur_contacts(src, tmp)
    else:
        print('  · χρήση υπάρχουσας θόλωσης')
    if SEGMENTS and os.environ.get('FD_NOCUT') != '1':
        short = os.path.join(OUT, '_short.mp4')
        cut(tmp, short, SEGMENTS)
        join(short, out)
        os.remove(short)
    else:
        join(tmp, out)
    print(f'  ✓ {os.path.basename(out)}  {os.path.getsize(out)//1024} KB')
