const {chromium,devices}=require('playwright');const fs=require('fs'),zlib=require('zlib');
const S=process.argv[2];const axeSrc=fs.readFileSync(S+'/ax/package/axe.min.js','utf8');
const ML=S+'/ml/package/dist/';const B='http://localhost:8765';
const pages=['/v2/','/index.html','/nacional/','/dashboard/','/dashboard/hemiciclo.html','/dashboard/metricas.html'];
async function route(ctx,log){await ctx.route(/unpkg\.com/,r=>{const u=r.request().url();const f=u.endsWith('.css')?'maplibre-gl.css':'maplibre-gl.js';
 r.fulfill({body:fs.readFileSync(ML+f),contentType:u.endsWith('.css')?'text/css':'text/javascript'});});
 ctx.on('response',async r=>{try{const b=await r.body();log.push({u:r.url().replace(B,''),raw:b.length,gz:zlib.gzipSync(b).length});}catch(e){}});}
(async()=>{const br=await chromium.launch();const out={};
for(const p of pages){const ctx=await br.newContext({viewport:{width:1280,height:800}});const log=[];await route(ctx,log);
 const pg=await ctx.newPage();const errs=[];pg.on('console',m=>m.type()==='error'&&errs.push(m.text().slice(0,120)));pg.on('pageerror',e=>errs.push('PE '+e.message.slice(0,120)));
 await pg.goto(B+p,{waitUntil:'load'}).catch(e=>errs.push(String(e)));await pg.waitForTimeout(2500);
 await pg.evaluate(axeSrc);
 const ax=await pg.evaluate(()=>axe.run(document,{runOnly:['wcag2a','wcag2aa','wcag21aa','best-practice']}));
 // teclado
 const tabs=[];for(let i=0;i<40;i++){await pg.keyboard.press('Tab');tabs.push(await pg.evaluate(()=>{const e=document.activeElement;if(!e||e===document.body)return null;const cs=getComputedStyle(e);return{t:e.tagName,id:e.id,txt:(e.textContent||e.getAttribute('aria-label')||'').trim().slice(0,25),outline:cs.outlineStyle+' '+cs.outlineWidth,shadow:cs.boxShadow!=='none'}}));}
 const noFocusVis=tabs.filter(t=>t&&t.outline.startsWith('none')&&!t.shadow).length;
 const clickNonFocus=await pg.evaluate(()=>[...document.querySelectorAll('div[onclick],span[onclick],li[onclick]')].length);
 const skip=await pg.evaluate(()=>!![...document.querySelectorAll('a')].find(a=>/saltar|skip/i.test(a.textContent)));
 out[p]={violations:ax.violations.map(v=>({id:v.id,impact:v.impact,n:v.nodes.length,help:v.help,ej:v.nodes.slice(0,2).map(n=>n.target.join(' ')+' | '+(n.failureSummary||'').split('\n')[1])})),
  incomplete:ax.incomplete.map(v=>v.id+':'+v.nodes.length),tabsDistinct:new Set(tabs.map(t=>t&&t.id+t.txt)).size,noFocusVis,clickNonFocus,skip,errs:errs.slice(0,6),
  res:log.filter(x=>x.raw>0).map(x=>x),total_raw:log.reduce((a,x)=>a+x.raw,0),total_gz:log.reduce((a,x)=>a+x.gz,0)};
 await ctx.close();}
fs.writeFileSync(S+'/axe_out.json',JSON.stringify(out,null,1));
// carga con red lenta / móvil (solo recursos locales estrangulados; CDN simulado a mano)
const prof={'3G lenta':{down:400*1024/8,up:400*1024/8,lat:400},'4G':{down:9*1024*1024/8,up:9*1024*1024/8,lat:170}};
const perf={};
for(const dev of ['Pixel 7','escritorio']){for(const [pn,pr] of Object.entries(prof)){
 const ctx=await br.newContext(dev==='escritorio'?{viewport:{width:1280,height:800}}:{...devices[dev]});const log=[];await route(ctx,log);
 const pg=await ctx.newPage();const c=await ctx.newCDPSession(pg);await c.send('Network.enable');
 await c.send('Network.emulateNetworkConditions',{offline:false,latency:pr.lat,downloadThroughput:pr.down,uploadThroughput:pr.up});
 const t0=Date.now();await pg.goto(B+'/v2/',{waitUntil:'domcontentloaded'});const dcl=Date.now()-t0;
 await pg.waitForFunction(()=>document.querySelector('h1')&&document.querySelector('h1').textContent.trim().length>0,{timeout:120000}).catch(()=>{});const h1=Date.now()-t0;
 await pg.waitForLoadState('load').catch(()=>{});const load=Date.now()-t0;
 const m=await pg.evaluate(()=>({sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth,small:[...document.querySelectorAll('button,a,.chip')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&(r.height<44||r.width<44)}).length,total:document.querySelectorAll('button,a,.chip').length}));
 perf[dev+' '+pn]={dcl,h1,load,...m};await ctx.close();}}
fs.writeFileSync(S+'/perf_out.json',JSON.stringify(perf,null,1));await br.close();})();
