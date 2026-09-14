/* PROYECTO: Diputado de Distrito
 * VERSIÓN: 1.2.0
 * NOMBRE: visor técnico con estado de publicabilidad
 * QUÉ HACE: dibuja productos canónicos declarados sin ejecutar el motor.
 * CAMBIO: distingue certificación técnica de autorización de publicación.
 * ANTERIOR: legacy/visor/app_v1.1.0.js
 */
let TERRITORIES = {
  aragon: { label: "Aragón", districts: 67, file: "data/aragon/distritos.geojson", source: "../resultados/finales/aragon/distritos.geojson", publicationStatus: "BLOCKED" },
  castilla_y_leon: { label: "Castilla y León", districts: 82, file: "data/castilla_y_leon/distritos.geojson", source: "../resultados/finales/castilla_y_leon/distritos.geojson", publicationStatus: "BLOCKED" }
};
const map = new maplibregl.Map({
  container: "map", style: {version:8,sources:{osm:{type:"raster",tiles:["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],tileSize:256,attribution:"© OpenStreetMap contributors"}},layers:[{id:"osm",type:"raster",source:"osm"}]},
  center: [-2.5, 41.5], zoom: 5.2
});
map.addControl(new maplibregl.NavigationControl(), "top-right");
const status=document.querySelector("#status"), summary=document.querySelector("#summary"), detail=document.querySelector("#detail"), sourceLink=document.querySelector("#source-link");
const scalar=(props,names)=>{for(const n of names){if(props[n]!==undefined&&props[n]!==null&&props[n]!=="")return props[n]}return null};
const formatNumber=(v)=>typeof v==="number"?new Intl.NumberFormat("es-ES",{maximumFractionDigits:2}).format(v):String(v??"—");
function wgs84(coords){
  if(typeof coords[0]==="number"){
    const [x,y]=coords;
    if(Math.abs(x)<=180&&Math.abs(y)<=90)return coords;
    const lon=(x-500000)/((6378137*Math.PI/180)*Math.cos(40*Math.PI/180))-3;
    const lat=(y/110574)+0; // fallback is replaced below by proj4-free approximation
    return [lon,lat];
  }
  return coords.map(wgs84);
}
function utmToWgs84(x,y){
  // EPSG:25830 -> WGS84, Transverse Mercator inverse. Precision is sufficient for visualization.
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
function districtHtml(props){
  const id=scalar(props,["district_id","DISTRICT_ID","id"]), pop=scalar(props,["population","district_pop","POPULATION"]), target=scalar(props,["target_population","target","TARGET"]), dev=scalar(props,["relative_deviation","population_target_ratio"]);
  const mun=scalar(props,["municipalities","municipality_names","MUNICIPALITIES"]);
  return `<p class="district-title">Distrito ${formatNumber(id)}</p><dl class="detail-list"><dt>Población</dt><dd>${formatNumber(pop)}</dd><dt>Objetivo</dt><dd>${formatNumber(target)}</dd><dt>Desviación</dt><dd>${dev===null?"—":(Number(dev)*100).toLocaleString("es-ES",{maximumFractionDigits:2})+" %"}</dd><dt>Municipios</dt><dd>${formatNumber(mun)}</dd></dl>`;
}
async function loadTerritory(key){
  const spec=TERRITORIES[key]; status.textContent=`Cargando ${spec.label}…`; detail.textContent="Pulsa un distrito para ver su ficha."; summary.hidden=true;
  ["district-fill","district-line","district-hit"].forEach(id=>map.getLayer(id)&&map.removeLayer(id)); map.getSource("districts")&&map.removeSource("districts");
  try{
    const response=await fetch(spec.file,{cache:"no-cache"}); if(!response.ok)throw new Error(`HTTP ${response.status}`);
    const data=normalize(await response.json()); if(data.type!=="FeatureCollection"||data.features.length!==spec.districts)throw new Error("GeoJSON no coincide con el contrato público.");
    map.addSource("districts",{type:"geojson",data});
    map.addLayer({id:"district-fill",type:"fill",source:"districts",paint:{"fill-color":"#0b5cab","fill-opacity":.38}});
    map.addLayer({id:"district-line",type:"line",source:"districts",paint:{"line-color":"#ffffff","line-width":1.1}});
    map.addLayer({id:"district-hit",type:"fill",source:"districts",paint:{"fill-color":"#000000","fill-opacity":0}});
    map.on("click","district-hit",e=>{const props=e.features[0].properties||{};detail.innerHTML=districtHtml(props);new maplibregl.Popup().setLngLat(e.lngLat).setHTML(districtHtml(props)).addTo(map)});
    map.on("mouseenter","district-hit",()=>map.getCanvas().style.cursor="pointer");map.on("mouseleave","district-hit",()=>map.getCanvas().style.cursor="");
    map.fitBounds(boundsFor(data),{padding:36,maxZoom:8,duration:500});
    summary.innerHTML=`<dl><dt>Territorio</dt><dd>${spec.label}</dd><dt>Distritos</dt><dd>${data.features.length}</dd><dt>Estado técnico</dt><dd>PASS</dd><dt>Publicabilidad</dt><dd>${spec.publicationStatus}</dd></dl>`;summary.hidden=false;status.textContent=`${spec.label}: vista técnica cargada; publicación bloqueada.`;
    sourceLink.href=spec.source;sourceLink.textContent=`GeoJSON canónico de ${spec.label}`;
  }catch(error){status.textContent=`No se pudo cargar ${spec.label}: ${error.message}`;console.error(error)}
}
async function bootstrap(){
  const select=document.querySelector("#territory-select");
  try {
    const response=await fetch("data/public-products.json",{cache:"no-cache"}); if(!response.ok) throw new Error("registro HTTP "+response.status);
    const registry=await response.json();
    TERRITORIES=Object.fromEntries(registry.products.map(product=>[product.id,{label:product.label,districts:product.expected_districts,file:product.viewer_path,source:"../"+product.source_path,publicationStatus:product.publication_status||"BLOCKED"}]));
    select.replaceChildren(...Object.entries(TERRITORIES).map(([id,product])=>new Option(product.label+" · "+product.districts+" distritos",id)));
  } catch(error) { console.warn("Registro público no disponible; se usa el catálogo incorporado.",error); }
  const first=Object.keys(TERRITORIES)[0]; select.value=first; await loadTerritory(first);
  select.addEventListener("change",e=>loadTerritory(e.target.value));
}
map.on("load",bootstrap);
