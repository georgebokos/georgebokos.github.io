// Ελεγκτής για τα γλυκά (δομή SWEETS). node _check-sweets.js [αρχεία…]
const fs=require('fs'),path=require('path');
const dir=__dirname;
const need=['n','n_en','e','srv','cal','ing','ing_en','steps','steps_en','q'];
const html=fs.readFileSync('/home/user/georgebokos.github.io/index.html','utf8');
const files=(process.argv.slice(2).length?process.argv.slice(2):fs.readdirSync(dir).filter(f=>/^batch[5-9].*\.js$/.test(f)));
let ok=true;const seen=new Map();
for(const f of files){
  const p=path.join(dir,path.basename(f));
  const A=eval('([' + fs.readFileSync(p,'utf8').replace(/^\/\/.*$/gm,'') + '])').flat();
  console.log('\n— '+path.basename(p));
  for(const v of A){
    const k=v.n;
    const bad=m=>{ok=false;console.log('  ❌',k,m);};
    const miss=need.filter(x=>v[x]===undefined);
    if(miss.length)bad('λείπουν: '+miss);
    if(v.ing.length!==v.ing_en.length)bad(`υλικά ${v.ing.length} vs ${v.ing_en.length}`);
    if(v.steps.length!==v.steps_en.length)bad(`βήματα ${v.steps.length} vs ${v.steps_en.length}`);
    if(html.includes("n:'"+k+"'"))bad('υπάρχει ήδη στο index.html');
    if(seen.has(k))bad('διπλό όνομα, και στο '+seen.get(k));
    seen.set(k,path.basename(p));
    if(/[Α-Ωα-ωά-ώ]/.test(v.n_en)||v.steps_en.some(s=>/[Α-Ωα-ωά-ώ]/.test(s))||v.ing_en.some(s=>/[Α-Ωα-ωά-ώ]/.test(s)))bad('ελληνικά σε αγγλικό πεδίο');
    if(!v.steps.some(s=>s.includes('ΣΗΜΑΝΤΙΚΟ')))bad('κανένα βήμα με ΣΗΜΑΝΤΙΚΟ');
    if(!v.q)bad('λείπει το πεδίο αναζήτησης q');
    console.log('  ✓',k.padEnd(30),'υλ.',String(v.ing.length).padStart(2),'| βήμ.',String(v.steps.length).padStart(2),'|',v.srv,'μερ. |',v.cal,'kcal');
  }
}
console.log(ok?`\n✅ ΟΛΑ ΣΩΣΤΑ — ${seen.size} γλυκά`:'\n❌ ΒΡΕΘΗΚΑΝ ΣΦΑΛΜΑΤΑ');
