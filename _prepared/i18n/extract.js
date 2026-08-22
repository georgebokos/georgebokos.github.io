// Εξάγει ΟΛΟ το μεταφράσιμο υλικό από το index.html σε πρότυπο πακέτου.
// Πηγή είναι τα αγγλικά (πληρέστερα και ευκολότερα ως ενδιάμεση γλώσσα).
// Χρήση: node extract.js [αρχείο εξόδου]
const fs=require('fs'),path=require('path'),vm=require('vm');
const ROOT=path.resolve(__dirname,'../..');
const html=fs.readFileSync(path.join(ROOT,'index.html'),'utf8');
const body=html.match(/<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/)[1];

// Απομονώνουμε μόνο τις δηλώσεις δεδομένων — όχι τον κώδικα που αγγίζει το DOM.
const ctx={window:{},document:{documentElement:{},querySelector:()=>null,querySelectorAll:()=>[],getElementById:()=>null,addEventListener:()=>{}},navigator:{},localStorage:{getItem:()=>null,setItem:()=>{}},location:{},console};
ctx.globalThis=ctx;
function grab(name,open,close){
  const i=body.indexOf(open); if(i<0)throw new Error('δεν βρέθηκε '+open);
  const j=body.indexOf(close,i); if(j<0)throw new Error('δεν κλείνει '+open);
  return body.slice(i,j+close.length);
}
const src=[grab('TR','const TR={','\n};'),
           grab('MEALS','const MEALS={','\n};'),
           grab('SWEETS','const SWEETS={','\n};'),
           grab('FESTIVE','const FESTIVE=[','\n];'),
           grab('MEAL_PREP','const MEAL_PREP={','\n};')].join('\n');
vm.createContext(ctx); new vm.Script(src+'\n;({TR,MEALS,SWEETS,FESTIVE,MEAL_PREP})').runInContext(ctx);
const {TR,MEALS,SWEETS,FESTIVE,MEAL_PREP}=new vm.Script('({TR,MEALS,SWEETS,FESTIVE,MEAL_PREP})').runInContext(ctx);

const pick=(o,map)=>{const r={};for(const[dst,srcKey]of map){const v=o[srcKey];if(v!==undefined&&v!==''&&!(Array.isArray(v)&&!v.length))r[dst]=v;}return r;};
const out={lang:'XX',ui:{},meals:{},sweets:{},fest:{},prep:{}};

// Περιβάλλον: κάθε κλειδί του ελληνικού TR, με το αγγλικό ως πηγή
let uiN=0;
for(const k of Object.keys(TR.el)){
  const v=TR.en[k]!==undefined?TR.en[k]:TR.el[k];
  out.ui[k]=v; uiN++;
}
for(const[id,m]of Object.entries(MEALS))
  out.meals[id]=pick(m,[['n','en'],['n','n_en'],['ing','ing_en'],['steps','steps_en'],['wine','wine_en'],['plate','plate_en']]);
for(const[c,arr]of Object.entries(SWEETS))
  arr.forEach((s,i)=>{out.sweets[c+':'+i]=pick(s,[['n','n_en'],['ing','ing_en'],['steps','steps_en']]);});
FESTIVE.forEach((f,i)=>{out.fest['f'+i]=pick(f,[['n','n_en'],['d','d_en'],['tl','tl_en'],['sub','sub_en'],['fn','fn_en'],['menu','menu_en'],['wine','wine_en'],['wt','wt_en'],['tl2','tl2_en']]);});
for(const[id,p]of Object.entries(MEAL_PREP))out.prep[id]=pick(p,[['msg','msg_en']]);

const dest=process.argv[2]||path.join(__dirname,'template.json');
fs.writeFileSync(dest,JSON.stringify(out,null,1));
const count=o=>JSON.stringify(o).match(/"/g).length;
let strs=0,words=0;
const walk=v=>{if(typeof v==='string'){strs++;words+=v.split(/\s+/).length;}else if(v&&typeof v==='object')Object.values(v).forEach(walk);};
walk(out);
console.log(`περιβάλλον: ${uiN} κλειδιά`);
console.log(`συνταγές: ${Object.keys(out.meals).length} | γλυκά: ${Object.keys(out.sweets).length} | γιορτές: ${Object.keys(out.fest).length} | προετοιμασία: ${Object.keys(out.prep).length}`);
console.log(`σύνολο: ${strs} κείμενα, ~${words} λέξεις, ${(fs.statSync(dest).size/1024).toFixed(0)} KB`);
console.log('→ '+dest);
