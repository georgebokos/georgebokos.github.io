// Στιγμιότυπα καταχώρισης Play Store από την πραγματική εφαρμογή.
// 1080×1920 (9:16) — το πρότυπο μέγεθος για τηλέφωνα.
// Χρήση: node store/shots.js el|en
const {chromium}=require('playwright');
const fs=require('fs');
const LANG=process.argv[2]||'el';
const DIR='store/screenshots-'+LANG;
fs.rmSync(DIR,{recursive:true,force:true}); fs.mkdirSync(DIR,{recursive:true});
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
 const p=await b.newPage({viewport:{width:540,height:960},deviceScaleFactor:2,
   userAgent:'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36'});
 const errs=[]; p.on('pageerror',e=>errs.push(e.message));
 // Καρφιτσώνουμε την πρόταση ημέρας, ώστε τα στιγμιότυπα να είναι επαναλήψιμα
 // και να δείχνουν πάντα ένα πιάτο με καλή φωτογραφία.
 await p.addInitScript(()=>{
   // ΠΡΟΣΟΧΗ: η εφαρμογή χρησιμοποιεί toDateString(), όχι ISO ημερομηνία.
   localStorage.setItem('fd_feat',JSON.stringify({id:'giouvetsi',date:new Date().toDateString()}));
 });
 await p.goto('http://localhost:8899/index.html',{waitUntil:'load'});
 await p.waitForTimeout(2500);
 await p.evaluate(l=>setLang(l),LANG); await p.waitForTimeout(1000);
 const shot=async(n,fn)=>{ await p.evaluate(fn); await p.waitForTimeout(1100);
   await p.screenshot({path:`${DIR}/${n}.png`}); console.log('  ✓',n); };

 await shot('1-arxiki',      ()=>{window.scrollTo(0,0);});
 await shot('2-katigories',  ()=>{window.scrollTo(0,300);});
 await shot('3-syntagi',     ()=>{openR('moussaka');});
 await shot('4-ektelesi',    ()=>{const t=document.querySelectorAll('#overlay .otab');if(t[1])t[1].click();});
 await shot('5-tairiasma',   ()=>{const t=document.querySelectorAll('#overlay .otab');if(t[2])t[2].click();});
 await shot('6-kalesmenoi',  ()=>{closeOv();showSec('guests','guests');setTimeout(()=>{try{selGuest(6)}catch(e){}},200);window.scrollTo(0,0);});
 await shot('7-eortes',      ()=>{showSec('festive','festive');window.scrollTo(0,0);});
 await shot('8-psygeio',     ()=>{
      // Το Ψυγείο είναι δική του ενότητα, όχι λειτουργία του «Καθημερινά».
      showSec('fridge','fridge');
      const en=document.documentElement.lang==='en';
      const i=document.getElementById('fridge-inp');
      // Τα υλικά μπαίνουν ως ετικέτες, όπως ακριβώς τα προσθέτει ο χρήστης.
      for(const v of (en?['mince','tomato','onion']:['κιμάς','ντομάτα','κρεμμύδι'])){ i.value=v; addTag(); }
      // Να φαίνονται ΚΑΙ τα υλικά που πληκτρολόγησε ο χρήστης ΚΑΙ τα αποτελέσματα.
      window.scrollTo(0,150);
    });
 console.log(errs.length?'⚠ σφάλματα JS: '+errs.join(' | '):'✅ κανένα σφάλμα JS');
 await b.close();
})();
