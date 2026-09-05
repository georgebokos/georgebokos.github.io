const {chromium}=require('playwright');
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
 const p=await b.newPage(); const errs=[]; p.on('pageerror',e=>errs.push(e.message));
 await p.goto('http://localhost:8899/'+process.argv[2],{waitUntil:'load'}); await p.waitForTimeout(2200);
 const out={_errs:errs};
 const txt=s=>p.evaluate(x=>{const e=document.querySelector(x);return e?(e.innerText||'').replace(/\s+/g,' ').trim():'—';},s);
 for(const L of ['el','en']){
  await p.evaluate(l=>setLang(l),L); await p.waitForTimeout(700);
  const o={};
  await p.evaluate(()=>openR('fasolada')); await p.waitForTimeout(600);
  o.meal=await txt('#overlay');
  for(const i of [1,2,3]){ await p.evaluate(n=>{const t=document.querySelectorAll('#overlay .tab, #overlay .ov-tab');if(t[n])t[n].click();},i); await p.waitForTimeout(300); o['tab'+i]=await txt('#overlay'); }
  await p.evaluate(()=>closeOv()); await p.waitForTimeout(300);
  await p.evaluate(()=>openPremiumScreen()); await p.waitForTimeout(700); o.premium=await txt('#pscreen');
  await p.evaluate(()=>closePremiumScreen()); await p.waitForTimeout(300);
  await p.evaluate(()=>openNotif()); await p.waitForTimeout(600); o.notif=await txt('#nmod');
  await p.evaluate(()=>closeNotif()); await p.waitForTimeout(300);
  await p.evaluate(()=>openProfile()); await p.waitForTimeout(600); o.profile=await txt('.prof-modal,#prof-modal,#profile');
  await p.evaluate(()=>{try{closeProfile()}catch(e){}}); await p.waitForTimeout(300);
  await p.evaluate(()=>{try{selGuest(4)}catch(e){}}); await p.waitForTimeout(600); o.guest=await txt('#guest-res');
  await p.evaluate(()=>{const i=document.getElementById('fridge-inp');if(i){i.value='zzzqq';i.dispatchEvent(new Event('input',{bubbles:true}));}
                        try{findFridge&&findFridge()}catch(e){}}); await p.waitForTimeout(600); o.fridge=await txt('#fridge-res');
  await p.evaluate(()=>{openSearch();doSearch('zzzqqq');}); await p.waitForTimeout(700); o.search=await txt('#search-results');
  await p.evaluate(()=>{try{closeSearch()}catch(e){}}); await p.waitForTimeout(300);
  await p.evaluate(()=>{try{openWeekPlanGated()}catch(e){}}); await p.waitForTimeout(700); o.week=await txt('#weekplan,#wp-modal,.wp-modal');
  await p.evaluate(()=>{try{closeWeekPlan()}catch(e){}}); await p.waitForTimeout(300);
  o.fest=await p.evaluate(()=>{try{rendFest('all')}catch(e){} const e=document.getElementById('fest-list')||document.querySelector('.fest-grid');return e?e.innerText.replace(/\s+/g,' ').trim().slice(0,3000):'—';});
  out[L]=o;
 }
 require('fs').writeFileSync(process.argv[3],JSON.stringify(out,null,1));
 await b.close();
})();
