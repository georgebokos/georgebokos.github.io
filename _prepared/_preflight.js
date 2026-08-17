// Πλήρης έλεγχος πριν την ένθεση στο index.html. node _preflight.js
const fs=require('fs'), path=require('path');
const D=__dirname, ROOT='/home/user/georgebokos.github.io/';
const html=fs.readFileSync(ROOT+'index.html','utf8');
const CATS=['meat','desserts','vegetables','seafood','pasta','soups','salads','pites','sauces','legumes','pizza'];
const NEED=['n','en','e','cats','cal','time','srv','pop','cost','cps','ing','ing_en','steps','steps_en','wine','wine_en','plate','plate_en'];
// ΦΑΣΗ Α: μόνο οι 56 νέες. Οι 26 μεταφερόμενες (batch8*) απαιτούν πρώτα
// αφαίρεση από το SWEETS, αλλιώς διπλασιάζονται στην αναζήτηση.
const ONLY=process.env.ALL?/^batch.*\.js$/:/^batch([1-4]|[567]m).*\.js$/;
const files=fs.readdirSync(D).filter(f=>ONLY.test(f)).sort();
let errors=[], warns=[], all={};

// ── 1. Συντακτικός έλεγχος και συλλογή ──────────────────────────
for(const f of files){
  let M;
  try{ M=eval('({'+fs.readFileSync(path.join(D,f),'utf8').replace(/^\/\/.*$/gm,'')+'})'); }
  catch(e){ errors.push(`${f}: ΣΥΝΤΑΚΤΙΚΟ ΣΦΑΛΜΑ — ${e.message}`); continue; }
  for(const [k,v] of Object.entries(M)){
    if(all[k]) errors.push(`διπλό id «${k}» σε ${f} και ${all[k]._file}`);
    all[k]={...v,_file:f};
  }
}
console.log(`1. Ανάγνωση: ${files.length} αρχεία, ${Object.keys(all).length} συνταγές`);

// ── 2. Πεδία, μήκη, γλώσσες ─────────────────────────────────────
for(const [k,v] of Object.entries(all)){
  NEED.filter(x=>v[x]===undefined).forEach(x=>errors.push(`${k}: λείπει το «${x}»`));
  if(v.ing&&v.ing_en&&v.ing.length!==v.ing_en.length)errors.push(`${k}: υλικά ${v.ing.length} vs ${v.ing_en.length}`);
  if(v.steps&&v.steps_en&&v.steps.length!==v.steps_en.length)errors.push(`${k}: βήματα ${v.steps.length} vs ${v.steps_en.length}`);
  (v.cats||[]).forEach(c=>{if(!CATS.includes(c))errors.push(`${k}: άγνωστη κατηγορία «${c}»`)});
  const gr=/[Α-Ωα-ωά-ώΐΰ]/;
  if(gr.test(v.en||''))errors.push(`${k}: ελληνικά στο «en»`);
  (v.steps_en||[]).forEach((s,i)=>{if(gr.test(s))errors.push(`${k}: ελληνικά στο steps_en[${i}]`)});
  (v.ing_en||[]).forEach((s,i)=>{if(gr.test(s))errors.push(`${k}: ελληνικά στο ing_en[${i}]`)});
  if(gr.test(v.wine_en||''))errors.push(`${k}: ελληνικά στο «wine_en»`);
  if(gr.test(v.plate_en||''))errors.push(`${k}: ελληνικά στο «plate_en»`);
  // αριθμητικά λογικά
  if(!(v.cal>0&&v.cal<2000))errors.push(`${k}: παράλογες θερμίδες ${v.cal}`);
  if(!(v.time>0&&v.time<1500))errors.push(`${k}: παράλογος χρόνος ${v.time}`);
  if(!(v.srv>0&&v.srv<=60))errors.push(`${k}: παράλογες μερίδες ${v.srv}`);
  if(![1,2,3].includes(v.pop))errors.push(`${k}: pop=${v.pop} (πρέπει 1-3)`);
  if(!/€/.test(v.cost||''))errors.push(`${k}: κόστος χωρίς €`);
  if(!/€/.test(v.cps||''))errors.push(`${k}: κόστος/μερίδα χωρίς €`);
  // κενά ή πολύ κοντά κείμενα
  (v.steps||[]).forEach((s,i)=>{if(s.trim().length<25)errors.push(`${k}: πολύ σύντομο βήμα ${i}`)});
  (v.ing||[]).forEach((s,i)=>{if(!s.trim())errors.push(`${k}: κενό υλικό ${i}`)});
  if(!(v.steps||[]).some(s=>s.includes('ΣΗΜΑΝΤΙΚΟ')))warns.push(`${k}: κανένα βήμα με ΣΗΜΑΝΤΙΚΟ`);
  // εισαγωγικά που θα σπάσουν τη JS
  for(const fld of ['n','wine','plate']){
    if(typeof v[fld]==='string'&&v[fld].includes('"'))warns.push(`${k}: διπλό εισαγωγικό στο «${fld}»`);
  }
}
console.log(`2. Πεδία και τιμές: ${errors.length?errors.length+' σφάλματα':'εντάξει'}`);

// ── 3. Συγκρούσεις με το index.html ─────────────────────────────
for(const k of Object.keys(all)){
  if(new RegExp('\\n  '+k+':\\{').test(html))errors.push(`${k}: το id υπάρχει ΗΔΗ στο index.html`);
}
// ίδια ονόματα με υπάρχουσες συνταγές
const existing=new Set([...html.matchAll(/n:'([^']{3,60})'/g)].map(m=>m[1]));
for(const [k,v] of Object.entries(all)){
  if(existing.has(v.n))warns.push(`${k}: όνομα «${v.n}» υπάρχει ήδη στο index.html`);
}
console.log(`3. Συγκρούσεις με index.html: ελέγχθηκαν ${Object.keys(all).length} id`);

// ── 4. Εικόνες ──────────────────────────────────────────────────
const imgTxt=fs.readFileSync(path.join(D,'meal-images.txt'),'utf8');
const imgMap={};
for(const m of imgTxt.matchAll(/(\w+):'(images\/[\w.\-]+)'/g))imgMap[m[1]]=m[2];
for(const k of Object.keys(all)){
  const p=imgMap[k];
  if(!p){errors.push(`${k}: λείπει εγγραφή στο meal-images.txt`);continue;}
  if(!fs.existsSync(ROOT+p))errors.push(`${k}: η εικόνα ${p} δεν υπάρχει`);
}
for(const k of Object.keys(imgMap)){
  if(!all[k])warns.push(`meal-images.txt: περιττή εγγραφή «${k}»`);
}
console.log(`4. Εικόνες: ${Object.keys(imgMap).length} εγγραφές ελέγχθηκαν`);

// ── 5. Αποτέλεσμα ───────────────────────────────────────────────
console.log('\n' + '─'.repeat(60));
if(warns.length){console.log(`\n⚠ ${warns.length} προειδοποιήσεις:`);warns.forEach(w=>console.log('  •',w));}
if(errors.length){console.log(`\n❌ ${errors.length} ΣΦΑΛΜΑΤΑ:`);errors.forEach(e=>console.log('  •',e));process.exit(1);}
console.log(`\n✅ ΚΑΘΑΡΟ — ${Object.keys(all).length} συνταγές έτοιμες για ένθεση`);
