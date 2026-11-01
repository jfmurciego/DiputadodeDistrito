/*
 * Proyecto: Diputado de Distrito
 * Versión: 1.1.1 | Nombre: visor analítico nacional (T-05: textos públicos «nacional»)
 * Fecha: 2026-10-27 | Alcance: pilotos no certificados de León y Cáceres
 * Estado: candidato no productivo
 * Cambios/motivo: validar y mostrar SHA del candidato y run de materialización.
 * Anterior: legacy/visor/congreso_pre_t05_20261101/congreso.js
 */
"use strict";
const palette=["#2a6fbd","#e88c40","#209779","#aa69bd"];
const provinces={
 "24":{name:"León",k:4,sections:444,population:448030,
    source:"INE 2025 / N08; León 444 CUSEC; revisión geométrica 2026-10-26",
    limitations:"Ningún municipio dividido. Dos pequeños solapamientos originales entre secciones dentro de LEON-02; no constituyen aristas. Falta acreditación externa CNIG/IGN."},
 "10":{name:"Cáceres",k:3,sections:411,population:388190,
    source:"INE 2025 / N08; alternativa degree_asc; revisión geométrica 2026-10-26",
    limitations:"Municipio 10037 (Cáceres) dividido. La necesidad está justificada solo con las demás asignaciones fijas, no globalmente. Falta acreditación externa CNIG/IGN."}
};
const map=new maplibregl.Map({container:"map",center:[-5.8,41.8],zoom:6.6,style:{
version:8,sources:{osm:{type:"raster",tiles:["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],tileSize:256,attribution:"© OpenStreetMap contributors"}},
layers:[{id:"osm",type:"raster",source:"osm"}]}});
map.addControl(new maplibregl.NavigationControl(),"top-right");
const status=document.querySelector("#status"),detail=document.querySelector("#detail"),
  list=document.querySelector("#district-list"),select=document.querySelector("#province-select"),
  limitations=document.querySelector("#limitations"),sourceDetails=document.querySelector("#source-details");
const fmt=n=>new Intl.NumberFormat("es-ES",{maximumFractionDigits:2}).format(n);
let loadSerial=0;
const initial=globalThis.DDD_CONGRESO_GEOJSON||{};
const embeds=(initial?.type==="FeatureCollection")?{"24":initial}:initial;
function removeLayers(){
 for(const id of ["split-municipal-line","nacional-border","nacional-fill"]){if(map.getLayer(id))map.removeLayer(id)}
 for(const id of ["split-municipality","nacional"]){if(map.getSource(id))map.removeSource(id)}
}
function validate(data,cpro){
 const spec=provinces[cpro];
 if(data?.type!=="FeatureCollection"||!Array.isArray(data.features)||data.features.length!==spec.k)throw Error("Cardinalidad de distritos inválida");
 const ids=new Set(),bound=new maplibregl.LngLatBounds(),rows=[];let sections=0,population=0;
 function visit(x){
   if(typeof x?.[0]==="number"){if(x.length<2||!Number.isFinite(x[0])||!Number.isFinite(x[1])||Math.abs(x[0])>180||Math.abs(x[1])>90)throw Error("Coordenadas no válidas");bound.extend(x)}
   else if(Array.isArray(x))x.forEach(visit);else throw Error("Estructura geométrica no válida")
 }
 for(const f of data.features){
   const p=f.properties||{};
   if(typeof p.district_id!=="string"||ids.has(p.district_id)||p.cpro!==cpro||
     p.pilot_only!==true||p.certification_status!=="NOT_CERTIFIED"||p.generation_authorized!==false||
     typeof p.candidate_file_sha256!=="string"||!/^[0-9a-f]{64}$/.test(p.candidate_file_sha256)||
     typeof p.execution_id!=="string"||!/^[0-9]+$/.test(p.execution_id)||
     !Number.isInteger(p.population)||p.population<0||!Number.isInteger(p.cusec_count)||p.cusec_count<1)
     throw Error("Identidad o puerta de candidato inválida");
   if(!["Polygon","MultiPolygon"].includes(f.geometry?.type))throw Error("Geometría no poligonal");
   ids.add(p.district_id);population+=p.population;sections+=p.cusec_count;
   visit(f.geometry.coordinates);rows.push(p);
 }
 if(sections!==spec.sections||population!==spec.population)throw Error("Población o cobertura provincial no concilian");
 return {rows:rows.sort((a,b)=>a.district_id.localeCompare(b.district_id)),bound};
}
function render(data,cpro){
 const {rows,bound}=validate(data,cpro);
 const provenance=rows[0];
 if(rows.some(p=>p.candidate_file_sha256!==provenance.candidate_file_sha256||p.execution_id!==provenance.execution_id||p.witness_sha256!==provenance.witness_sha256))
   throw Error("Trazabilidad inconsistente entre distritos");
 removeLayers();
 map.addSource("nacional",{type:"geojson",data});
 const match=["match",["get","district_id"]];rows.forEach((p,i)=>match.push(p.district_id,palette[i]));match.push("#888");
 map.addLayer({id:"nacional-fill",type:"fill",source:"nacional",paint:{"fill-color":match,"fill-opacity":0.6}});
 map.addLayer({id:"nacional-border",type:"line",source:"nacional",paint:{"line-color":"#273449","line-width":1.5}});
 map.fitBounds(bound,{padding:40,maxZoom:10,duration:300});
 list.replaceChildren();
 const target=provinces[cpro].population/provinces[cpro].k;
 for(const [i,p] of rows.entries()){
   const div=document.createElement("div");div.className="legend-item";
   const swatch=document.createElement("span");swatch.className="swatch";swatch.style.backgroundColor=palette[i];
   const text=document.createElement("span");
   const deviation=100*(p.population/target-1);
   text.textContent=p.district_id+" · "+fmt(p.population)+" hab. · "+fmt(p.cusec_count)+" CUSEC ("+(deviation>=0?"+":"")+fmt(deviation)+" %)";
   div.append(swatch,text);list.appendChild(div);
 }
 status.textContent=provinces[cpro].name+": "+rows.length+" distritos analíticos · "+fmt(provinces[cpro].population)+" habitantes";
 limitations.textContent=provinces[cpro].limitations;
 sourceDetails.textContent=provinces[cpro].source+
   "; candidato SHA-256 "+provenance.candidate_file_sha256+
   "; ejecución GitHub Actions #"+provenance.execution_id+
   "; testigo SHA-256 "+provenance.witness_sha256+
   "; certificación: NOT_PERFORMED";
 detail.textContent="Pulsa un distrito para ver su ficha.";
}
async function show(cpro){
 const serial=++loadSerial;
 if(!provinces[cpro])return;
 status.textContent="Cargando "+provinces[cpro].name+"…";
 try{
   let data=embeds[cpro];
   if(!data){
     const response=await fetch("data/"+cpro+".geojson",{cache:"no-cache"});
     if(!response.ok)throw Error("cartografía no disponible (HTTP "+response.status+")");
     data=await response.json();
   }
   if(serial!==loadSerial)return;
   if(!map.isStyleLoaded())await new Promise(resolve=>map.once("load",resolve));
   if(serial!==loadSerial)return;
   render(data,cpro);
   if(cpro==="10"){
     try{
       const split=embeds["10-split"]||await (async()=>{const r=await fetch("data/10-municipios-divididos.geojson",{cache:"no-cache"});return r.ok?await r.json():null})();
       if(serial===loadSerial&&split?.type==="FeatureCollection"&&split.features?.length>0){
         map.addSource("split-municipality",{type:"geojson",data:split});
         map.addLayer({id:"split-municipal-line",type:"line",source:"split-municipality",paint:{"line-color":"#b42318","line-width":3,"line-dasharray":[2,1]}});
       }
     }catch(_){/* no inventar una delimitación si la capa no está disponible */}
   }
 }catch(err){if(serial===loadSerial){removeLayers();list.textContent="No se pudo cargar la cartografía";status.textContent="Error: "+err.message}}
}
map.on("click","nacional-fill",event=>{
 const p=event.features?.[0]?.properties;if(!p)return;
 const spec=provinces[select.value],target=spec.population/spec.k,dev=100*(Number(p.population)/target-1);
 detail.textContent=p.district_id+" — "+fmt(Number(p.population))+" habitantes; "+
 fmt(Number(p.cusec_count))+" CUSEC; desviación "+(dev>=0?"+":"")+fmt(dev)+" % del objetivo. Producto no certificado.";
});
map.on("mouseenter","nacional-fill",()=>map.getCanvas().style.cursor="pointer");
map.on("mouseleave","nacional-fill",()=>map.getCanvas().style.cursor="");
select.addEventListener("change",cpro=>show(select.value));
document.querySelector("#geojson-file").addEventListener("change",async event=>{
 const file=event.target.files?.[0];if(!file)return;
 try{
  const data=JSON.parse(await file.text());
  if(!map.isStyleLoaded())await new Promise(resolve=>map.once("load",resolve));
  render(data,select.value);
 }catch(err){status.textContent="Archivo rechazado: "+err.message}
});
if(map.isStyleLoaded())show(select.value);else map.once("load",()=>show(select.value));
