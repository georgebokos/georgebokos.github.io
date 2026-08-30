# Βοήθεια με φωτογραφία — Premium

Ο χρήστης κολλάει σε ένα βήμα, τραβά φωτογραφία, παίρνει οδηγία. Είναι η
**μοναδική** λειτουργία επί πληρωμή — οι οδηγοί μένουν δωρεάν.

**Πληρώνει ο χρήστης, όχι εσύ.** Ο worker επαληθεύει τη συνδρομή στο
RevenueCat πριν από κάθε φωτογραφία και κρατά μετρητή, ώστε το κόστος να μην
ξεπερνά ποτέ τα έσοδα.

```
Εφαρμογή Android ──αγορά──► Google Play ──► RevenueCat
       │                                        │ webhook
       │ φωτογραφία + app_user_id               ▼
       └──────────────────► Worker ◄──επαλήθευση── RevenueCat API
                              │  (κρατά κλειδιά, μετρά όρια)
                              ▼
                          Claude API
```

## ⚠ Τι πρέπει να ξέρεις πριν ξεκινήσεις

**1. Το Google Play Billing δουλεύει ΜΟΝΟ μέσα σε εφαρμογή Android.**
Η σελίδα στο `georgebokos.github.io/diy/` δεν μπορεί να δεχτεί πληρωμή. Πρέπει
να πακεταριστεί ως εφαρμογή (Capacitor, όπως το FoodDaily) και να ανέβει στο
Play. Μέχρι τότε το paywall δείχνει «η αγορά γίνεται μέσα από την εφαρμογή».
Σε iPhone και browser δεν θα υπάρχει ποτέ αγορά με αυτή τη διαδρομή.

**2. Ο έλεγχος γίνεται στον server, όχι στη σελίδα.**
Ό,τι λέει ο πελάτης αγνοείται. Δοκιμασμένο: πλαστό `premium:true` από τον
πελάτη επιστρέφει 402.

**3. Το όριο ανά συνδρομητή δεν είναι προαιρετικό.**
Χωρίς το KV binding `RL` δεν μετριέται τίποτα και ένας χρήστης μπορεί να
στείλει απεριόριστες φωτογραφίες με δικό σου κόστος.

## Πόσο να βάλω — τα νούμερα

Κάθε φωτογραφία κοστίζει **~2–4 λεπτά του ευρώ** (`claude-opus-5`, εικόνα
1024 px, απάντηση 120–220 λέξεις).

| Τιμή συνδρομής | Μετά την προμήθεια Play (15%) | Καλύπτει περίπου | Ασφαλές `SUB_MONTHLY_QUOTA` |
|---|---|---|---|
| 1,99 €/μήνα | 1,69 € | ~55 φωτογραφίες | **40** |
| 2,99 €/μήνα | 2,54 € | ~85 φωτογραφίες | **60** |
| 4,99 €/μήνα | 4,24 € | ~140 φωτογραφίες | **100** |

Για πακέτα, ίδια λογική: 20 φωτογραφίες κοστίζουν σου ~0,60 €, οπότε τιμή
2,99 € αφήνει περιθώριο ακόμη και με την προμήθεια.

Το προεπιλεγμένο `SUB_MONTHLY_QUOTA = 60` ταιριάζει σε συνδρομή 2,99 €.
**Αν αλλάξεις τιμή, άλλαξε και το όριο.**

Ένας κανονικός χρήστης στέλνει 3–10 φωτογραφίες τον μήνα. Το όριο δεν είναι
για να τον περιορίσει — είναι για να μη σε καταστρέψει ένας κακόβουλος.

## Εγκατάσταση

### 1. RevenueCat

1. Λογαριασμός στο [revenuecat.com](https://www.revenuecat.com), νέο project.
2. Σύνδεση με το Google Play (Service Account, όπως το έκανες στο FoodDaily).
3. **Entitlement** με ταυτότητα `DIY Pro`.
4. **Products** από το Play Console:
   - `diy_premium_monthly` — συνδρομή, συνδεμένη με το entitlement
   - `diy_photos_20`, `diy_photos_50` — *consumable* προϊόντα (πακέτα)
5. **Offering** `default` με τα παραπάνω ως packages.
6. Στα **API keys**: κράτα το *public* (Android) για την εφαρμογή και το
   *secret* για τον worker.

### 2. Worker

```bash
cd diy/worker
npm install

npx wrangler secret put ANTHROPIC_API_KEY    # κλειδί Anthropic
npx wrangler secret put RC_SECRET_KEY        # ΜΥΣΤΙΚΟ κλειδί RevenueCat
npx wrangler secret put RC_WEBHOOK_TOKEN     # φτιάξε ένα τυχαίο, π.χ. openssl rand -hex 24

npx wrangler kv namespace create RL          # ΑΠΑΡΑΙΤΗΤΟ για τα όρια
# αντίγραψε το id στο wrangler.toml, στο [[kv_namespaces]]

npx wrangler deploy
```

Στο `wrangler.toml` ρύθμισε `ENTITLEMENT_ID`, `SUB_MONTHLY_QUOTA`,
`PACK_PRODUCTS` (product id → πόσες φωτογραφίες).

### 3. Webhook RevenueCat

Στο RevenueCat → **Integrations → Webhooks**:
- URL: `https://<ο worker σου>.workers.dev/rc-webhook`
- Authorization header: ό,τι έβαλες στο `RC_WEBHOOK_TOKEN`

Χωρίς αυτό η εφαρμογή δουλεύει (ο worker ρωτά μόνος του το RevenueCat), αλλά
τα πακέτα φωτογραφιών πιστώνονται με καθυστέρηση.

### 4. Σύνδεση με την εφαρμογή

Στο `diy/index.html`:
```js
const HELP_ENDPOINT  = 'https://<ο worker σου>.workers.dev';
const RC_PUBLIC_KEY  = 'goog_…';        // public — δεν είναι μυστικό
const ENTITLEMENT_ID = 'DIY Pro';
const PLAY_URL       = 'https://play.google.com/store/apps/details?id=…';
```
Αύξησε το `VERSION` στο `diy/sw.js` και κάνε push.

**Δοκιμή χωρίς νέο build:** άνοιξε τη σελίδα με
`?help=https://…workers.dev&rc=goog_…`. Οι τιμές μένουν μόνο στη συσκευή σου.

### 5. Εφαρμογή Android

Δεν υπάρχει ακόμη. Χρειάζεται Capacitor project που φορτώνει το
`https://georgebokos.github.io/diy/`, με το plugin:

```bash
npm install @revenuecat/purchases-capacitor
npx cap sync android
```

Το ίδιο μοτίβο με το FoodDaily, αλλά **δικό της package id** (π.χ.
`com.diyodigos.app`) και δική της καταχώρηση στο Play.

## Διαδρομές του worker

| Διαδρομή | Τι κάνει |
|---|---|
| `GET /status` | `{ active, plan, quotaLeft, credits }` για τη διεπαφή |
| `POST /help` | Επαλήθευση → ανάλυση → χρέωση μίας φωτογραφίας |
| `POST /rc-webhook` | Συμβάντα RevenueCat (αγορές, ανανεώσεις, λήξεις) |

Όλες θέλουν `X-App-User-Id` (το app_user_id του RevenueCat), εκτός από το
webhook που ταυτοποιείται με το `RC_WEBHOOK_TOKEN`.

Η χρέωση γίνεται **μόνο μετά από επιτυχημένη απάντηση**: αν αποτύχει το
μοντέλο, ο χρήστης δεν χάνει φωτογραφία.

## Ασφάλεια περιεχομένου

Το system prompt στο `buildSystem()` επιβάλλει:
- να μην εικάζει για ό,τι δεν φαίνεται καθαρά στη φωτογραφία
- να λέει ρητά πότε χρειάζεται αδειούχος επαγγελματίας (πίνακας, αέριο,
  καυστήρας, φέροντα) — τότε επιστρέφει `callPro: true` και η εφαρμογή το
  δείχνει με κόκκινο πλαίσιο
- να μην προτείνει ποτέ παράκαμψη μέτρου ασφαλείας, γείωσης ή ρελέ
- σε καμένα ηλεκτρολογικά, να στέλνει στη γενική ασφάλεια και σε ηλεκτρολόγο

**Μην χαλαρώσεις αυτούς τους κανόνες.**

## Ιδιωτικότητα

Η φωτογραφία σμικρύνεται στη συσκευή στα 1024 px, περνά από τον worker και
δεν αποθηκεύεται πουθενά. Στο KV μένει μόνο: κατάσταση συνδρομής, μετρητής
φωτογραφιών, υπόλοιπο πακέτων και ids συναλλαγών.

## Έλεγχος ότι δουλεύει

```bash
# Χωρίς συνδρομή → 402
curl -s -o /dev/null -w '%{http_code}\n' -X POST https://<worker>/help \
  -H 'Origin: https://georgebokos.github.io' -H 'X-App-User-Id: test123' \
  -H 'Content-Type: application/json' -d '{"image":"//9k="}'

# Κατάσταση χρήστη
curl -s https://<worker>/status \
  -H 'Origin: https://georgebokos.github.io' -H 'X-App-User-Id: test123'
```

Στο Play, φτιάξε **δοκιμαστικό λογαριασμό** (License testing) για να κάνεις
αγορές χωρίς χρέωση.
