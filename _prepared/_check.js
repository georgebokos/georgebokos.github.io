// Ελεγκτής ποιότητας για τις νέες συνταγές. node _check.js [αρχεία…]
const fs=require('fs'),path=require('path');
const dir=__dirname;
const CATS=['meat','desserts','vegetables','seafood','pasta','soups','salads','pites','sauces','legumes','pizza'];
const need=['n','en','e','cats','cal','time','srv','pop','cost','cps','ing','ing_en','steps','steps_en','wine','wine_en','plate','plate_en'];
const html=fs.readFileSync('/home/user/georgebokos.github.io/index.html','utf8');
const files=(process.argv.slice(2).length?process.argv.slice(2):fs.readdirSync(dir).filter(f=>f.endsWith('.js')&&!f.startsWith('_')));
let ok=true;const seen=new Map();
for(const f of files){
  const p=path.isAbsolute(f)?f:path.join(dir,path.basename(f));
  const M=eval('({'+fs.readFileSync(p,'utf8').replace(/^\/\/.*$/gm,'')+'})');
  console.log('\n— '+path.basename(p));
  for(const [k,v] of Object.entries(M)){
    const bad=m=>{ok=false;console.log('  ❌',k,m);};
    const miss=need.filter(x=>v[x]===undefined);
    if(miss.length)bad('λείπουν: '+miss);
    if(v.ing.length!==v.ing_en.length)bad(`υλικά ${v.ing.length} vs ${v.ing_en.length}`);
    if(v.steps.length!==v.steps_en.length)bad(`βήματα ${v.steps.length} vs ${v.steps_en.length}`);
    (v.cats||[]).forEach(c=>{if(!CATS.includes(c))bad('άγνωστη κατηγορία '+c);});
    if(html.includes('  '+k+':{'))bad('υπάρχει ήδη στο index.html');
    if(seen.has(k))bad('διπλό id, και στο '+seen.get(k));
    seen.set(k,path.basename(p));
    if(/[Α-Ωα-ωά-ώ]/.test(v.en)||v.steps_en.some(s=>/[Α-Ωα-ωά-ώ]/.test(s))||v.ing_en.some(s=>/[Α-Ωα-ωά-ώ]/.test(s)))bad('ελληνικά σε αγγλικό πεδίο');
    if(!v.steps.some(s=>s.includes('ΣΗΜΑΝΤΙΚΟ')))bad('κανένα βήμα με ΣΗΜΑΝΤΙΚΟ');
    console.log('  ✓',k.padEnd(26),'υλ.',String(v.ing.length).padStart(2),'| βήμ.',String(v.steps.length).padStart(2),'|',(v.time+"'").padStart(5),'|',v.srv,'μερ.');
  }
}
console.log(ok?`\n✅ ΟΛΑ ΣΩΣΤΑ — ${seen.size} συνταγές έτοιμες / 56`:'\n❌ ΒΡΕΘΗΚΑΝ ΣΦΑΛΜΑΤΑ');
