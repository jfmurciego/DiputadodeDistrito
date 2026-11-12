/* PROYECTO: Diputado de Distrito
 * CLASE: prueba de interacción V3
 * VERSIÓN: 1.0.0 · FECHA: 2026-11-12 · ESTADO: candidato
 * ANTERIOR: ninguna (fichero nuevo)
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
  '  globalThis.__DDD_TEST__={S,D,PALETA,regionId,openProvince,renderDetail};\n  init();\n})();');
vm.runInNewContext(instrumented,sandbox,{filename:"v3.js",timeout:5000});
const flush=async()=>{for(let i=0;i<16;i++)await new Promise(resolve=>setImmediate(resolve));};
async function main(){
  await flush();
  const t=sandbox.__DDD_TEST__;
  assert.equal(doc.body.dataset.ready,"1","el mapa inicial debe cargar");
  assert.equal(t.PALETA.PP,"#1d6fb8");
  assert.equal(t.PALETA.PSOE,"#d32b2b");
  assert.equal(t.PALETA.VOX,"#5fa335");
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
  console.log("V3 UI smoke: PASS (regiones, mapa, secciones, fecha y sistema)");
}
main().catch(e=>{console.error(e);process.exitCode=1;});
