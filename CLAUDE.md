# FoodDaily — Οδηγίες project

Ελληνική εφαρμογή συνταγών (PWA + Android app στο Google Play).

## Γλώσσα επικοινωνίας
Απάντα **πάντα στα ελληνικά**.

## Δομή κώδικα
- `index.html` — **όλη** η εφαρμογή σε ένα αρχείο (HTML + CSS + JS, ~1.4 MB)
- `service-worker.js` — cache, ειδοποιήσεις, timer μαγειρικής
- `manifest.json` — PWA manifest
- `.well-known/assetlinks.json` — σύνδεση site ↔ Android app
- `images/` — φωτογραφίες συνταγών
- `build.py` + `.github/workflows/build-deploy.yml` — obfuscation και deploy στο `gh-pages`

## Κανόνες εργασίας

**Push:** κάθε ολοκληρωμένη αλλαγή πάει σε **δύο** σημεία, χωρίς να το ζητήσει ο χρήστης:
```
git push -u origin <branch εργασίας>
git push origin <branch εργασίας>:main
```

**Service worker:** σε **κάθε** αλλαγή περιεχομένου, αύξησε τα `VERSION` και `CACHE` στο `service-worker.js` — αλλιώς οι χρήστες δεν παίρνουν την ενημέρωση.

**Διγλωσσία:** η εφαρμογή είναι ελληνικά/αγγλικά. Κάθε νέο κείμενο προς τον χρήστη πρέπει να μπαίνει **και στις δύο γλώσσες** (μέσω `curLang==='en'?...:...`, του πίνακα `TR`, ή των `data-i18n` attributes).

**Εικόνες:** κάθε νέα συνταγή χρειάζεται πραγματική φωτογραφία **χωρίς πνευματικά δικαιώματα** — αποκλειστικά από **Wikimedia Commons**. Καμία εικόνα με αμφίβολη άδεια.

Κάθε εικόνα που μπαίνει στο `images/` **συμπιέζεται πάντα πριν το commit**:
```python
from PIL import Image
im = Image.open(src).convert('RGB')
if im.width > 1000:
    im = im.resize((1000, round(im.height*1000/im.width)), Image.LANCZOS)
im.save(dst, 'JPEG', quality=82, optimize=True, progressive=True)
```
Μόνο `.jpg` — όχι PNG για φωτογραφίες. Στόχος: **80–150 KB** ανά εικόνα.
Μετά την προσθήκη, επαλήθευσε ότι κάθε αναφορά στο `MEAL_IMAGES`/`SWEET_IMAGES` αντιστοιχεί σε υπαρκτό αρχείο.

## Δεδομένα
`MEALS` (συνταγές), `SWEETS` (γλυκά), `FESTIVE` (γιορτές), `MEAL_PREP`, `DISLIKE_OPTS`.
Κάθε αντικείμενο έχει και πεδία με κατάληξη `_en` για τα αγγλικά (`ing_en`, `steps_en`, `n_en`, `d_en`, ...).

## Διανομή στο Google Play

- **Package ID:** `com.fooddaily.app` (δεν αλλάζει ποτέ — αλλιώς θεωρείται νέα εφαρμογή)
- **versionCode:** πρέπει **πάντα** να αυξάνεται. Τελευταίο: **20**
- **Κανάλια:** Κλειστή δοκιμή (Alpha, 53 δοκιμαστές) · Εσωτερική δοκιμή (μόνο ο ιδιοκτήτης)
- Δεν έχει βγει ακόμα σε παραγωγή — εκκρεμεί η απαίτηση 12+ δοκιμαστών για 14 ημέρες

### Δύο εκδόσεις της Android εφαρμογής
1. **TWA** (τρέχουσα, υποβλήθηκε για έλεγχο παραγωγής) — project στο `C:\Users\pco1`, χτίζεται με Bubblewrap
2. **Capacitor** (υπό δοκιμή) — project στο `C:\Users\pco1\Desktop\fooddaily-app` και `C:\Users\User\Desktop\fooddaily-app`, ενσωματωμένο WebView, native πληρωμές

Και οι δύο φορτώνουν το **ίδιο live site**. Αλλαγές στον web κώδικα εμφανίζονται αμέσως και στις δύο, χωρίς νέο build.

### ⚠️ Κανόνας προτεραιότητας (μέχρι να εγκριθεί η παραγωγή)

Η TWA βρίσκεται σε **έλεγχο για παραγωγή**. Καμία αλλαγή δεν πρέπει να θέτει σε κίνδυνο αυτή την έγκριση.

**Κάθε λειτουργία που δεν μπορεί να δουλέψει σωστά στην TWA πρέπει να απενεργοποιείται εκεί**, με έλεγχο ύπαρξης του αντίστοιχου Capacitor plugin:

| Λειτουργία | Έλεγχος |
|---|---|
| Paywall / συνδρομές | `hasNativeBilling()` |
| Ειδοποιήσεις | `isNativeApp()` |
| Κουμπί «πίσω» | `Capacitor.Plugins.App` |
| Εκφώνηση | `ttsPlugin()` |
| Κοινοποίηση | `sharePlugin()` |

Στην TWA οι λειτουργίες Premium μένουν **ξεκλείδωτες** και δεν εμφανίζεται προτροπή συνδρομής, γιατί οι αγορές εκεί εξαρτώνται από τον browser και συχνά αποτυγχάνουν.

Σειρά: **TWA → έγκριση παραγωγής → μετά ανεβαίνει η Capacitor** ως επίσημη έκδοση.

## Συνδρομές Premium

- `premium_monthly` — 1,99€/μήνα (base plan `monthly`)
- `premium_yearly` — 14,99€/χρόνο (base plan `yearly`)
- **RevenueCat** entitlement: `FoodDaily Pro`
- Public SDK key (Android): `goog_wlLGtgfQNNakMXhZIqFioFaiPoX`

Στο `purchasePremium()` η σειρά προτεραιότητας είναι:
1. RevenueCat (Capacitor, native) — ανεξάρτητο από browser
2. Digital Goods API (TWA μέσω Chrome)
3. Ενημερωτικό μήνυμα

**Μην αφαιρέσεις τη διαδρομή 2** — χρησιμοποιείται από την έκδοση που έχουν σήμερα οι δοκιμαστές.

## Γνωστά θέματα

- Το **Brave** δεν υποστηρίζει Google Play Billing → η TWA έκδοση δεν μπορεί να κάνει αγορές εκεί. Λύνεται με την Capacitor έκδοση.
- Η Google απαιτεί **Play Billing Library 8** μέχρι 31/8/2026. Η TWA δεν μπορεί να συμμορφωθεί (η βιβλιοθήκη της έχει κολλήσει στην 7.1.1) — γι' αυτό η μετάβαση σε Capacitor είναι απαραίτητη.
- Το WebView **δεν** υποστηρίζει ειδοποιήσεις service worker. Στην Capacitor έκδοση πρέπει να ξαναγραφτούν με `@capacitor/local-notifications`.

## Ασφάλεια
Το `signing.keystore` και το JSON του service account είναι **μυστικά** — ποτέ σε commit, ποτέ σε δημόσιο αρχείο.
