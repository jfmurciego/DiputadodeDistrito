/* PROYECTO: Diputado de Distrito
 * VERSIÓN: 1.4.0
 * NOMBRE: visor técnico con leyendas por tipo de resultado
 * QUÉ HACE: visualiza resultados certificados, con simbología M06/M08 y estado verificable.
 * ANTERIOR: visor/app.js v1.3.1
 */
let RESULTS=[];
const map=new maplibregl.Map({container:"map",style:{version:8,sources:{osm:{type:"raster",tiles:["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],tileSize:256,attribution:"© OpenStreetMap contributors"}},layers:[{id:"osm",type:"raster",source:"osm"}]},center:[-2.5,41.5],zoom:5.2});
map.addControl(new maplibregl.NavigationControl(),"top-right");
const territorySelect=document.querySelector("#territory-select"),resultSelect=document.querySelector("#result-select"),status=document.querySelector("#status"),summary=document.querySelector("#summary"),detail=document.querySelector("#detail"),legend=document.querySelector("#legend"),sourceLink=document.querySelector("#source-link"),useStatus=document.querySelector("#use-status");
const scalar=(props,names)=>{for(const n of names){if(props[n]!==undefined&&props[n]!==null&&props[n]!=="")return props[n]}return null};
const formatNumber=v=>typeof v==="number"?new Intl.NumberFormat("es-ES",{maximumFractionDigits:2}).format(v):String(v??"—");
const formatPercent=v=>{if(v===null||v===undefined||v==="")return"—";const n=Number(v);if(!Number.isFinite(n))return String(v);const pct=Math.abs(n)<=1?n*100:n;return pct.toLocaleString("es-ES",{minimumFractionDigits:2,maximumFractionDigits:2})+" %"};
const M06_BINS=[
  {label:"Menos de −10 %",color:"#2166ac"},
  {label:"−10 % a −5 %",color:"#67a9cf"},
  {label:"−5 % a +5 %",color:"#f7f7f7"},
  {label:"+5 % a +10 %",color:"#ef8a62"},
  {label:"Más de +10 %",color:"#b2182b"},
];
const PARTY_PALETTE=["#0072B2","#D55E00","#009E73","#CC79A7","#E69F00","#56B4E9","#6A3D9A","#8C564B","#2F4B7C","#7F7F7F"];
function utmToWgs84(x,y){const a=6378137,e=0.081819191,e1=(1-Math.sqrt(1-e*e))/(1+Math.sqrt(1-e*e)),k0=.9996,x1=x-500000,M=y/k0,mu=M/(a*(1-e*e/4-3*Math.pow(e,4)/64-5*Math.pow(e,6)/256));const phi1=mu+(3*e1/2-27*Math.pow(e1,3)/32)*Math.sin(2*mu)+(21*e1*e1/16-55*Math.pow(e1,4)/32)*Math.sin(4*mu)+(151*Math.pow(e1,3)/96)*Math.sin(6*mu);const ep=e*e/(1-e*e),C1=ep*Math.cos(phi1)**2,T1=Math.tan(phi1)**2,N1=a/Math.sqrt(1-e*e*Math.sin(phi1)**2),R1=a*(1-e*e)/Math.pow(1-e*e*Math.sin(phi1)**2,1.5),D=x1/(N1*k0);const lat=phi1-(N1*Math.tan(phi1)/R1)*(D*D/2-(5+3*T1+10*C1-4*C1*C1-9*ep)*D**4/24+(61+90*T1+298*C1+45*T1*T1-252*ep-3*C1*C1)*D**6/720);const lon=(-3*Math.PI/180)+(D-(1+2*T1+C1)*D**3/6+(5-2*C1+28*T1-3*C1*C1+8*ep+24*T1*T1)*D**5/120)/Math.cos(phi1);return[lon*180/Math.PI,lat*180/Math.PI]}
function transformCoordinates(v){if(typeof v[0]==="number")return Math.abs(v[0])<=180&&Math.abs(v[1])<=90?v:utmToWgs84(v[0],v[1]);return v.map(transformCoordinates)}
function normalize(data){return{...data,features:data.features.map(f=>({...f,geometry:{...f.geometry,coordinates:transformCoordinates(f.geometry.coordinates)}}))}}
function boundsFor(data){const b=new maplibregl.LngLatBounds();data.features.forEach(f=>{const visit=c=>typeof c[0]==="number"?b.extend(c):c.forEach(visit);visit(f.geometry.coordinates)});return b}
function partyEntries(data){
  const parties=[...new Set(data.features.map(f=>String(f.properties?.winner_party??"").trim()).filter(Boolean))].sort((a,b)=>a.localeCompare(b,"es"));
  const used=new Set();
  return parties.map(party=>{
    let hash=2166136261;
    for(const ch of party){hash^=ch.codePointAt(0);hash=Math.imul(hash,16777619)>>>0}
    let index=hash%PARTY_PALETTE.length;
    while(used.has(index)&&used.size<PARTY_PALETTE.length)index=(index+1)%PARTY_PALETTE.length;
    used.add(index);
    return{party,color:PARTY_PALETTE[index]};
  });
}
function fillPaint(spec,data){
  if(spec.kind==="canonical_m06")return["case",
    ["<",["to-number",["get","relative_deviation"]],-0.10],M06_BINS[0].color,
    ["<",["to-number",["get","relative_deviation"]],-0.05],M06_BINS[1].color,
    ["<=",["to-number",["get","relative_deviation"]],0.05],M06_BINS[2].color,
    ["<=",["to-number",["get","relative_deviation"]],0.10],M06_BINS[3].color,
    M06_BINS[4].color];
  if(spec.kind==="canonical_m08"){
    const entries=partyEntries(data),match=["match",["to-string",["get","winner_party"]]];
    entries.forEach(({party,color})=>match.push(party,color));
    match.push("#6b7280");
    return match;
  }
  return"#0b5cab";
}
function renderLegend(spec,data){
  legend.replaceChildren();legend.hidden=true;
  let title="",entries=[];
  if(spec.kind==="canonical_m06"){
    title="Desviación respecto a la población objetivo";
    entries=M06_BINS.map(({label,color})=>({label,color}));
  }else if(spec.kind==="canonical_m08"){
    title="Partido ganador";
    entries=partyEntries(data).map(({party,color})=>({label:party,color}));
  }
  if(!entries.length)return;
  const heading=document.createElement("h2");heading.textContent=title;legend.appendChild(heading);
  const list=document.createElement("ul");
  entries.forEach(({label,color})=>{const item=document.createElement("li"),swatch=document.createElement("span"),text=document.createElement("span");swatch.className="legend-swatch";swatch.style.backgroundColor=color;text.textContent=label;item.append(swatch,text);list.appendChild(item)});
  legend.appendChild(list);legend.hidden=false;
}
function districtHtml(props,spec){
  const id=scalar(props,["district_id","DISTRICT_ID","id"]),pop=scalar(props,["population","district_pop","POPULATION"]),target=scalar(props,["target_population","target","TARGET"]),dev=scalar(props,["relative_deviation","population_target_ratio"]),mun=scalar(props,["municipalities","municipality_names","MUNICIPALITIES"]);
  let extra="";
  if(spec?.kind==="canonical_m08"){
    const winner=scalar(props,["winner_party"]),winnerVotes=scalar(props,["winner_votes"]),winnerShare=scalar(props,["winner_share"]),totalVotes=scalar(props,["total_votes"]);
    extra=`<dt>Partido ganador</dt><dd>${formatNumber(winner)}</dd><dt>Votos del ganador</dt><dd>${formatNumber(winnerVotes)}</dd><dt>Porcentaje del ganador</dt><dd>${formatPercent(winnerShare)}</dd><dt>Votos totales</dt><dd>${formatNumber(totalVotes)}</dd>`;
  }
  return`<p class="district-title">Distrito ${formatNumber(id)}</p><dl class="detail-list"><dt>Población</dt><dd>${formatNumber(pop)}</dd><dt>Objetivo</dt><dd>${formatNumber(target)}</dd><dt>Desviación</dt><dd>${dev===null?"—":formatPercent(dev)}</dd><dt>Municipios</dt><dd>${formatNumber(mun)}</dd>${extra}</dl>`;
}
function removeDistrictLayers(){["district-fill","district-line","district-hit"].forEach(id=>map.getLayer(id)&&map.removeLayer(id));if(map.getSource("districts"))map.removeSource("districts")}
async function loadResult(id){
  const spec=RESULTS.find(r=>r.id===id);if(!spec)return;
  status.textContent=`Cargando ${spec.label}…`;detail.textContent="Pulsa un distrito para ver su ficha.";summary.hidden=true;legend.hidden=true;removeDistrictLayers();
  try{
    const response=await fetch(spec.viewer_path,{cache:"no-cache"});if(!response.ok)throw new Error(`HTTP ${response.status}`);
    const data=normalize(await response.json());if(data.type!=="FeatureCollection")throw new Error("El recurso no es un FeatureCollection.");if(spec.expected_districts&&data.features.length!==Number(spec.expected_districts))throw new Error(`Esperados ${spec.expected_districts} distritos; recibidos ${data.features.length}.`);
    map.addSource("districts",{type:"geojson",data});map.addLayer({id:"district-fill",type:"fill",source:"districts",paint:{"fill-color":fillPaint(spec,data),"fill-opacity":.52}});map.addLayer({id:"district-line",type:"line",source:"districts",paint:{"line-color":"#ffffff","line-width":1.1}});map.addLayer({id:"district-hit",type:"fill",source:"districts",paint:{"fill-color":"#000000","fill-opacity":0}});
    renderLegend(spec,data);map.fitBounds(boundsFor(data),{padding:36,maxZoom:8,duration:400});
    const geo=spec.geometric_status||"NOT_AUDITED",technical=spec.technical_status||"UNKNOWN",certification=spec.certification_status||"NOT_CERTIFIED",certified=["CERTIFIED","CERTIFIED_WITH_GOVERNED_EXCEPTIONS"].includes(certification),technicalBlocked=certification==="BLOCKED"||technical==="BLOCK"||geo==="BLOCK",publication=spec.publication_status||"BLOCKED",reasons=(spec.status_reasons||[]).join(", ")||"—";
    summary.innerHTML=`<dl><dt>Territorio</dt><dd>${spec.territory_label}</dd><dt>Resultado</dt><dd>${spec.kind}</dd><dt>Distritos</dt><dd>${data.features.length}</dd><dt>Estado técnico</dt><dd class="${technicalBlocked?'bad':'good'}">${technical}</dd><dt>Certificación técnica</dt><dd class="${technicalBlocked?'bad':'good'}">${certification}</dd><dt>Motivos de estado</dt><dd>${reasons}</dd><dt>Auditoría geométrica</dt><dd class="${geo==='BLOCK'?'bad':'good'}">${geo}</dd><dt>Publicabilidad política</dt><dd>${publication}</dd>${spec.run_id?`<dt>Run</dt><dd>${spec.run_id}</dd>`:""}</dl>${spec.geometric_gate?`<p class="gate">${spec.geometric_gate}</p>`:""}`;summary.hidden=false;
    status.textContent=technicalBlocked?`${spec.label}: resultado técnico bloqueado.`:certified?`${spec.label}: ${certification}.`:`${spec.label}: resultado visible sin certificación consolidada.`;
    useStatus.textContent=technicalBlocked?"Este resultado no supera las puertas de certificación técnica.":!certified?"No consta una certificación técnica consolidada para este resultado.":publication==="PUBLICABLE"?"Resultado autorizado para publicación según la política vigente.":"Resultado técnicamente certificado; la certificación no implica autorización política o electoral de publicación.";
    if(spec.source_url){sourceLink.href=spec.source_url;sourceLink.hidden=false}else sourceLink.hidden=true;
  }catch(error){legend.hidden=true;status.textContent=`No se pudo cargar ${spec.label}: ${error.message}`;console.error(error)}
}
function refreshResults(){const filtered=RESULTS.filter(r=>r.territory_id===territorySelect.value);resultSelect.replaceChildren(...filtered.map(r=>new Option(r.label,r.id)));if(filtered.length){resultSelect.value=filtered[0].id;loadResult(filtered[0].id)}}
async function bootstrap(){try{let response=await fetch("data/viewer-results.json",{cache:"no-cache"});if(!response.ok)throw new Error(`registro HTTP ${response.status}`);let registry=await response.json();RESULTS=registry.results||[]}catch(error){console.warn("Registro de ejecuciones no disponible; se intenta catálogo histórico.",error);const response=await fetch("data/public-products.json",{cache:"no-cache"});const registry=await response.json();RESULTS=registry.products.map(p=>({id:`static-${p.id}`,territory_id:p.id,territory_label:p.label,label:`${p.label} · producto histórico`,kind:"static",expected_districts:p.expected_districts,viewer_path:p.viewer_path,technical_status:p.technical_status||p.status,publication_status:p.publication_status||"BLOCKED",geometric_status:"LEGACY_OR_NOT_AUDITED"}))}const territories=[...new Map(RESULTS.map(r=>[r.territory_id,r.territory_label])).entries()];territorySelect.replaceChildren(...territories.map(([id,label])=>new Option(label,id)));territorySelect.addEventListener("change",refreshResults);resultSelect.addEventListener("change",()=>loadResult(resultSelect.value));refreshResults()}
map.on("click",e=>{if(!map.getLayer("district-hit"))return;const features=map.queryRenderedFeatures(e.point,{layers:["district-hit"]});if(!features.length)return;const props=features[0].properties||{},spec=RESULTS.find(r=>r.id===resultSelect.value);detail.innerHTML=districtHtml(props,spec);new maplibregl.Popup().setLngLat(e.lngLat).setHTML(districtHtml(props,spec)).addTo(map)});
map.on("mousemove",e=>{if(!map.getLayer("district-hit"))return;const f=map.queryRenderedFeatures(e.point,{layers:["district-hit"]});map.getCanvas().style.cursor=f.length?"pointer":""});
map.on("load",bootstrap);
