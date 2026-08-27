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

def build(rid, lang='el'):
    data = load(rid); m = data['m']; imgp = data['img']
    el = lang == 'el'
    name  = m['n'] if el else (m.get('en') or m.get('n_en') or m['n'])
    ings  = m['ing'] if el else (m.get('ing_en') or m['ing'])
    steps = m['steps'] if el else (m.get('steps_en') or m['steps'])
    L = {'ing':'ΥΛΙΚΑ' if el else 'INGREDIENTS',
         'how':'ΕΚΤΕΛΕΣΗ' if el else 'METHOD',
         'serv':'μερίδες' if el else 'servings',
         'cta':'376 ελληνικές συνταγές' if el else '376 Greek recipes',
         'app':'στην εφαρμογή FoodDaily' if el else 'in the FoodDaily app',
         'q':'Τι μαγειρεύουμε σήμερα;' if el else 'What are we cooking today?',
         'b1':'Πρόταση φαγητού κάθε μέρα' if el else 'A meal suggestion every day',
         'b2':'Υπενθύμιση τι να ετοιμάσεις' if el else 'Reminders of what to prep',
         'b3':'376 ελληνικές συνταγές' if el else '376 Greek recipes',
         'get':'Σύνδεσμος στο προφίλ' if el else 'Link in bio',
         'url':'georgebokos.github.io/app',
         'free':'Δωρεάν στο Google Play' if el else 'Free on Google Play'}

    # Μικρές παραλλαγές, ώστε 30 βίντεο στη σειρά να μη μοιάζουν πανομοιότυπα.
    # Παράγονται από το id, άρα κάθε συνταγή βγάζει πάντα το ίδιο αποτέλεσμα.
    var = sum(ord(c) for c in rid)
    QS = ([L['q'], 'Τι θα φάμε σήμερα;', 'Τέλος το «τι μαγειρεύουμε;»'] if el
          else [L['q'], 'What are we eating today?', 'No more "what shall we cook?"'])
    L['q'] = QS[var % 3]
    zoom_in = (var // 3) % 2 == 0

    photo = Image.open(os.path.join(ROOT, imgp)).convert('RGB')
    bg = cover(photo, W, H)
    blur = bg.filter(ImageFilter.GaussianBlur(20))

    def scrim(src, top, base=.30, peak=.95):
        g = Image.new('L',(1,H)); px=g.load()
        for y in range(H):
            f = 0 if y<top else (y-top)/max(1,H-top)
            px[0,y] = round(255*(base+(peak-base)*min(1.,f)**1.5))
        return Image.composite(Image.new('RGB',(W,H),(20,11,2)), src, g.resize((W,H)))

    f_big  = ImageFont.truetype(FB, 86)
    f_meta = ImageFont.truetype(FB, 40)
    f_hdr  = ImageFont.truetype(FB, 52)
    f_item = ImageFont.truetype(FR, 42)
    f_step = ImageFont.truetype(FR, 44)
    f_num  = ImageFont.truetype(FB, 60)
    f_cta  = ImageFont.truetype(FB, 62)
    f_sub  = ImageFont.truetype(FR, 38)

    D = 118
    logo = Image.open(os.path.join(ROOT,'icon-512.png')).convert('RGB').crop((118,88,394,364)).resize((D,D), Image.LANCZOS)
    mk = Image.new('L',(D*4,D*4),0); ImageDraw.Draw(mk).ellipse([0,0,D*4,D*4],fill=255)
    logo.putalpha(mk.resize((D,D), Image.LANCZOS))

    def shorten(st):
        """Κρατά τον τίτλο του βήματος και την πρώτη πρόταση. Στο Reel κανείς
        δεν διαβάζει παράγραφο — και το πλήρες κείμενο είναι μέσα στην εφαρμογή."""
        head, body = (st.split(':', 1) + [''])[:2] if ':' in st[:60] else ('', st)
        body = body.strip()
        cut = body.find('. ')
        if cut > 30: body = body[:cut+1]
        if len(body) > 90: body = body[:87].rsplit(' ', 1)[0] + '…'
        return head.strip(), body

    # Στα Reels ελάχιστοι φτάνουν στο τέλος: το σύνολο κόβεται στα ~14 δευτ.,
    # αλλά η τελευταία ενότητα — αυτή που λέει πώς κατεβαίνει η εφαρμογή —
    # κρατά περισσότερο, γιατί εκεί γίνεται η μετατροπή.
    # ΣΕΙΡΑ: το πιάτο σταματά τον θεατή, η εφαρμογή του λέει αμέσως τι είναι
    # και πώς κατεβαίνει, και μετά ακολουθεί η συνταγή.
    scenes = []
    scenes.append(('hook', 2.0, None))
    scenes.append(('cta',  5.0, None))
    scenes.append(('ing',  2.5, None))
    for i, st in enumerate(steps[:2]):
        scenes.append(('step', 2.75, (i, shorten(st))))

    out = os.path.join(OUT, f'reel-{rid}-{lang}.mp4')
    proc = subprocess.Popen([FFMPEG,'-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),
        '-i','-','-c:v','libx264','-preset','medium','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',out],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    n_all = sum(round(s*FPS) for _,s,_ in scenes); FADE = round(FPS*.4); total = 0
    pad = 74

    for kind, secs, extra in scenes:
        n = round(secs*FPS)
        for i in range(n):
            p = i/max(1,n-1)
            if kind == 'hook':
                # Άλλοτε ζουμ προς τα μέσα, άλλοτε προς τα έξω
                z = (1.0+.07*p) if zoom_in else (1.07-.07*p)
                cw, ch = round(W/z), round(H/z)
                fr = bg.crop(((W-cw)//2,(H-ch)//2,(W-cw)//2+cw,(H-ch)//2+ch)).resize((W,H), Image.LANCZOS)
                fr = scrim(fr, int(H*.42))
            elif kind == 'cta':
                # Ελαφρύτερο σκίαστρο: η σκηνή ανοίγει το βίντεο, οπότε το πιάτο
                # πρέπει να φαίνεται πίσω από το κείμενο.
                fr = scrim(blur, 0, .62, .78)
            else:
                fr = scrim(blur, 0, .62, .80)
            d = ImageDraw.Draw(fr)

            if kind == 'hook':
                lines = wrap(d, name, f_big, W-2*pad)
                y = H - pad - 150 - len(lines)*100
                for ln in lines:
                    d.text((pad,y), ln, font=f_big, fill=(255,253,248)); y += 100
                meta = f"⏱ {m['time']}′   🔥 {m['cal']}   💰 {m.get('cps',m.get('cost','')).strip()}"
                d.text((pad, y+18), meta, font=f_meta, fill=(240,206,150))
            elif kind == 'ing':
                fr.paste(logo,(pad,pad),logo)
                d.text((pad, pad+D+34), L['ing'], font=f_hdr, fill=(233,178,74))
                y = pad+D+34+70
                shown = ings[:11]
                for k, it in enumerate(shown):
                    if y > H-pad-60: break
                    vis = min(1.0, max(0.0, p*len(shown)*1.25 - k))
                    if vis <= 0: continue
                    c = tuple(round(20+(252-20)*vis) for _ in range(3))
                    d.text((pad, y), '· '+it, font=f_item, fill=c); y += 62
            elif kind == 'step':
                idx, (head, body) = extra
                fr.paste(logo,(pad,pad),logo)
                d.text((pad, pad+D+34), L['how'], font=f_hdr, fill=(233,178,74))
                y = pad+D+120
                d.text((pad, y), str(idx+1), font=f_num, fill=(200,80,26))
                if head:
                    for ln in wrap(d, head, f_hdr, W-2*pad-110)[:2]:
                        d.text((pad+104, y+4), ln, font=f_hdr, fill=(255,252,246)); y += 64
                    y += 34
                else:
                    y += 84
                for ln in wrap(d, body, f_step, W-2*pad)[:7]:
                    d.text((pad,y), ln, font=f_step, fill=(248,241,229)); y += 62
            else:
                ctr = lambda t,f,yy,c: d.text(((W-d.textlength(t,font=f))/2, yy), t, font=f, fill=c)
                f_q    = ImageFont.truetype(FB, 58)
                f_bul  = ImageFont.truetype(FR, 40)
                f_url  = ImageFont.truetype(FB, 40)
                bul    = [L['b1'], L['b2'], L['b3']]
                bul    = bul[var % 3:] + bul[:var % 3]   # εναλλαγή σειράς
                bh, bw = 118, round(d.textlength(L['get'], font=f_sub)) + 170

                # Ολόκληρο το μπλοκ υπολογίζεται και κεντράρεται, ώστε να μη
                # βγαίνει έξω από το κάδρο όταν αλλάξουν τα κείμενα.
                block = (D + 30 + f_cta.size + 34 + f_q.size + 40
                         + len(bul)*56 + 44 + bh + 30 + f_sub.size + 18 + f_url.size)
                y = (H - block) // 2

                fr.paste(logo, ((W-D)//2, y), logo); y += D + 30
                ctr('FoodDaily', f_cta, y, (255,253,248)); y += f_cta.size + 34
                # Η κύρια ιδέα της εφαρμογής, με τα λόγια του χρήστη
                ctr(L['q'], f_q, y, (255,250,240)); y += f_q.size + 40
                # Κοινό αριστερό περιθώριο για όλες τις γραμμές: αν κεντραριστεί
                # η καθεμία χωριστά, οι κουκκίδες βγαίνουν σε ζιγκ-ζαγκ.
                wmax = max(d.textlength(t_, font=f_bul) for t_ in bul)
                bx0 = round((W - wmax) / 2)
                for t_ in bul:
                    d.ellipse([bx0-36, y+16, bx0-20, y+32], fill=(233,178,74))
                    d.text((bx0, y), t_, font=f_bul, fill=(243,225,192))
                    y += 56
                y += 44

                bx = (W-bw)//2
                d.rounded_rectangle([bx,y,bx+bw,y+bh], radius=bh//2, fill=(200,80,26))
                # Το ☝ δεν υπάρχει στη γραμματοσειρά — το βέλος σχεδιάζεται.
                ax, ay = bx+62, y+bh//2
                d.polygon([(ax, ay-26), (ax-20, ay-2), (ax-8, ay-2), (ax-8, ay+26),
                           (ax+8, ay+26), (ax+8, ay-2), (ax+20, ay-2)], fill=(255,255,255))
                d.text((bx+108, y+(bh-38)//2-4), L['get'], font=f_sub, fill=(255,255,255))
                y += bh + 30
                ctr(L['free'], f_sub, y, (232,204,162)); y += f_sub.size + 18
                # Και γραπτά, για όποιον δει το βίντεο εκτός πλατφόρμας.
                ctr(L['url'], f_url, y, (233,178,74))

            fade = min(1., (total+1)/FADE, (n_all-total)/FADE)
            if fade < 1.:
                fr = Image.blend(Image.new('RGB',(W,H),(0,0,0)), fr, max(0.,fade))
            proc.stdin.write(fr.tobytes()); total += 1

    proc.stdin.close(); proc.wait()
    print(f'  ✓ {os.path.basename(out)}  {total/FPS:.1f}s  {os.path.getsize(out)//1024} KB')
    return out

if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv)>1 else 'moussaka',
          sys.argv[2] if len(sys.argv)>2 else 'el')
