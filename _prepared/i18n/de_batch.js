// Εξάγει μια παρτίδα συνταγών προς μετάφραση, ή συγχωνεύει μια μεταφρασμένη.
//   node de_batch.js out <N>    → γράφει _prepared/i18n/de/src_<N>.json
//   node de_batch.js merge      → ελέγχει ΟΛΑ τα de_*.json και τα βάζει στο lang/de.json
const fs=require('fs'), path=require('path');
const ROOT=path.resolve(__dirname,'../..');
const DIR=path.join(__dirname,'de');
const SIZE=24;                       // συνταγές ανά παρτίδα

const source=()=>require('./_dump_en.js');

const cmd=process.argv[2];
const SRC=source();
const IDS=Object.keys(SRC).sort();

if(cmd==='out'){
  const n=parseInt(process.argv[3],10);
  const ids=IDS.slice(n*SIZE,(n+1)*SIZE);
  if(!ids.length){console.log('τέλος — δεν υπάρχει παρτίδα '+n);process.exit(0);}
  const o={}; ids.forEach(i=>o[i]=SRC[i]);
  fs.mkdirSync(DIR,{recursive:true});
  fs.writeFileSync(path.join(DIR,`src_${n}.json`),JSON.stringify(o,null,1));
  console.log(`παρτίδα ${n}: ${ids.length} συνταγές (${n*SIZE+1}–${n*SIZE+ids.length} από ${IDS.length})`);
  console.log('→ '+path.join(DIR,`src_${n}.json`));
}

if(cmd==='merge'){
  const files=fs.readdirSync(DIR).filter(f=>/^de_\d+\.json$/.test(f)).sort();
  const all={}; const errs=[];
  for(const f of files){
    const d=JSON.parse(fs.readFileSync(path.join(DIR,f),'utf8'));
    for(const [id,m] of Object.entries(d)){
      const s=SRC[id];
      if(!s){errs.push(`${f}: άγνωστο id «${id}»`);continue;}
      // ΚΡΙΣΙΜΟ: πίνακας με άλλο πλήθος αγνοείται σιωπηλά από την εφαρμογή
      for(const k of ['ing','steps']){
        if(m[k]&&s[k]&&m[k].length!==s[k].length)
          errs.push(`${id}.${k}: ${m[k].length} ≠ ${s[k].length}`);
        if(m[k]&&!s[k]) errs.push(`${id}.${k}: δεν υπάρχει στα αγγλικά`);
      }
      if(m.n&&!String(m.n).trim()) errs.push(`${id}.n: κενό`);
      if(all[id]) errs.push(`διπλό id «${id}»`);
      all[id]=m;
    }
  }
  if(errs.length){console.error('❌ ΣΦΑΛΜΑΤΑ:');errs.forEach(e=>console.error('  • '+e));process.exit(1);}
  const p=path.join(ROOT,'lang','de.json');
  const pack=JSON.parse(fs.readFileSync(p,'utf8'));
  pack.meals=all;
  fs.writeFileSync(p,JSON.stringify(pack,null,1));
  const done=Object.keys(all).length;
  console.log(`✅ ${files.length} αρχεία · ${done}/${IDS.length} συνταγές στο lang/de.json`);
  console.log(`   μέγεθος: ${(fs.statSync(p).size/1024).toFixed(0)} KB`);
}
