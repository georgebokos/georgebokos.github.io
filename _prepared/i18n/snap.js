const {chromium}=require('playwright');
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
 const p=await b.newPage(); const errs=[]; p.on('pageerror',e=>errs.push(e.message));
 await p.goto('http://localhost:8899/'+process.argv[2],{waitUntil:'load'});
 await p.waitForTimeout(2500);
 const out={};
 for(const L of ['el','en']){
   await p.evaluate(l=>setLang(l),L); await p.waitForTimeout(900);
   out[L]=await p.evaluate(()=>{
     const g=s=>[...document.querySelectorAll(s)].map(e=>e.textContent.trim()).join('|');
     return {nav:g('.ntab'),cats:g('.cpill'),hero:g('.hero-greeting,.hero-title,#sub-lbl'),
       cards:g('.meal-card .m-name'), feat:g('.feat-meal-name,.feat-cooked-badge,.feat-go-btn,.feat-act-btn'),
       more:g('.more-hdr h3'), body:document.body.innerText.replace(/\s+/g,' ').slice(0,6000)};
   });
 }
 out._errs=errs;
 require('fs').writeFileSync(process.argv[3],JSON.stringify(out,null,1));
 await b.close();
})();
