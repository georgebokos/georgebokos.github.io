// Εξάγει το ΑΓΓΛΙΚΟ περιεχόμενο κάθε συνταγής από το index.html.
const fs=require('fs'),vm=require('vm'),path=require('path');
const ROOT=path.resolve(__dirname,'../..');
const b=fs.readFileSync(path.join(ROOT,'index.html'),'utf8')
        .match(/<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/)[1];
const i=b.indexOf('const MEALS={'), j=b.indexOf('\n};',i);
const ctx={}; vm.createContext(ctx);
new vm.Script(b.slice(i,j+3)).runInContext(ctx);
const M=vm.runInContext('MEALS',ctx);
const out={};
for(const [id,m] of Object.entries(M)){
  const o={n:m.en||m.n_en||m.n};
  if(m.ing_en)o.ing=m.ing_en;
  if(m.steps_en)o.steps=m.steps_en;
  if(m.wine_en)o.wine=m.wine_en;
  if(m.plate_en)o.plate=m.plate_en;
  out[id]=o;
}
module.exports=out;
if(require.main===module)console.log(JSON.stringify(out));
