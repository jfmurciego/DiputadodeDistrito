/* Proyecto: Diputado de Distrito · Versión 1.0.0 · visor Nacional (T-84, D-16)
 * Vista Nacional: barra temporal, capas y feature-state de MapLibre. Solo muestra lo publicado en datos/
 * (datos_abiertos/INDEX.json). No inventa histórico: las elecciones y capas sin datos salen desactivadas.
 * Teselas PMTiles: pendiente (hoy GeoJSON por provincia, cargado en paralelo). */
"use strict";
const DATOS=new URLSearchParams(location.search).get("datos")||"../datos/";
const ELECCIONES=[
 {id:"2011",label:"2011",ok:false,motivo:"pendiente de T-83/T-85"},
 {id:"2015",label:"2015",ok:false,motivo:"pendiente de T-83/T-85"},
 {id:"2016",label:"2016",ok:false,motivo:"pendiente de T-83/T-85"},
 {id:"2019",label:"2019",ok:false,motivo:"pendiente de T-83/T-85"},
 {id:"2023",label:"2023",ok:true}];
const CAPAS=[
 {id:"ganador-distrito",label:"Ganador por distrito",ok:true},
 {id:"ganador-seccion",label:"Ganador por sección",ok:false,motivo:"sin datos por sección publicados"},
 {id:"rotacion",label:"Rotación",ok:false,motivo:"requiere dos elecciones (T-83/T-85)"},
 {id:"participacion",label:"Participación",ok:false,motivo:"sin censo publicado"}];
const FAMILIAS=[
 {re:/^PP$/,name:"PP",color:"#1d84ce"},
 {re:/PSOE|^PSC|^PSE|^PSN|^PSIB/,name:"PSOE y federados",color:"#d62728"},
 {re:/VOX/i,name:"VOX",color:"#4c9a2a"},
 {re:/PNV/,name:"EAJ-PNV",color:"#2b8a3e"},
 {re:/Bildu/,name:"EH Bildu",color:"#9acd32"},
 {re:/SUMAR|PODEMOS|IU/i,name:"Sumar y afines",color:"#9b59b6"}];
const OTRO="#7f7f7f";
const familia=g=>FAMILIAS.find(f=>f.re.test(g))||{name:"Otros",color:OTRO};
const $=s=>document.querySelector(s),fmt=n=>new Intl.NumberFormat("es-ES",{maximumFractionDigits:2}).format(n);
const status=$("#status"),detail=$("#detail"),legend=$("#legend");
let capa="ganador-distrito",eleccion="2023",hover=null,selected=null;
function botones(cont,items,activo,onclick){
 cont.replaceChildren();
 for(const it of items){
  const b=document.createElement("button");b.type="button";b.textContent=it.label;
  b.setAttribute("aria-pressed",String(it.id===activo));
  if(!it.ok){b.disabled=true;b.title=it.motivo}
  b.onclick=()=>onclick(it.id);cont.appendChild(b);
 }
}
function pintaControles(){
 botones($("#timebar"),ELECCIONES,eleccion,id=>{eleccion=id;pintaControles()});
 botones($("#layers"),CAPAS,capa,id=>{capa=id;pintaControles()});
}
function parseCsv(t){return t.trim().split(/\r?\n/).slice(1).map(l=>{const c=l.split(",");
 return{distrito:+c[0],poblacion:+c[1],votos:+c[2],ganador:c[3],votosGanador:+c[4],pct:+c[5]}})}
const map=new maplibregl.Map({container:"map",center:[-3.7,40.2],zoom:5.2,style:{version:8,
 sources:{osm:{type:"raster",tiles:["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],tileSize:256,attribution:"© OpenStreetMap contributors"}},
 layers:[{id:"osm",type:"raster",source:"osm"}]}});
map.addControl(new maplibregl.NavigationControl(),"top-right");
async function cargaProvincia(t,info){
 const [g,c]=await Promise.all([fetch(DATOS+info.geojson.ruta).then(r=>{if(!r.ok)throw Error(t);return r.json()}),
  fetch(DATOS+info.resultados.ruta).then(r=>{if(!r.ok)throw Error(t);return r.text()})]);
 const res=new Map(parseCsv(c).map(r=>[r.distrito,r]));
 return g.features.map(f=>{const id=f.properties.district_id,r=res.get(id)||{};
  return{type:"Feature",id:undefined,geometry:f.geometry,properties:{uid:t+"-"+id,provincia:info.provincia,distrito:id,
   poblacion:f.properties.district_pop,ganador:r.ganador||"",votos:r.votos,votosGanador:r.votosGanador,pct:r.pct,
   familia:familia(r.ganador||"").name,color:familia(r.ganador||"").color}}});
}
function pintaLeyenda(){
 legend.replaceChildren();const h=document.createElement("h2");h.textContent="Ganador por distrito, "+eleccion;legend.appendChild(h);
 for(const f of [...FAMILIAS,{name:"Otros",color:OTRO}]){const d=document.createElement("div");d.className="legend-item";
  const s=document.createElement("span");s.className="swatch";s.style.backgroundColor=f.color;
  const t=document.createElement("span");t.textContent=f.name;d.append(s,t);legend.appendChild(d)}
}
function ficha(p){
 detail.replaceChildren();const dl=document.createElement("dl");
 for(const [k,v] of [["Provincia",p.provincia],["Distrito",p.distrito],["Población",fmt(p.poblacion)],["Ganador",p.ganador||"—"],
  ["Votos del ganador",fmt(p.votosGanador)],["Porcentaje",fmt(p.pct)+" %"],["Votos totales",fmt(p.votos)]]){
  const a=document.createElement("dt"),b=document.createElement("dd");a.textContent=k;b.textContent=v;dl.append(a,b)}
 detail.appendChild(dl);
}
function estado(uid,key,val){if(uid!==null)map.setFeatureState({source:"distritos",id:uid},{[key]:val})}
map.on("load",async()=>{
 try{
  const idx=await fetch(DATOS+"INDEX.json").then(r=>{if(!r.ok)throw Error("INDEX.json: HTTP "+r.status);return r.json()});
  const ent=Object.entries(idx.territorios);let hechos=0;
  const listas=await Promise.all(ent.map(([t,i])=>cargaProvincia(t,i).then(x=>{status.textContent="Cargando "+(++hechos)+"/"+ent.length+"…";return x})));
  const feats=listas.flat();
  map.addSource("distritos",{type:"geojson",promoteId:"uid",data:{type:"FeatureCollection",features:feats}});
  map.addLayer({id:"d-fill",type:"fill",source:"distritos",paint:{"fill-color":["get","color"],
   "fill-opacity":["case",["boolean",["feature-state","sel"],false],0.9,["boolean",["feature-state","hover"],false],0.8,0.6]}});
  map.addLayer({id:"d-line",type:"line",source:"distritos",paint:{"line-color":"#273449","line-width":["case",["boolean",["feature-state","sel"],false],3,0.6]}});
  pintaLeyenda();
  status.textContent=feats.length+" distritos en "+ent.length+" provincias · generales 2023";
  document.body.dataset.listo="1";
 }catch(e){status.textContent="No se pudieron cargar los datos: "+e.message;console.error(e)}
});
map.on("mousemove","d-fill",e=>{const u=e.features[0].properties.uid;map.getCanvas().style.cursor="pointer";
 if(u!==hover){estado(hover,"hover",false);hover=u;estado(hover,"hover",true)}});
map.on("mouseleave","d-fill",()=>{estado(hover,"hover",false);hover=null;map.getCanvas().style.cursor=""});
map.on("click","d-fill",e=>{const p=e.features[0].properties;estado(selected,"sel",false);selected=p.uid;estado(selected,"sel",true);ficha(p)});
pintaControles();
