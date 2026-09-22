/* DDD visor v2.0.0 — experiencia pública ejecutiva con datos vivos. */
const RAW_BASE="https://raw.githubusercontent.com/jfmurciego/DiputadodeDistrito/main/";
const LIVE_CATALOG="publicado/visor/catalogo.json";
const LIVE_STATE="orchestracion/estado_operativo.json";
let CATALOG={territories:[]}, PROJECT_STATE={territories:[],kpis:{}}, CURRENT=null;

const $=s=>document.querySelector(s);
const territorySelect=$("#territory-select"), resultSelect=$("#result-select"), summary=$("#summary"),
      detail=$("#detail"), legend=$("#legend"), mapMessage=$("#map-message"),
      territoryBadge=$("#territory-badge"), freshness=$("#freshness"),
      kpiGrid=$("#kpi-grid"), territoryStatusGrid=$("#territory-status-grid");

const map=new maplibregl.Map({
  container:"map",
  style:{version:8,sources:{osm:{type:"raster",tiles:["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],tileSize:256,attribution:"© OpenStreetMap contributors"}},layers:[{id:"osm",type:"raster",source:"osm"}]},
  center:[-3.5,40.2],zoom:5
});
map.addControl(new maplibregl.NavigationControl(),"top-right");

const M06_BINS=[
  {label:"Más de 10 % por debajo del objetivo",color:"#2166ac"},
  {label:"Entre 5 % y 10 % por debajo",color:"#67a9cf"},
  {label:"Dentro de ±5 %",color:"#f7f7f7"},
  {label:"Entre 5 % y 10 % por encima",color:"#ef8a62"},
  {label:"Más de 10 % por encima del objetivo",color:"#b2182b"}
];
const PARTY_PALETTE=["#0072B2","#D55E00","#009E73","#CC79A7","#E69F00","#56B4E9","#6A3D9A","#8C564B","#2F4B7C","#7F7F7F"];

function scalar(props,names){for(const n of names){const v=props?.[n];if(v!==undefined&&v!==null&&v!=="")return v}return null}
function num(v){const n=Number(v);return Number.isFinite(n)?n:null}
function fmt(v,d=0){const n=num(v);return n===null?"—":new Intl.NumberFormat("es-ES",{maximumFractionDigits:d}).format(n)}
function pct(v){const n=num(v);if(n===null)return"—";const x=Math.abs(n)<=1?n*100:n;return x.toLocaleString("es-ES",{minimumFractionDigits:1,maximumFractionDigits:1})+" %"}
function year(p){if(p?.election_date)return String(p.election_date).slice(0,4);return String(p?.election_id||"").match(/20\d{2}/)?.[0]||null}
function productLabel(p){return p.kind==="electoral"?`Electoral · elecciones ${year(p)||"vigentes"}`:"Territorial y censal"}
function productSubtitle(p){return p.kind==="electoral"?"Resultados electorales incorporados después de fijar los distritos.":"Distribución territorial y población por distrito."}
function rawUrl(path){return /^https?:\/\//.test(path)?path:RAW_BASE+String(path).replace(/^\/+/ ,"")}
async function fetchJson(primary,fallback){
  const v=Date.now();
  try{const r=await fetch(rawUrl(primary)+`?v=${v}`,{cache:"no-store"});if(!r.ok)throw new Error(`HTTP ${r.status}`);return await r.json()}
  catch(e){if(!fallback)throw e;const r=await fetch(`${fallback}?v=${v}`,{cache:"no-store"});if(!r.ok)throw e;return await r.json()}
}
function projectRow(id){return PROJECT_STATE.territories?.find(r=>r.territory_id===id)||null}
function publicStatus(r){
  if(!r)return{className:"gray",label:"Estado pendiente"};
  if(r.re==="green")return{className:"green",label:"Territorio y resultados electorales disponibles"};
  if(r.g==="green")return{className:"blue",label:"Distritos territoriales disponibles"};
  if(r.ft==="green"||r.g==="yellow")return{className:"yellow",label:"En preparación"};
  if(r.ft==="red"||r.g==="red")return{className:"red",label:"No incorporado"};
  return{className:"gray",label:"Pendiente"};
}
function removeLayers(){["district-fill","district-line","district-hit"].forEach(id=>map.getLayer(id)&&map.removeLayer(id));if(map.getSource("districts"))map.removeSource("districts")}
function boundsFor(data){const b=new maplibregl.LngLatBounds(),visit=c=>{if(!Array.isArray(c)||!c.length)return;if(typeof c[0]==="number")b.extend(c);else c.forEach(visit)};data.features.forEach(f=>visit(f.geometry?.coordinates));return b}
function partyEntries(data){
  const parties=[...new Set(data.features.map(f=>String(f.properties?.winner_party??"").trim()).filter(Boolean))].sort((a,b)=>a.localeCompare(b,"es")),used=new Set();
  return parties.map(p=>{let h=2166136261;for(const ch of p){h^=ch.codePointAt(0);h=Math.imul(h,16777619)>>>0}let i=h%PARTY_PALETTE.length;while(used.has(i)&&used.size<PARTY_PALETTE.length)i=(i+1)%PARTY_PALETTE.length;used.add(i);return{party:p,color:PARTY_PALETTE[i]}})
}
function fillPaint(p,data){
  if(p.kind==="territorial")return["case",["<",["to-number",["get","relative_deviation"]],-0.10],M06_BINS[0].color,["<",["to-number",["get","relative_deviation"]],-0.05],M06_BINS[1].color,["<=",["to-number",["get","relative_deviation"]],0.05],M06_BINS[2].color,["<=",["to-number",["get","relative_deviation"]],0.10],M06_BINS[3].color,M06_BINS[4].color];
  const entries=partyEntries(data),match=["match",["to-string",["get","winner_party"]]];entries.forEach(({party,color})=>match.push(party,color));match.push("#7b8794");return match
}
function renderLegend(p,data){
  legend.replaceChildren();legend.hidden=true;let title="",entries=[];
  if(p.kind==="territorial"){title="Equilibrio de población";entries=M06_BINS}
  else{title="Partido más votado";entries=partyEntries(data).map(({party,color})=>({label:party,color}))}
  if(!entries.length)return;
  const h=document.createElement("h2");h.textContent=title;const ul=document.createElement("ul");
  entries.forEach(({label,color})=>{const li=document.createElement("li"),sw=document.createElement("span"),tx=document.createElement("span");sw.className="legend-swatch";sw.style.backgroundColor=color;tx.textContent=label;li.append(sw,tx);ul.appendChild(li)});
  legend.append(h,ul);legend.hidden=false
}
function districtHtml(props,p){
  const id=scalar(props,["district_id","DISTRICT_ID","id"]),pop=scalar(props,["population","district_pop","POPULATION"]),
        target=scalar(props,["target_population","target","TARGET"]),dev=scalar(props,["relative_deviation","population_target_ratio"]),
        mun=scalar(props,["municipalities","municipality_names","MUNICIPALITIES"]);
  let rows=[["Población",fmt(pop)],["Objetivo de población",fmt(target)],["Desviación",pct(dev)],["Municipios",mun??"—"]];
  if(p.kind==="electoral")rows=[["Partido más votado",scalar(props,["winner_party"])??"—"],["Porcentaje",pct(scalar(props,["winner_share"]))],["Votos del ganador",fmt(scalar(props,["winner_votes"]))],["Votos totales",fmt(scalar(props,["total_votes"]))],["Población",fmt(pop)]];
  return `<p class="district-title">Distrito ${id??"—"}</p><dl class="detail-list">${rows.map(([a,b])=>`<dt>${a}</dt><dd>${b}</dd>`).join("")}</dl>`
}
function stats(data,p,edition){
  const pops=data.features.map(f=>num(scalar(f.properties,["population","district_pop","POPULATION"]))).filter(v=>v!==null),
        devs=data.features.map(f=>num(scalar(f.properties,["relative_deviation","population_target_ratio"]))).filter(v=>v!==null),
        votes=data.features.map(f=>num(scalar(f.properties,["total_votes"]))).filter(v=>v!==null);
  const out=[["Distritos",fmt(data.features.length)],["Población",pops.length?fmt(pops.reduce((a,b)=>a+b,0)):"—"]];
  if(p.kind==="electoral")out.push(["Votos contabilizados",votes.length?fmt(votes.reduce((a,b)=>a+b,0)):"—"],["Elecciones",year(p)||"Vigentes"]);
  else out.push(["Desviación máxima",devs.length?pct(Math.max(...devs.map(v=>Math.abs(v)))):"—"],["Edición",edition||"2025"]);
  return out
}
function renderSummary(t,p,data){
  summary.innerHTML=`<div class="summary-title"><h2>${t.name}</h2><p>${productSubtitle(p)}</p></div><div class="stat-grid">${stats(data,p,t.edition).map(([a,b])=>`<div class="stat"><span>${a}</span><strong>${b}</strong></div>`).join("")}</div>`;
  const r=projectRow(t.territory_id),s=publicStatus(r);territoryBadge.className=`territory-badge ${s.className}`;territoryBadge.textContent=r?.status||s.label
}
async function loadResult(key){
  const t=CATALOG.territories.find(x=>x.territory_id===territorySelect.value),p=t?.products.find(x=>`${t.territory_id}:${x.kind}`===key);if(!t||!p)return;
  mapMessage.textContent=`Cargando ${productLabel(p).toLowerCase()}…`;detail.innerHTML='<span class="detail-empty">Pulsa un distrito para ver sus datos.</span>';legend.hidden=true;removeLayers();
  try{
    const r=await fetch(rawUrl(p.source_path)+`?v=${Date.now()}`,{cache:"no-store"});if(!r.ok)throw new Error(`HTTP ${r.status}`);const data=await r.json();
    if(data.type!=="FeatureCollection")throw new Error("El recurso no es un mapa de distritos.");
    if(p.districts&&data.features.length!==Number(p.districts))throw new Error(`El mapa contiene ${data.features.length} distritos; se esperaban ${p.districts}.`);
    CURRENT={data,product:p};map.addSource("districts",{type:"geojson",data});map.addLayer({id:"district-fill",type:"fill",source:"districts",paint:{"fill-color":fillPaint(p,data),"fill-opacity":.58}});map.addLayer({id:"district-line",type:"line",source:"districts",paint:{"line-color":"#fff","line-width":1.15}});map.addLayer({id:"district-hit",type:"fill",source:"districts",paint:{"fill-color":"#000","fill-opacity":0}});
    const b=boundsFor(data);if(!b.isEmpty())map.fitBounds(b,{padding:38,maxZoom:8,duration:450});renderLegend(p,data);renderSummary(t,p,data);
    mapMessage.textContent=p.kind==="electoral"?"Resultados incorporados después de fijar los distritos.":"Datos territoriales y censales del producto vigente."
  }catch(e){CURRENT=null;mapMessage.textContent=`No se pudo cargar esta vista: ${e.message}`;console.error(e)}
}
function refreshProducts(){
  const t=CATALOG.territories.find(x=>x.territory_id===territorySelect.value),products=t?.products||[];
  resultSelect.replaceChildren(...products.map(p=>new Option(productLabel(p),`${t.territory_id}:${p.kind}`)));
  const preferred=products.find(p=>p.kind==="electoral")||products.find(p=>p.kind==="territorial");
  if(preferred){resultSelect.value=`${t.territory_id}:${preferred.kind}`;loadResult(resultSelect.value)}
}
function renderProjectState(){
  const k=PROJECT_STATE.kpis||{},cards=[["Cadena completa",k.complete??0,"Territorio + elecciones"],["Distritos disponibles",k.territorial_validated??k.validated??0,"Generación territorial"],["En preparación",k.ready??0,"Siguiente fase preparada"],["Pendientes",Number(k.pending??0)+Number(k.blocked??0),"Por completar"]];
  kpiGrid.innerHTML=cards.map(([a,b,c])=>`<article class="kpi"><span>${a}</span><strong>${fmt(b)}</strong><small>${c}</small></article>`).join("");
  territoryStatusGrid.innerHTML=(PROJECT_STATE.territories||[]).map(r=>{const s=publicStatus(r);return `<article class="territory-card ${s.className}"><span class="dot" aria-hidden="true"></span><div><strong>${r.name}</strong><small>${r.status||s.label}</small></div></article>`}).join("")
}
function legacyCatalog(registry){
  const g=new Map();for(const x of registry.results||[]){if(!["canonical_m06","canonical_m08","static"].includes(x.kind))continue;const id=x.territory_id;if(!g.has(id))g.set(id,{territory_id:id,name:x.territory_label||id,edition:"2025",products:[]});g.get(id).products.push({kind:x.kind==="canonical_m08"?"electoral":"territorial",source_path:x.viewer_path,districts:x.expected_districts})}return{schema:"legacy",territories:[...g.values()]}
}
async function loadCatalog(){try{return await fetchJson(LIVE_CATALOG,"data/catalogo.json")}catch(e){console.warn("Catálogo vivo no disponible; usando snapshot legado.",e);const r=await fetch("data/viewer-results.json",{cache:"no-store"});if(!r.ok)throw e;return legacyCatalog(await r.json())}}
async function loadState(){try{return await fetchJson(LIVE_STATE,"data/estado-operativo.json")}catch(e){console.warn("Estado vivo no disponible.",e);return{territories:[],kpis:{}}}}
async function bootstrap(){
  [CATALOG,PROJECT_STATE]=await Promise.all([loadCatalog(),loadState()]);
  const d=PROJECT_STATE.generated_at?new Date(PROJECT_STATE.generated_at):null;freshness.textContent=d&&!Number.isNaN(d.getTime())?`Estado actualizado ${new Intl.DateTimeFormat("es-ES",{day:"numeric",month:"short",hour:"2-digit",minute:"2-digit"}).format(d)}`:"Estado consultado al abrir la página";
  renderProjectState();const available=CATALOG.territories.filter(t=>(t.products||[]).length);territorySelect.replaceChildren(...available.map(t=>new Option(t.name,t.territory_id)));territorySelect.addEventListener("change",refreshProducts);resultSelect.addEventListener("change",()=>loadResult(resultSelect.value));
  if(available.length){const preferred=available.find(t=>t.territory_id==="galicia")||available[0];territorySelect.value=preferred.territory_id;refreshProducts()}else{territoryBadge.textContent="Sin territorios publicados";mapMessage.textContent="Todavía no hay productos disponibles en el catálogo público."}
}
map.on("click",e=>{if(!CURRENT||!map.getLayer("district-hit"))return;const f=map.queryRenderedFeatures(e.point,{layers:["district-hit"]});if(!f.length)return;const html=districtHtml(f[0].properties||{},CURRENT.product);detail.innerHTML=html;new maplibregl.Popup().setLngLat(e.lngLat).setHTML(html).addTo(map)});
map.on("mousemove",e=>{if(!map.getLayer("district-hit"))return;map.getCanvas().style.cursor=map.queryRenderedFeatures(e.point,{layers:["district-hit"]}).length?"pointer":""});
map.on("load",bootstrap);
