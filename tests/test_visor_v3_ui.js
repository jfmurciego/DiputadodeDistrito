/* PROYECTO: Diputado de Distrito
 * CLASE: prueba de interacción V3
 * VERSIÓN: 1.2.0 · FECHA: 2026-11-14 · ESTADO: candidato
 * ANTERIOR: legacy/tests/test_visor_v3_ui_v1.1.0_20261114.js
 * 1.2.0 (T-295): accesibilidad WCAG 2.1 AA (marcado, CSS, contraste, anuncio de selección y tabla alternativa).
 * 1.1.0 (T-300): casos del panel «De dónde sale este mapa» (catálogo de procedencia real, sin catálogo, sin producto).
 * CAMBIOS: prueba la UI con un navegador simulado y datos territoriales reales. */
"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const ROOT=path.resolve(__dirname,"..");
const source=fs.readFileSync(path.join(ROOT,"visor/v3/v3.js"),"utf8");
const provincias=JSON.parse(fs.readFileSync(path.join(ROOT,"visor/v2/datos/provincias.json"),"utf8"));
const comunidades=JSON.parse(fs.readFileSync(path.join(ROOT,"visor/v2/datos/comunidades.json"),"utf8"));
const index=JSON.parse(fs.readFileSync(path.join(ROOT,"datos_abiertos/INDEX.json"),"utf8"));
const catalogo=JSON.parse(fs.readFileSync(path.join(ROOT,"orchestracion/catalogo_procedencia.json"),"utf8"));
const madrid=provincias.features.find(f=>f.properties.cod==="28");
const madridEntry=Object.entries(index.territorios).find(([id,v])=>v.provincia==="Madrid");
assert.ok(madrid&&madridEntry);
const first=madridEntry[1].distritos[0];
const districtFC={type:"FeatureCollection",features:[{type:"Feature",geometry:madrid.geometry,
  properties:{distrito:first.distrito,district_pop:first.poblacion,relative_deviation:0.02,section_count:7}}]};
const sectionFC={type:"FeatureCollection",features:[{type:"Feature",geometry:madrid.geometry,
  properties:{s:"2807912003",m:"Madrid",p:1622,d:first.distrito,t:"congreso_madrid"}}]};
const fixtures={
  "../v2/datos/provincias.json":provincias,
  "../v2/datos/comunidades.json":comunidades,
  "../datos/INDEX.json":index,
  "../v2/datos/secciones/INDEX.json":{provincias:{"28":{}}},
  "../v2/datos/secciones/28.geojson":sectionFC,
  "../v2/datos/territorial.json":{provincias:{}},
  "../data/viewer-results.json":{results:[{kind:"canonical_m06",territory_id:"madrid",
    publication_status:"PUBLICABLE",viewer_path:"data/results/madrid/1/m06.geojson",
    run_id:"1",label:"M06 Madrid",certification_status:"CERTIFIED"}]},
  "../data/results/madrid/1/m06.geojson":districtFC,
  "../datos/catalogo_procedencia.json":catalogo,
  "calendario.json":{madrid:[["202305","may. 2023"]]}
};
for(const v of Object.values(index.territorios))fixtures["../datos/"+v.geojson.ruta]=districtFC;
const group={},el={};
function element(id){
  if(id==="level"&&!el[id]){
    el[id]={id,options:["comunidad","provincia","distrito","municipio","seccion"].map(value=>
      ({value,disabled:false,removeAttribute(k){delete this[k];}}))};
  }
  return el[id]||(el[id]={id,value:"",hidden:false,checked:true,
  innerHTML:"",textContent:"",dataset:{},style:{},
  setAttribute(k,v){this[k]=v;},addEventListener(k,fn){this[k]=fn;},
  replaceChildren(...children){this.children=children;},
  appendChild(child){(this.children??=[]).push(child);return child;}});}
for(const [id,opts] of [["scope",["nacional","autonomico"]],
  ["system",["proporcional","mayoritario"]],["view",["territorial","electoral"]]]){
  group["#"+id+" button"]=opts.map(value=>({dataset:{value},setAttribute(k,v){this[k]=v;}}));
}
group["[data-panel]"]=["territorio","resultados","comparar","evolucion"]
  .map(panel=>({dataset:{panel},setAttribute(k,v){this[k]=v;}}));
const doc={getElementById:element,querySelectorAll:q=>group[q]||[],
  createElement:tag=>({tag,textContent:"",setAttribute(k,v){this[k]=v;}}),
  body:{dataset:{}}};
let map;
class FakeMap{
  constructor(){this.sources=new Map();this.layers=new Map();this.handlers={};this.hit=[];
    map=this;queueMicrotask(()=>this.handlers.load?.());}
  addControl(){}
  on(ev,...args){this.handlers[ev]=args.at(-1);}
  addSource(id,s){this.sources.set(id,{data:s.data,setData(next){this.data=next;}});}
  getSource(id){return this.sources.get(id);}
  addLayer(layer){this.layers.set(layer.id,{...layer,layout:{visibility:"visible",...layer.layout},
    paint:{...layer.paint}});}
  getLayer(id){return this.layers.get(id);}
  getLayoutProperty(id,k){return this.layers.get(id).layout[k];}
  setLayoutProperty(id,k,v){this.layers.get(id).layout[k]=v;}
  setPaintProperty(id,k,v){this.layers.get(id).paint[k]=v;}
  fitBounds(){}
  getZoom(){return 5;}
  queryRenderedFeatures(){return this.hit;}
}
const libre={Map:FakeMap,NavigationControl:class{}};
const sandbox={document:doc,window:{maplibregl:libre},maplibregl:libre,console,
  fetch:async key=>({ok:Object.hasOwn(fixtures,key),status:Object.hasOwn(fixtures,key)?200:404,
    json:async()=>fixtures[key]})};
const marker="  init();\n})();";
assert.ok(source.includes(marker),"Cambió el arranque de V3");
const instrumented=source.replace(marker,
  '  globalThis.__DDD_TEST__={S,D,PALETA,regionId,openProvince,renderDetail,getProvinceEntry};\n  init();\n})();');
vm.runInNewContext(instrumented,sandbox,{filename:"v3.js",timeout:5000});
const flush=async()=>{for(let i=0;i<16;i++)await new Promise(resolve=>setImmediate(resolve));};
async function main(){
  await flush();
  const t=sandbox.__DDD_TEST__;
  assert.equal(doc.body.dataset.ready,"1","el mapa inicial debe cargar");
  assert.equal(t.PALETA.PP,"#1d6fb8");
  assert.equal(t.PALETA.PSOE,"#d32b2b");
  assert.equal(t.PALETA.VOX,"#5fa335");
  const feat=n=>({properties:{nombre:n}});
  const saved=t.D.index;
  t.D.index={territorios:{nac28:{provincia:"Madrid"},congreso_albacete:{},nac02:{provincia:"Albacete"}}};
  assert.equal(t.getProvinceEntry(feat("Madrid")).key,"nac28","resolución por campo provincia (clave nacNN)");
  t.D.index={territorios:{congreso_albacete:{}}};
  assert.equal(t.getProvinceEntry(feat("Albacete")).key,"congreso_albacete","clave heredada congreso_*");
  t.D.index={territorios:{congreso_madrid:{provincia:"Madrid"}}};
  assert.equal(t.getProvinceEntry(feat("Madrid")).key,"congreso_madrid");
  t.D.index=saved;
  const names={"Asturias":"principado_de_asturias","Baleares":"illes_balears",
    "Navarra":"comunidad_foral_de_navarra"};
  for(const [name,id] of Object.entries(names))assert.equal(t.regionId(name),id);
  group["#scope button"][1].onclick();await flush();
  assert.equal(element("level").options.find(x=>x.value==="seccion").disabled,true,
    "sin geometrías autonómicas seccionadas no debe ofrecerse el nivel");
  for(const name of Object.keys(names)){
    const f=comunidades.features.find(x=>x.properties.nombre===name);
    assert.ok(f);
    map.hit=[{layer:{id:"ccaa-fill"},geometry:f.geometry,properties:f.properties}];
    map.handlers.click({point:{}});
    await flush();
    assert.equal(t.S.region,names[name],name+" no resuelve el catálogo");
    assert.equal(element("current-label").textContent,"Parlamento autonómico");
    assert.equal(Number(element("ddd-count").textContent),
      ({Asturias:45,Baleares:59,Navarra:50})[name]);
  }
  group["#scope button"][0].onclick();
  assert.equal(element("level").options.find(x=>x.value==="seccion").disabled,false);
  group["#system button"][1].onclick();
  await flush();
  assert.equal(t.S.scope,"nacional");
  assert.equal(t.S.system,"mayoritario");
  assert.ok(map.getSource("distritos").data.features.length>=1,"no se cargaron distritos");
  t.openProvince("28",true);await flush();
  element("level").value="seccion";
  element("level").onchange({target:element("level")});await flush();
  const sec=map.getSource("secciones").data.features[0];
  assert.ok(sec,"no se cargó la sección");
  assert.equal(sec.properties.s,"2807912003");
  assert.equal(sec.properties.party,first.ganador==="PP"?"PP":"PSOE");
  assert.equal(map.getLayer("sec-fill").layout.visibility,"visible");
  t.S.unit={kind:"distrito",properties:map.getSource("distritos").data.features[0].properties};
  element("elections").children.find(b=>b.textContent==="nov. 2011").onclick();
  await flush();
  assert.match(element("context").innerHTML,/No disponible para la elección\/vista/);
  assert.equal(map.getLayer("dist-fill").paint["fill-color"],"#a8bac7");
  group["#system button"][0].onclick();await flush();
  assert.equal(map.getLayer("dist-fill").layout.visibility,"none");
  // T-300: panel de procedencia, leído del catálogo publicado.
  const prov=()=>element("prov-content").innerHTML;
  const madridKey=t.getProvinceEntry(madrid).key;
  const vig=catalogo.territorios[madridKey].productos.find(p=>p.vigente&&p.producto==="M08");
  t.S.unit={kind:"provincia",properties:madrid.properties};t.S.election="202307";t.S.view="electoral";
  t.renderDetail();
  assert.match(prov(),/Padrón/);assert.match(prov(),/Seccionado/);
  assert.ok(prov().includes(vig.sha256.slice(0,12)),"huella abreviada del catálogo");
  assert.ok(!prov().includes(vig.sha256),"la huella va abreviada");
  assert.ok(!prov().includes(vig.run_id),"sin id de ejecución del repositorio privado (D-92)");
  assert.ok(prov().includes(catalogo.motor.nombre+" "+catalogo.motor.version+" (no necesariamente la de este mapa)"),"motor: versión actual con su salvedad");
  assert.match(prov(),/Motor Deslinde \(versión actual\)/);
  assert.ok(prov().includes(catalogo.fuentes_oficiales.poblacion_por_sexo_y_edad.url),"enlace al padrón oficial");
  assert.ok(prov().includes(catalogo.fuentes_oficiales.resultados_electorales[vig.eleccion].url),"enlace a resultados");
  assert.ok(prov().includes(vig.eleccion),"elección");
  assert.match(prov(),/Fecha de generación<\/dt><dd>No consta/,"sin inventar fecha");
  assert.ok(!/territorios\/|receipt/.test(prov()),"sin rutas ni ids internos del repositorio");
  t.S.election="201911";t.renderDetail();
  assert.match(prov(),/Sin producto vigente/,"elección sin producto: aviso");
  t.S.election="202307";
  const savedProv=t.D.provenance;t.D.provenance=null;t.renderDetail();
  assert.match(prov(),/Procedencia no disponible/,"sin catálogo: aviso, nada inventado");
  assert.ok(!/sha256|Deslinde/.test(prov()));
  t.D.provenance=savedProv;
  t.S.unit=null;t.renderDetail();
  assert.match(prov(),/Selecciona una provincia/);
  // T-295: accesibilidad.
  const html=fs.readFileSync(path.join(ROOT,"visor/v3/index.html"),"utf8");
  const css=fs.readFileSync(path.join(ROOT,"visor/v3/v3.css"),"utf8");
  assert.match(html,/<html lang="es">/);
  assert.match(html,/class="skip" href="#contenido"/,"enlace de salto");
  assert.match(html,/id="sr-status"[^>]*aria-live="polite"/,"región viva única para el anuncio de la selección");
  assert.ok(!/<aside class="insights"[^>]*aria-live/.test(html),"sin aria-live en toda la columna (ruido)");
  assert.ok(!/id="provenance"[^>]*aria-live/.test(html),"el panel de procedencia no duplica el anuncio");
  for(const id of ["reset-map","peninsula","canarias","help"])
    assert.match(html,new RegExp('id="'+id+'"[^>]*aria-label="[^"]{4,}"'),"nombre accesible de #"+id);
  assert.match(html,/id="map"[^>]*aria-describedby="map-help"/);
  assert.match(html,/id="results-table"/);
  assert.match(css,/prefers-reduced-motion:reduce/);
  assert.match(css,/:focus-visible[^{]*\{outline:3px solid #14161a/);
  assert.ok(!/e6a344/.test(css),"foco antiguo de 2.1:1");
  function lum(h){const c=[1,3,5].map(i=>parseInt(h.slice(i,i+2),16)/255).map(v=>v<=.03928?v/12.92:((v+.055)/1.055)**2.4);return .2126*c[0]+.7152*c[1]+.0722*c[2];}
  function ratio(a,b){const [x,y]=[lum(a),lum(b)].sort((m,n)=>n-m);return (x+.05)/(y+.05);}
  for(const [fg,bg,min,what] of [["#575962","#ffffff",4.5,"texto gris"],["#575962","#fdf1f1",4.5,"gris sobre tarjeta"],
    ["#ffffff","#7d5547",4.5,"hero fin degradado"],["#ffffff","#9c2733",4.5,"botón activo"],["#14161a","#ffffff",3,"foco"],
    ["#868992","#ffffff",3,"borde de control"],["#575962","#f9eff0",4.5,"gris sobre tarjeta"]])
    assert.ok(ratio(fg,bg)>=min,what+" "+fg+"/"+bg+" "+ratio(fg,bg).toFixed(2));
  // anuncio de la selección y tabla alternativa
  t.S.unit={kind:"provincia",properties:madrid.properties};t.S.election="202307";t.S.view="electoral";t.S.scope="nacional";
  element("results-table").dataset={};t.renderDetail();
  assert.match(element("sr-status").textContent,/Provincia: Madrid/,"se anuncia la selección");
  const tbl=element("results-table").innerHTML;
  assert.match(tbl,/<caption>Resultados generales 2023 por provincia/);
  assert.match(tbl,/<th scope='row'><button type='button' data-prov='28'>Madrid<\/button>/,"fila de Madrid operable con teclado");
  assert.equal((tbl.match(/data-prov=/g)||[]).length,provincias.features.length,"todas las provincias en la tabla");
  assert.match(tbl,/<td><i style='background:#[0-9a-f]{6}'><\/i>(PP|PSOE|VOX)/,"partido por nombre además del color");
  t.S.election="201911";t.renderDetail();
  assert.match(element("results-table").innerHTML,/sin capa electoral certificada/,"sin 2023 no se atribuyen ganadores");
  t.S.election="202307";
  console.log("V3 UI smoke: PASS (regiones, mapa, secciones, fecha y sistema)");
}
main().catch(e=>{console.error(e);process.exitCode=1;});
