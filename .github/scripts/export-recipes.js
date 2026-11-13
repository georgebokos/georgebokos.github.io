const fs=require("fs"),vm=require("vm");
// Εξάγει όλα τα δεδομένα συνταγών από το index.html σε ένα JSON.
// Χρήση: node .github/scripts/export-recipes.js <αρχείο εξόδου>
const OUTFILE=process.argv[2]||"recipes.json";
const b=fs.readFileSync("index.html","utf8").match(/<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/)[1];
const g=(o,c)=>{const i=b.indexOf(o),j=b.indexOf(c,i);return b.slice(i,j+c.length)};
const ctx={};vm.createContext(ctx);
const grab=(name,open,close)=>{try{
  vm.runInContext(g(open,close).replace("const ","var ")+";this."+name+"="+name+";",ctx);
  return ctx[name];}catch(e){console.error('✗',name,e.message);return null;}};
const MEALS=grab("MEALS","const MEALS={","\n};");
const PRI=grab("MEAL_PRIORITY","const MEAL_PRIORITY={","};");
const IMG=grab("MEAL_IMAGES","const MEAL_IMAGES={","\n};");
const MAC=grab("MEAL_MACROS","const MEAL_MACROS={","]};");
const PREP=grab("MEAL_PREP","const MEAL_PREP={","\n};");
const FEST=grab("FESTIVE","const FESTIVE=[","\n];");
const out={generated:new Date().toISOString().slice(0,10),count:Object.keys(MEALS||{}).length,
  meals:MEALS,priority:PRI,images:IMG,macros:MAC,prep:PREP,festive:FEST};
fs.writeFileSync(OUTFILE,JSON.stringify(out,null,1));
console.log("συνταγές:",out.count,"· macros:",Object.keys(MAC||{}).length,
  "· priority:",Object.keys(PRI||{}).length,"· εορτές:",(FEST||[]).length,
  "·",(fs.statSync(OUTFILE).size/1048576).toFixed(1),"MB");
