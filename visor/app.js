/* PROYECTO: Diputado de Distrito
 * VERSIÓN: 1.3.0
 * NOMBRE: visor técnico multiresultado
 * QUÉ HACE: muestra resultado canónico y alternativas GerryChain desde un único visor.
 * CAMBIO: añade selector de resultado, metadatos de ejecución y catálogo opcional de ensemble.
 * ANTERIOR: legacy/visor/app_v1.2.0.js
 */
let TERRITORIES = {
  aragon: { label: "Aragón", districts: 67, file: "data/aragon/distritos.geojson", source: "data/aragon/distritos.geojson", publicationStatus: "BLOCKED", metadata: "data/aragon/metadata.json" },
  castilla_y_leon: { label: "Castilla y León", districts: 82, file: "data/castilla_y_leon/distritos.geojson", source: "data/castilla_y_leon/distritos.geojson", publicationStatus: "BLOCKED", metadata: "data/castilla_y_leon/metadata.json" }
};
let ENSEMBLE_SUMMARY = null;
let ENSEMBLE_INDEX = null;
let CURRENT_VARIANTS = [];
let CURRENT_SPEC = null;

const palette=['#264653','#2a9d8f','#e9c46a','#f4a261','#e76f51','#457b9d','#8d5a97','#588157','#bc6c25','#6d597a','#1d3557','#e63946','#457b9d','#a8dadc','#ffb703','#219ebc','#8338ec','#3a86ff','#fb5607','#06d6a0'];
const map = new maplibregl.Map({
  container: "map", style: {version:8,sources:{osm:{type:"raster",tiles:["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],tileSize:256,attribution:"© OpenStreetMap contributors"}},layers:[{id:"osm",type:"raster",source:"osm"}]},
  center: [-2.5, 41.5], zoom: 5.2
});
map.addControl(new maplibregl.NavigationControl(), "top-right");

const status=document.querySelector("#status");
const summary=document.querySelector("#summary");
const detail=document.querySelector("#detail");
const sourceLink=document.querySelector("#source-link");
const ensembleLink=document.querySelector("#ensemble-link");
const territorySelect=document.querySelector("#territory-select");
const resultSelect=document.querySelector("#result-select");
const scalar=(props,names)=>{for(const n of names){if(props[n]!==undefined&&props[n]!==null&&props[n]!=="")return props[n]}return null};
const formatNumber=(v)=>typeof v==="number"?new Intl.NumberFormat("es-ES",{maximumFractionDigits:2}).format(v):String(v??"—");
const pct=v=>v===null||v===undefined||Number.isNaN(Number(v))?"—":(Number(v)*100).toLocaleString("es-ES",{maximumFractionDigits:2})+" %";
const esc=v=>String(v??"").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));

function utmToWgs84(x,y){
  const a=6378137, e=0.081819191, e1=(1-Math.sqrt(1-e*e))/(1+Math.sqrt(1-e*e)), k0=.9996, x1=x-500000, M=y/k0, mu=M/(a*(1-e*e/4-3*Math.pow(e,4)/64-5*Math.pow(e,6)/256));
  const phi1=mu+(3*e1/2-27*Math.pow(e1,3)/32)*Math.sin(2*mu)+(21*e1*e1/16-55*Math.pow(e1,4)/32)*Math.sin(4*mu)+(151*Math.pow(e1,3)/96)*Math.sin(6*mu);
  const ep=e*e/(1-e*e), C1=ep*Math.cos(phi1)**2, T1=Math.tan(phi1)**2, N1=a/Math.sqrt(1-e*e*Math.sin(phi1)**2), R1=a*(1-e*e)/Math.pow(1-e*e*Math.sin(phi1)**2,1.5), D=x1/(N1*k0);
  const lat=phi1-(N1*Math.tan(phi1)/R1)*(D*D/2-(5+3*T1+10*C1-4*C1*C1-9*ep)*D**4/24+(61+90*T1+298*C1+45*T1*T1-252*ep-3*C1*C1)*D**6/720);
  const lon=(-3*Math.PI/180)+(D-(1+2*T1+C1)*D**3/6+(5-2*C1+28*T1-3*C1*C1+8*ep+24*T1*T1)*D**5/120)/Math.cos(phi1);
  return [lon*180/Math.PI,lat*180/Math.PI];
}
function transformCoordinates(value){
  if(typeof value[0]==="number") return Math.abs(value[0])<=180&&Math.abs(value[1])<=90?value:utmToWgs84(value[0],value[1]);
  return value.map(transformCoordinates);
}
function normalize(data){return {...data,features:data.features.map(f=>({...f,geometry:{...f.geometry,coordinates:transformCoordinates(f.geometry.coordinates)}}))};}
function boundsFor(data){const b=new maplibregl.LngLatBounds();data.features.forEach(f=>{const visit=c=>typeof c[0]==="number"?b.extend(c):c.forEach(visit);visit(f.geometry.coordinates)});return b;}
async function optionalJson(path){try{const r=await fetch(path,{cache:"no-cache"});return r.ok?await r.json():null}catch(_){return null}}

function colorExpression(field, values){
  const exp=['match',['to-string',['get',field]]];
  values.forEach((value,index)=>exp.push(String(value),palette[index%palette.length]));
  exp.push('#8b95a5');
  return exp;
}
function metric(metrics,path){let cur=metrics;for(const key of path){if(cur===null||cur===undefined)return null;cur=cur[key]}return cur}
function stateClass(value){const text=String(value||'').toUpperCase();if(text.includes('PASS')&&!text.includes('BLOCK'))return 'state-pass';if(text.includes('BLOCK')||text.includes('FAIL'))return 'state-block';return 'state-warn'}
function dl(rows){return `<dl>${rows.map(([k,v,cls])=>`<dt>${esc(k)}</dt><dd${cls?` class="${cls}"`:''}>${v}</dd>`).join('')}</dl>`}

function districtHtml(props,spec){
  const id=scalar(props,[spec.districtField,"district_id","DISTRICT_ID","id"]);
  const districtPop=scalar(props,["district_pop","population","POPULATION"]);
  const target=scalar(props,["target_population","target","TARGET"]);
  const dev=scalar(props,["relative_deviation","population_target_ratio"]);
  const section=scalar(props,["CUSEC_KEY","CUSEC"]);
  const municipality=scalar(props,["NMUN","municipality_names","MUNICIPALITIES"]);
  const sectionPop=scalar(props,["POP_2025","POP"]);
  const rows=[["Distrito",esc(formatNumber(id))]];
  if(districtPop!==null) rows.push(["Población distrito",esc(formatNumber(districtPop))]);
  if(target!==null) rows.push(["Objetivo",esc(formatNumber(target))]);
  if(dev!==null) rows.push(["Desviación",esc(pct(dev))]);
  if(section!==null) rows.push(["Sección",esc(section)]);
  if(municipality!==null) rows.push(["Municipio",esc(municipality)]);
  if(sectionPop!==null&&districtPop===null) rows.push(["Población sección",esc(formatNumber(sectionPop))]);
  return `<p class="district-title">${spec.kind==='ensemble'?'Alternativa':'Resultado'} · distrito ${esc(formatNumber(id))}</p>${dl(rows)}`;
}

function baselineVariant(key,spec){return {id:'baseline',label:'Resultado canónico M01–M06',kind:'baseline',territory:key,file:spec.file,source:spec.source,metadata:spec.metadata,districts:spec.districts,districtField:'district_id',publicationStatus:spec.publicationStatus};}
function variantsForTerritory(key){
  const spec=TERRITORIES[key];
  const variants=[baselineVariant(key,spec)];
  if(ENSEMBLE_SUMMARY&&ENSEMBLE_SUMMARY.territory_id===key){
    for(const c of ENSEMBLE_SUMMARY.candidates||[]){
      if(!c.asset) continue;
      variants.push({
        id:c.candidate_id,
        label:`${c.candidate_id} · ${c.profile}`,
        kind:'ensemble',
        territory:key,
        file:`ensemble/${c.asset}`,
        source:`ensemble/${c.asset}`,
        metadata:null,
        districts:spec.districts,
        districtField:(c.fields&&c.fields.district)||'district_id',
        publicationStatus:'BLOCKED',
        candidate:c
      });
    }
  }
  return variants;
}
function populateResults(key,preferred){
  CURRENT_VARIANTS=variantsForTerritory(key);
  resultSelect.replaceChildren(...CURRENT_VARIANTS.map(v=>new Option(v.label,v.id)));
  resultSelect.value=CURRENT_VARIANTS.some(v=>v.id===preferred)?preferred:CURRENT_VARIANTS[0].id;
}

async function loadVariant(){
  const territory=territorySelect.value;
  const spec=CURRENT_VARIANTS.find(v=>v.id===resultSelect.value)||CURRENT_VARIANTS[0];
  CURRENT_SPEC=spec;
  const territorySpec=TERRITORIES[territory];
  status.textContent=`Cargando ${territorySpec.label} · ${spec.label}…`;
  detail.textContent="Pulsa el mapa para ver su ficha.";
  summary.hidden=true;
  ["district-fill","district-line","district-hit"].forEach(id=>map.getLayer(id)&&map.removeLayer(id));
  if(map.getSource("districts"))map.removeSource("districts");
  try{
    const response=await fetch(spec.file,{cache:"no-cache"});
    if(!response.ok)throw new Error(`HTTP ${response.status}`);
    const raw=await response.json();
    if(raw.type!=="FeatureCollection"||!Array.isArray(raw.features)||raw.features.length===0)throw new Error("GeoJSON vacío o inválido.");
    const districtValues=[...new Set(raw.features.map(f=>String((f.properties||{})[spec.districtField])).filter(v=>v!=="undefined"&&v!=="null"))];
    if(districtValues.length!==spec.districts)throw new Error(`El resultado contiene ${districtValues.length} distritos; se esperaban ${spec.districts}.`);
    const data=normalize(raw);
    map.addSource("districts",{type:"geojson",data});
    map.addLayer({id:"district-fill",type:"fill",source:"districts",paint:{"fill-color":colorExpression(spec.districtField,districtValues),"fill-opacity":.58}});
    map.addLayer({id:"district-line",type:"line",source:"districts",paint:{"line-color":spec.kind==='baseline'?'#ffffff':'rgba(255,255,255,0.18)',"line-width":spec.kind==='baseline'?1.2:.25}});
    map.addLayer({id:"district-hit",type:"fill",source:"districts",paint:{"fill-color":"#000000","fill-opacity":0}});
    map.fitBounds(boundsFor(data),{padding:36,maxZoom:8,duration:500});

    let metadata=spec.metadata?await optionalJson(spec.metadata):null;
    let rows=[["Territorio",esc(territorySpec.label)],["Resultado",esc(spec.label)],["Distritos",esc(spec.districts)]];
    if(spec.kind==='baseline'){
      const technical=metadata?.technical_status||'PASS técnico';
      const audit=metadata?.geometric_audit||null;
      rows.push(["Estado M01–M06",esc(technical),stateClass(technical)]);
      if(audit){
        rows.push(["Auditoría geométrica",esc(audit.decision),stateClass(audit.decision)]);
        rows.push(["Conexos geométricos",esc(`${audit.connected_districts}/${audit.district_count}`),audit.decision==='PASS'?'state-pass':'state-block']);
      }
      if(metadata?.source_run_id) rows.push(["Run",esc(metadata.source_run_id)]);
      if(metadata?.max_population_deviation!==undefined) rows.push(["Desviación máx.",esc(pct(metadata.max_population_deviation))]);
    }else{
      const c=spec.candidate||{};const m=c.metrics||{};
      rows.push(["Perfil",esc(c.profile||'—')],["Semilla",esc(c.seed??'—')],["Desviación máx.",esc(pct(metric(m,['population','max_deviation'])))],["PP mediana",esc(formatNumber(metric(m,['shape','polsby_popper_median'])))],["Retención comarca",esc(pct(metric(m,['comarca','retention_ratio'])))],["Estado",'Candidato válido', 'state-pass']);
    }
    rows.push(["Publicabilidad",esc(spec.publicationStatus),stateClass(spec.publicationStatus)]);
    summary.innerHTML=dl(rows);summary.hidden=false;
    const auditText=metadata?.geometric_audit?` · geometría ${metadata.geometric_audit.connected_districts}/${metadata.geometric_audit.district_count}`:'';
    status.textContent=`${territorySpec.label} · ${spec.label} cargado${auditText}.`;
    sourceLink.href=spec.source;sourceLink.textContent=spec.kind==='baseline'?`Abrir GeoJSON canónico de ${territorySpec.label}`:`Abrir GeoJSON de ${spec.id}`;
    ensembleLink.hidden=!ENSEMBLE_INDEX?.gallery_path;
    if(!ensembleLink.hidden) ensembleLink.href=ENSEMBLE_INDEX.gallery_path;
  }catch(error){status.textContent=`No se pudo cargar ${territorySpec.label} · ${spec.label}: ${error.message}`;console.error(error)}
}

async function bootstrap(){
  try {
    const response=await fetch("data/public-products.json",{cache:"no-cache"});
    if(!response.ok) throw new Error("registro HTTP "+response.status);
    const registry=await response.json();
    TERRITORIES=Object.fromEntries(registry.products.map(product=>[product.id,{label:product.label,districts:product.expected_districts,file:product.viewer_path,source:product.viewer_path,publicationStatus:product.publication_status||"BLOCKED",metadata:`data/${product.id}/metadata.json`}]))
  } catch(error) { console.warn("Registro público no disponible; se usa el catálogo incorporado.",error); }
  ENSEMBLE_INDEX=await optionalJson("data/ensemble-index.json");
  if(ENSEMBLE_INDEX?.summary_path) ENSEMBLE_SUMMARY=await optionalJson(ENSEMBLE_INDEX.summary_path);
  territorySelect.replaceChildren(...Object.entries(TERRITORIES).map(([id,product])=>new Option(product.label+" · "+product.districts+" distritos",id)));
  const first=Object.keys(TERRITORIES)[0];territorySelect.value=first;populateResults(first);await loadVariant();
  territorySelect.addEventListener("change",async e=>{populateResults(e.target.value);await loadVariant();});
  resultSelect.addEventListener("change",loadVariant);
}

function wireInteractions(){
  map.on("click","district-hit",e=>{if(!e.features?.length||!CURRENT_SPEC)return;const props=e.features[0].properties||{};const html=districtHtml(props,CURRENT_SPEC);detail.innerHTML=html;new maplibregl.Popup().setLngLat(e.lngLat).setHTML(html).addTo(map)});
  map.on("mouseenter","district-hit",()=>map.getCanvas().style.cursor="pointer");
  map.on("mouseleave","district-hit",()=>map.getCanvas().style.cursor="");
}
map.on("load",async()=>{await bootstrap();wireInteractions();});
