/* PROYECTO: Diputado de Distrito
 * CLASE: visor V3 (nueva interfaz)
 * VERSIÓN: 1.0.0
 * FECHA: 2026-11-12
 * ESTADO: candidato
 * CAMBIOS: explorador mapa, ámbito, proporcional/mayoritario, territorial/electoral,
 * calendario por ámbito, distrito y sección censal reales, paleta de partidos.
 * MOTIVO: una sola experiencia con datos acreditados y fallo cerrado ante fuentes ausentes.
 * ANTERIOR: ninguna (fichero nuevo) */
"use strict";
(function () {
  const BASE={provincias:"../v2/datos/provincias.json",comunidades:"../v2/datos/comunidades.json",
    indices:"../datos/INDEX.json",secciones:"../v2/datos/secciones/",territorial:"../v2/datos/territorial.json",
    productos:"../data/viewer-results.json",calendario:"calendario.json"};
  const PALETA={PP:"#1d6fb8",PSOE:"#d32b2b",VOX:"#5fa335",SUMAR:"#cf2a7b",PODEMOS:"#8750b5",
    "EAJ-PNV":"#2c5e36","EH BILDU":"#0f7a52",ERC:"#f0ac00",JUNTS:"#18a99b",BNG:"#7cb2d8",CC:"#e8c400",
    UPN:"#3a55a2",OTROS:"#9aa3ad"};
  const NATIONAL=[["201111","nov. 2011"],["201512","dic. 2015"],["201606","jun. 2016"],
    ["201904","abr. 2019"],["201911","nov. 2019"],["202307","jul. 2023"]];
  const REGION={
    "Andalucía":"andalucia","Aragón":"aragon","Principado de Asturias":"principado_de_asturias",
    "Islas Baleares":"illes_balears","Canarias":"canarias","Cantabria":"cantabria",
    "Castilla y León":"castilla_y_leon","Castilla-La Mancha":"castilla_la_mancha","Cataluña":"cataluna",
    "Comunidad Valenciana":"comunidad_valenciana","Extremadura":"extremadura","Galicia":"galicia",
    "Comunidad de Madrid":"madrid","Región de Murcia":"region_de_murcia",
    "Comunidad Foral de Navarra":"comunidad_foral_de_navarra","País Vasco":"pais_vasco",
    "La Rioja":"la_rioja","Ceuta":"ceuta","Melilla":"melilla"
  };
  const REGION_ALIAS={"Asturias":"principado_de_asturias","Baleares":"illes_balears","Navarra":"comunidad_foral_de_navarra"};
  const SEATS={"andalucia":109,"aragon":67,"principado_de_asturias":45,"illes_balears":59,
    "canarias":70,"cantabria":35,"castilla_y_leon":82,"castilla_la_mancha":33,
    "cataluna":135,"comunidad_valenciana":99,"extremadura":65,"galicia":75,
    "madrid":135,"region_de_murcia":45,"comunidad_foral_de_navarra":50,
    "pais_vasco":75,"la_rioja":33,"ceuta":25,"melilla":25};
  const $=id=>document.getElementById(id);
  const normal=s=>String(s||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase()
    .replace(/[^a-z0-9]/g,"");
  const fmt=x=>Number.isFinite(Number(x))?Number(x).toLocaleString("es-ES"):"—";
  const pct=x=>Number.isFinite(Number(x))?Number(x).toLocaleString("es-ES",{maximumFractionDigits:2})+" %":"—";
  function family(name){
    const s=String(name||"").toUpperCase();
    if (/^PP$|PARTIDO POPULAR/.test(s))return "PP";
    if (/PSOE|PSC|PSE-EE|PSN-|PSIB/.test(s))return "PSOE";
    if (/VOX/.test(s))return "VOX";
    if (/SUMAR/.test(s))return "SUMAR";
    if (/PODEMOS|UNIDAS PODEMOS/.test(s))return "PODEMOS";
    if (/EH BILDU|BILDU/.test(s))return "EH BILDU";
    if (/PNV/.test(s))return "EAJ-PNV";
    if (/^ERC|ESQUERRA REPUBLICANA/.test(s))return "ERC";
    if (/JUNTS/.test(s))return "JUNTS";
    if (/BNG/.test(s))return "BNG";
    if (/COALICION CANARIA|^CCA$|^CC$/.test(s))return "CC";
    if (/^UPN$/.test(s))return "UPN";
    return "OTROS";
  }
  function esc(s){return String(s??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;");}
  function color(n){return PALETA[family(n)]||PALETA.OTROS;}
  function randomNeutral(n){const pal=["#91aabb","#a5bcc8","#b5c8d0","#9baac2","#c2d0da","#afbeca","#8eabb7"];let h=0;for(const ch of String(n))h=(h*31+ch.charCodeAt(0))>>>0;return pal[h%pal.length];}
  const S={scope:"nacional",system:"proporcional",view:"electoral",layer:"ganador",level:"provincia",election:"202307",region:"",panel:"territorio",province:null,unit:null,selected:null};
  const D={prov:null,communities:null,index:null,sectionsIndex:null,territorial:null,products:null,calendar:{},
    districtCache:new Map(),sectionCache:new Map(),regionCache:new Map(),allDistricts:new Map(),allSections:new Map()};
  let districtBulkPromise=null;
  let map=null,bootstrap=false,loading=false;
  const empty=()=>({type:"FeatureCollection",features:[]});
  async function getJson(path){const r=await fetch(path,{cache:"default"});if(!r.ok)throw Error(path+": HTTP "+r.status);return r.json();}
  function note(t){$("map-notice").textContent=t||"";}
  function legend(t){$("legend").innerHTML=t;}
  function helpText(t){$("election-note").textContent=t;}
  function bbox(geometry){let box=[180,90,-180,-90];function walk(coords){if(typeof coords[0]==="number"){box[0]=Math.min(box[0],coords[0]);box[1]=Math.min(box[1],coords[1]);box[2]=Math.max(box[2],coords[0]);box[3]=Math.max(box[3],coords[1]);}else coords.forEach(walk);}walk(geometry.coordinates||[]);return [[box[0],box[1]],[box[2],box[3]]];}
  function focus(g){if(map&&g&&g.coordinates){map.fitBounds(bbox(g),{padding:65,maxZoom:12,duration:420});}}
  function updateSegments(id,val){document.querySelectorAll("#"+id+" button").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.value===val)));}
  function paletteExpression(){const e=["match",["get","party"]];Object.entries(PALETA).forEach(([k,c])=>{e.push(k,c);});e.push(PALETA.OTROS);return e;}
  function paintWith(layer,fill){if(map?.getLayer(layer))map.setPaintProperty(layer,"fill-color",fill);}
  function showLayer(id,show){if(map?.getLayer(id))map.setLayoutProperty(id,"visibility",show?"visible":"none");}
  function rows(){
    const a=["PP","PSOE","VOX","SUMAR","PODEMOS","EAJ-PNV","EH BILDU","ERC","JUNTS","BNG","CC","OTROS"];
    legend("<h3>"+(S.view==="electoral"?"Partido más votado":"Unidades territoriales")+"</h3><ul>"+
      (S.view==="electoral"?a.map(p=>"<li><i style='background:"+PALETA[p]+"'></i>"+esc(p)+"</li>").join(""):
      "<li><i style='background:#9caebc'></i>Territorio</li><li><i style='background:#9c2733'></i>Seleccionado</li>")+"</ul>"+
      "<small>"+(S.view==="electoral"?"PP azul · PSOE rojo · VOX verde · Sumar rosa. Se muestra el nivel electoral acreditado.":"Colores territoriales sin significado partidista.")+"</small>");
  }
  function validElection(){return S.scope==="nacional"&&S.election==="202307";}
  function availability(){
    if(S.scope==="autonomico"&&S.system==="proporcional"&&S.view==="electoral")
      return "Todavía no se ha publicado aquí un producto de resultados autonómicos proporcionales con cartografía para la elección seleccionada.";
    if(S.scope==="nacional"&&!validElection()&&S.view==="electoral")
      return "Elección histórica elegida. La serie existe en el repositorio, pero no está materializada aquí como capa electoral de sección/distrito V3. No se reutilizan los colores de 2023.";
    if(S.scope==="autonomico"&&S.view==="electoral"&&!S.region)
      return "Selecciona una comunidad para consultar sus productos M08 publicados; no se mezclan resultados de parlamentos distintos.";
    if(S.scope==="autonomico"&&S.view==="electoral"&&S.region)
      return "Los productos M08 autonómicos no acreditan en este visor la identidad de la elección seleccionada: la cartografía se muestra neutra hasta disponer de esa correspondencia.";
    return "";
  }
  function provinceFeatures(){return D.prov?.features||[];}
  function namedProvince(name){return provinceFeatures().find(f=>normal(f.properties.nombre)===normal(name));}
  function provinceByCode(code){return provinceFeatures().find(f=>f.properties.cod===code);}
  function selectedProvince(){return S.province&&provinceByCode(S.province);}
  function getProvinceEntry(f){
    if(!D.index?.territorios||!f)return null;
    const n=normal(f.properties.nombre);
    let e=Object.entries(D.index.territorios).find(([key,v])=>normal(v.provincia)===n);
    if(!e){const candidates=[n,n.replace(/^islas/,""),n.replace(/^illes/,""),n.replace("lapalma","santacruzdetenerife")];
      e=Object.entries(D.index.territorios).find(([key,v])=>candidates.some(c=>normal(key.replace(/^congreso_/,""))===c));}
    return e?{key:e[0],data:e[1]}:null;
  }
  function metaOfDistrict(province,id){
    const e=getProvinceEntry(province);
    return e?.data.distritos?.find(d=>Number(d.distrito)===Number(id))||null;
  }
  function overviewProps(){
    const f=provinceFeatures();return f.map(x=>{
      const p=x.properties,ent=getProvinceEntry(x),winner=ent?.data?.distritos?.length?
        Object.entries(ent.data.distritos.reduce((a,d)=>(a[family(d.ganador)]=(a[family(d.ganador)]||0)+1,a),{}))
        .sort((a,b)=>b[1]-a[1])[0]?.[0]||"":""; // ganador dominante entre los distritos de la provincia
      const ds=ent?.data?.distritos||[],pop=ds.reduce((a,d)=>a+(Number(d.poblacion)||0),0);
      const target=ds.length?pop/ds.length:0;
      const deviation=target?Math.max(...ds.map(d=>Math.abs((Number(d.poblacion)-target)/target))):null;
      return {...x,properties:{...p,party:family(S.system==="mayoritario"?winner:p.ganador),
        population:pop||null,deviation:deviation,dominant:winner}};
    });
  }
  function styleInit(){return{version:8,sources:{},layers:[{id:"water",type:"background",paint:{"background-color":"#eef3f7"}}]};}
  function installSource(id,g){if(map.getSource(id))map.getSource(id).setData(g);else map.addSource(id,{type:"geojson",data:g});}
  function install(){
    installSource("ccaa",D.communities);
    installSource("prov",{type:"FeatureCollection",features:overviewProps()});
    installSource("distritos",empty());installSource("secciones",empty());
    map.addLayer({id:"ccaa-fill",type:"fill",source:"ccaa",paint:{"fill-color":"#b8c5d0","fill-opacity":.8}});
    map.addLayer({id:"ccaa-line",type:"line",source:"ccaa",paint:{"line-color":"#687b8a","line-width":1.3}});
    map.addLayer({id:"prov-fill",type:"fill",source:"prov",paint:{"fill-color":paletteExpression(),"fill-opacity":.84}});
    map.addLayer({id:"prov-line",type:"line",source:"prov",paint:{"line-color":"#fff","line-width":1}});
    map.addLayer({id:"prov-label",type:"symbol",source:"prov",
      layout:{"text-field":["get","nombre"],"text-size":11,"visibility":"none","text-allow-overlap":false},
      paint:{"text-color":"#283746","text-halo-color":"#ffffff","text-halo-width":1.6}});
    map.addLayer({id:"dist-fill",type:"fill",source:"distritos",paint:{"fill-color":paletteExpression(),"fill-opacity":.88}});
    map.addLayer({id:"dist-line",type:"line",source:"distritos",paint:{"line-color":"#fff","line-width":.8}});
    map.addLayer({id:"sec-fill",type:"fill",source:"secciones",paint:{"fill-color":paletteExpression(),"fill-opacity":.82}});
    map.addLayer({id:"sec-line",type:"line",source:"secciones",paint:{"line-color":"#fff","line-width":.45}});
    map.on("click",e=>{
      const visible=["sec-fill","dist-fill","prov-fill","ccaa-fill"].filter(id=>map.getLayoutProperty(id,"visibility")!=="none");
      const hits=map.queryRenderedFeatures(e.point,{layers:visible});
      if(!hits.length)return;
      const f=hits[0],p=f.properties;
      if(f.layer.id==="sec-fill"){S.unit={kind:"seccion",properties:p};S.selected=p.s;renderDetail();return;}
      if(f.layer.id==="dist-fill"){
        if(p.province)S.province=p.province;
        S.unit={kind:"distrito",properties:p};S.selected=p.distrito||p.id;
        S.level="distrito";$("level").value="distrito";focus(f.geometry);renderDetail();return;}
      if(f.layer.id==="prov-fill"){openProvince(p.cod,true);return;}
      if(f.layer.id==="ccaa-fill"){S.region=regionId(p.nombre);$("election-region").value=S.region;
        S.unit={kind:"comunidad",properties:p};S.selected=p.cod;syncElection();focus(f.geometry);refresh();return;}
    });
    map.on("zoomend",()=>{if($("auto-sections").checked&&map.getZoom()>=7.2&&S.province&&S.level!=="seccion"){S.level="seccion";$("level").value="seccion";prepareArea();}});
    document.body.dataset.ready="1";
    refresh();
  }
  function regionId(name){return REGION[name]||REGION_ALIAS[name]||
    Object.entries({...REGION,...REGION_ALIAS}).find(([k,v])=>normal(k)===normal(name))?.[1]||"";}
  function regionName(id){return Object.entries(REGION).find(([k,v])=>v===id)?.[0]||id;}
  async function loadDistricts(f){
    const cod=f.properties.cod;if(D.districtCache.has(cod))return D.districtCache.get(cod);
    const e=getProvinceEntry(f);
    if(!e?.data?.geojson?.ruta)throw Error("No hay producto de distritos acreditado para "+f.properties.nombre);
    const raw=await getJson("../datos/"+e.data.geojson.ruta);
    const features=raw.features.map(g=>{
      const d=Number(g.properties?.distrito??g.properties?.district_id??g.properties?.district),m=metaOfDistrict(f,d);
      const target=e.data.distritos?.length?e.data.distritos.reduce((a,x)=>a+(Number(x.poblacion)||0),0)/e.data.distritos.length:0;
      return {...g,properties:{...g.properties,province:cod,provinceName:f.properties.nombre,distrito:d,party:m?family(m.ganador):"OTROS",ganador:m?.ganador||"",population:m?.poblacion??g.properties?.district_pop??null,
        deviation:target?((Number(m?.poblacion)-target)/target):null,neutralColor:randomNeutral(d),
        sections:m?.secciones??null,municipios:m?.municipios??null,run_id:e.data.run_id,identity:e.key}};
    });
    const fc={type:"FeatureCollection",features};
    D.districtCache.set(cod,fc);return fc;
  }
  async function loadNationalDistricts(){
    if(D.allDistricts.size>=provinceFeatures().length){
      installSource("distritos",{type:"FeatureCollection",features:Array.from(D.allDistricts.values()).flatMap(x=>x.features)});return;
    }
    if(districtBulkPromise)return districtBulkPromise;
    districtBulkPromise=(async()=>{
      const provs=provinceFeatures(),pending=provs.filter(p=>!D.allDistricts.has(p.properties.cod));
      let next=0,done=0;const errors=[];
      async function worker(){
        while(next<pending.length){
          const p=pending[next++];
          try{const layer=await loadDistricts(p);D.allDistricts.set(p.properties.cod,layer);}
          catch(e){errors.push(p.properties.nombre);}
          done++;
          if(done%5===0||done===pending.length){
            installSource("distritos",{type:"FeatureCollection",features:Array.from(D.allDistricts.values()).flatMap(x=>x.features)});
            $("map-caption").textContent="Cargando distritos DDD: "+done+"/"+pending.length+" provincias";
          }
        }
      }
      await Promise.all(Array.from({length:Math.min(5,pending.length)},worker));
      if(errors.length)note("Distritos no disponibles para: "+errors.join(", ")+".");
    })().finally(()=>{districtBulkPromise=null;});
    return districtBulkPromise;
  }
  function secGroupColor(d){return randomNeutral("DDD-"+d);}
  async function loadSections(f){
    const cod=f.properties.cod;if(D.sectionCache.has(cod))return D.sectionCache.get(cod);
    if(!D.sectionsIndex?.provincias?.[cod])throw Error("No hay secciones INE publicadas para "+f.properties.nombre);
    const d=await getJson(BASE.secciones+cod+".geojson");
    if(d.type!=="FeatureCollection")throw Error("Geometría seccional inválida");
    const ents=getProvinceEntry(f);
    const byDist=new Map((ents?.data.distritos||[]).map(x=>[Number(x.distrito),x]));
    const features=d.features.map(x=>{
      const m=byDist.get(Number(x.properties.d));
      return {...x,properties:{...x.properties,province:cod,provinceName:f.properties.nombre,party:m?family(m.ganador):"OTROS",
        winnerOfDistrict:m?.ganador||"",parentDistrict:m?.distrito||x.properties.d,
        identity:"cusec:"+x.properties.s}};
    });
    const fc={type:"FeatureCollection",features};D.sectionCache.set(cod,fc);return fc;
  }
  function newest(items,kind){return items.filter(x=>x.kind===kind&&x.viewer_path&&x.publication_status==="PUBLICABLE").sort((a,b)=>Number(b.run_id)-Number(a.run_id))[0]||null;}
  async function loadAutonomic(){
    if(!S.region)return;
    const cacheKey=S.region+":"+S.view;
    if(D.regionCache.has(cacheKey)){installSource("distritos",D.regionCache.get(cacheKey));return;}
    const items=D.products?.results||[];
    const kind=S.view==="electoral"?"canonical_m08":"canonical_m06";
    let product=newest(items.filter(x=>x.territory_id===S.region),kind);
    if(!product&&kind==="canonical_m08")product=newest(items.filter(x=>x.territory_id===S.region),"canonical_m06");
    if(!product){note("No hay un producto "+kind+" publicable para "+regionName(S.region)+".");installSource("distritos",empty());return;}
    const raw=await getJson("../"+product.viewer_path);
    const mapped={type:"FeatureCollection",features:raw.features.map((x,i)=>{const p=x.properties||{},winner=p.winner_party||p.ganador||p.winner||"";
      return {...x,properties:{...p,distrito:p.distrito??p.district_id??i+1,party:family(winner),ganador:winner,
        population:p.population??p.district_pop??p.poblacion??null,region:S.region,run_id:product.run_id,
        neutralColor:randomNeutral(S.region+":"+(p.distrito??p.district_id??i+1))}};})};
    D.regionCache.set(cacheKey,mapped);installSource("distritos",mapped);
    $("source-label").textContent=product.label+" · "+product.certification_status+" · ejecución "+product.run_id;
  }
  async function prepareArea(){
    if(!map||!bootstrap)return;
    const ticket=Date.now();loading=true;
    if(S.scope==="autonomico"&&S.system==="mayoritario"&&S.region){
      try{await loadAutonomic();}catch(e){note("No se ha podido cargar el producto autonómico: "+e.message);}
    }else if(S.scope==="nacional"&&S.system==="mayoritario"&&!S.province){
      try{await loadNationalDistricts();}catch(e){note("Error al recuperar el mapa nacional: "+e.message);}
    }else if(S.scope==="nacional"&&S.province&&(S.level==="distrito"||S.level==="seccion"||S.level==="municipio"||S.system==="mayoritario")){
      const f=selectedProvince();
      try{installSource("distritos",await loadDistricts(f));}catch(e){installSource("distritos",empty());note(e.message);}
    }else installSource("distritos",empty());
    if(S.province&&(S.level==="seccion"||S.level==="municipio")){
      try{installSource("secciones",await loadSections(selectedProvince()));}
      catch(e){installSource("secciones",empty());note(e.message);}
    }else installSource("secciones",empty());
    loading=false;paint();renderDetail();
  }
  function paint(){
    if(!bootstrap)return;
    const isN=S.scope==="nacional",isElect=S.view==="electoral",good=validElection();
    const showC=!isN||S.level==="comunidad";
    const showS=isN&&S.province&&(S.level==="seccion"||S.level==="municipio")&&D.sectionsIndex?.provincias?.[S.province];
    const showD=(isN&&S.system==="mayoritario"&&(!!S.province||D.allDistricts.size>0))
     ||(!isN&&S.system==="mayoritario"&&!!S.region);
    showLayer("ccaa-fill",showC);showLayer("ccaa-line",true);
    showLayer("prov-fill",isN&&!showC&&!showD&&!showS);showLayer("prov-line",isN&&!showC&&!showS);
    showLayer("dist-fill",!!showD&&!showS);showLayer("dist-line",!!showD&&!showS);
    showLayer("sec-fill",!!showS);showLayer("sec-line",!!showS);
    // Nunca usar colores de una elección distinta para un resultado.
    const permitColors=isElect&&isN&&good; // Sin correspondencia electoral autonómica acreditada, nunca pintar ganadores de otra elección.
    const neutral="#a8bac7";
    const party=paletteExpression();
    const territorial=["get","neutralColor"];
    paintWith("ccaa-fill",neutral);
    const popColor=["interpolate",["linear"],["to-number",["get","population"],0],0,"#e9f0f3",100000,"#9cc5d2",1000000,"#4c819f",4000000,"#244e73"];
    const devColor=["interpolate",["linear"],["abs",["to-number",["get","deviation"],0]],0,"#dcebdc",.12,"#c2d4b4",.25,"#f3cb84",.6,"#b64c53"];
    function thematic(base){if(S.layer==="poblacion")return popColor;if(S.layer==="desviacion")return devColor;
      if(S.layer==="unidades")return ["coalesce",["get","neutralColor"],neutral];return base;}
    paintWith("prov-fill",thematic(permitColors?party:neutral));
    paintWith("dist-fill",thematic(permitColors?party:S.view==="territorial"?["coalesce",["get","neutralColor"],neutral]:neutral));
    const secPop=["interpolate",["linear"],["to-number",["get","p"],0],0,"#eff6f9",500,"#bbd6df",2000,"#497e9b",5000,"#193f61"];
    const secTerr=["coalesce",["get","territorialColor"],neutral];
    paintWith("sec-fill",S.layer==="poblacion"?secPop:
      (S.layer==="desviacion"?neutral:S.view==="territorial"?secTerr:
      (permitColors&&isN&&S.system==="mayoritario"?party:neutral)));
    if(map.getLayer("sec-fill")&&showS&&(S.view==="territorial"||S.layer==="unidades")){
      // Colorea por distrito o municipio, nunca atribuye voto propio a una sección.
      let fc=D.sectionCache.get(S.province);
      if(fc){const newFc={type:"FeatureCollection",features:fc.features.map(f=>({...f,properties:{...f.properties,
        territorialColor:S.level==="municipio"?randomNeutral(f.properties.m):secGroupColor(f.properties.d)}}))};
        installSource("secciones",newFc);}
    }
    ["prov-line","dist-line","sec-line"].forEach(id=>map.setPaintProperty(id,"line-opacity",$("boundaries").checked?1:0));
    showLayer("prov-label",$("labels").checked&&S.scope==="nacional"&&!showS);
    map.setPaintProperty("prov-fill","fill-opacity",S.view==="electoral"?.88:.68);
    map.setPaintProperty("dist-fill","fill-opacity",.82);map.setPaintProperty("sec-fill","fill-opacity",.86);
    // Resalta mediante trazo de selección en la ficha contextual, sin crear resultados de ejemplo.
    const s=availability();if(s)note(s);
    rows();
    if(S.layer==="poblacion"||S.layer==="desviacion"){
      legend("<h3>"+(S.layer==="poblacion"?"Población":"Desviación de población")+"</h3><div style='height:12px;background:linear-gradient(90deg,#dcebdc,#f3cb84,#b64c53);border-radius:6px'></div><small>Capa basada en población M06, donde está publicada; no representa partidos.</small>");
    }
    if(showS)legend($("legend").innerHTML+"<small><b>Importante:</b> la geometría es de la sección censal INE; el color electoral, cuando exista, es heredado del distrito DDD, no de un escrutinio propio de la sección.</small>");
    const caption=S.scope==="nacional"?
      (S.view==="territorial"?"Geometrías territoriales DDD / INE":
       good?(S.system==="mayoritario"?"Ganador por distrito DDD · generales de 2023":"Partido más votado por provincia · generales de 2023"):"Sin capa electoral certificada para la fecha elegida"):
      (S.system==="mayoritario"?"Distritos autonómicos publicados · "+regionName(S.region):"Comunidades autónomas · cartografía");
    $("map-caption").textContent=caption;
  }
  function findDistrict(d){return D.districtCache.get(S.province)?.features.find(x=>Number(x.properties.distrito)===Number(d));}
  function openProvince(cod,move){
    const f=provinceByCode(cod);if(!f)return;
    S.province=cod;S.unit={kind:"provincia",properties:f.properties};S.selected=cod;
    if(S.scope==="nacional"&&S.system==="mayoritario"&&S.level==="provincia"){S.level="distrito";$("level").value="distrito";}
    if(move)focus(f.geometry);
    note("");prepareArea();renderDetail();
  }
  function renderTimeline(){
    const auto=S.scope==="autonomico";$("election-region").hidden=!auto;
    $("election-region-label").hidden=!auto;
    $("election-region").value=S.region;
    $("timeline-subtitle").textContent=auto?"Elecciones autonómicas · "+(S.region?regionName(S.region):"elige comunidad"):"Elecciones generales";
    const rows=auto?(D.calendar[S.region]||[]):NATIONAL;
    const container=$("elections");container.replaceChildren();
    if(!rows.length){container.textContent="Selecciona un parlamento para ver sus convocatorias documentadas.";return;}
    if(!rows.some(x=>x[0]===S.election)){S.election=auto?rows[rows.length-1][0]:"202307";}
    rows.forEach(([id,label])=>{
      const b=document.createElement("button");b.type="button";b.textContent=label;b.setAttribute("aria-pressed",String(S.election===id));
      b.onclick=()=>{S.election=id;renderTimeline();note("");refresh();};
      container.appendChild(b);
    });
    helpText(auto?"Calendario derivado de las ediciones históricas almacenadas; el mapa solo usa el producto acreditado disponible.":"Histórico documentado en el repositorio. Mapa electoral detallado disponible para 2023.");
  }
  function renderDetail(){
    const obj=S.unit?.properties||{},kind=S.unit?.kind||"pais";
    $("selection-type").textContent={pais:"España",comunidad:"Comunidad autónoma",provincia:"Provincia",distrito:"Distrito uninominal",seccion:"Sección censal INE"}[kind];
    let name=kind==="pais"?"España":kind==="seccion"?"Sección "+obj.s:kind==="distrito"?"Distrito "+obj.distrito:(obj.nombre||"España");
    $("selection-name").textContent=name;
    $("selection-path").textContent=kind==="seccion"?
      "España › "+(selectedProvince()?.properties.nombre||"") +" › distrito "+obj.d+" › CUSEC "+obj.s:
      kind==="distrito"?"España › "+(selectedProvince()?.properties.nombre||"") +" › "+name:
      kind==="provincia"?"España › "+name:"Selección territorial actual";
    $("ddd-count").textContent=S.scope==="nacional"?"407":(SEATS[S.region]??"—");
    $("current-count").textContent=S.scope==="nacional"?"350":(SEATS[S.region]??"—");
    $("ddd-label").textContent=S.scope==="nacional"?"Propuesta DDD":"DDD mayoritario";
    $("current-label").textContent=S.scope==="nacional"?"Congreso actual":"Parlamento autonómico";
    $("ddd-unit").textContent=S.scope==="nacional"?"distritos nacionales":
      (S.region?"distritos previstos":"elige una comunidad");
    $("current-unit").textContent=S.scope==="nacional"?"escaños":
      (S.region?"escaños actuales":"elige un parlamento");
    const records=[];
    if(kind==="provincia"){
      const pr=selectedProvince()?.properties||obj,ent=getProvinceEntry(selectedProvince());
      records.push(["Escaños proporcionales 2023",fmt(pr.escanos)],["Distritos propuestos DDD",fmt(pr.k407)]);
      if(validElection())records.push(["Ganador provincial, 2023",pr.ganador||"—"],["Porcentaje del ganador",pct(pr.pct)]);
      else records.push(["Resultados de "+S.election,"Sin capa electoral certificada para esta fecha"]);
      if(ent)records.push(["Producto territorial",ent.data.run_id||"—"]);
    }else if(kind==="distrito"){
      records.push(["Población",fmt(obj.population)],
        ["Partido ganador del distrito",S.scope==="nacional"&&validElection()&&S.view==="electoral"?
          (obj.ganador||"Sin datos electorales"):"No disponible para la elección/vista"],
        ["Secciones",fmt(obj.sections)],["Identificador",obj.distrito],["Ejecución",obj.run_id||"—"]);
    }else if(kind==="seccion"){
      records.push(["CUSEC",obj.s],["Municipio",obj.m||"—"],["Población de sección",fmt(obj.p)],
        ["Distrito DDD",fmt(obj.d)],["Ganador del distrito 2023",S.scope==="nacional"&&validElection()&&S.system==="mayoritario"?(obj.winnerOfDistrict||"—"):"No disponible como resultado de sección"]);
    }else if(kind==="comunidad"){
      records.push(["Territorio",obj.nombre],["Modelo consultado",S.system==="mayoritario"?"Distritos uninominales":"Proporcional"]);
    }else records.push(["Ámbito",S.scope==="nacional"?"Congreso":"Parlamentos autonómicos"],["Sistema",S.system==="mayoritario"?"Mayoritario DDD":"Proporcional actual"],["Vista",S.view]);
    $("context").innerHTML="<dl>"+records.map(([a,b])=>"<div><dt>"+esc(a)+"</dt><dd>"+esc(b)+"</dd></div>").join("")+"</dl>";
    const source=kind==="seccion"?"INE · seccionado 2025 / composición DDD (no resultado de mesa)":
      kind==="distrito"?"M06 publicado; resultado M08 solo para elección acreditada · "+(obj.run_id||"sin identidad de producto"):
      kind==="provincia"?(validElection()?"Resultados oficiales generales 2023 / catálogo DDD":"Cartografía DDD · capa electoral histórica no disponible"):
        "Productos del registro durable de DDD";
    $("source-label").textContent=source;
    let content="";
    if(S.panel==="territorio")content="<p class='small-note'>Selecciona cualquier territorio en el mapa. El zoom abre distritos y, donde existen, secciones censales con su geometría real.</p>";
    if(S.panel==="resultados"){
      const data=kind==="provincia"&&validElection()&&S.scope==="nacional"?selectedProvince()?.properties.esc:null;
      const winner=kind==="distrito"&&S.scope==="nacional"&&S.view==="electoral"&&validElection()&&obj.ganador?obj.ganador:null;
      if(data){const entries=Object.entries(data).sort((a,b)=>b[1]-a[1]);const max=Math.max(1,...entries.map(x=>x[1]));
        content=entries.map(([p,n])=>"<div class='party-row'><b>"+esc(p)+"</b><div class='track'><b style='width:"+(n/max*100)+"%;background:"+color(p)+"'></b></div><strong>"+fmt(n)+"</strong></div>").join("")+
          "<p class='small-note'>Escaños oficiales de esta provincia en el Congreso de 2023.</p>";}
      else content=winner?"<p>Ganador acreditado M08: <b style='color:"+color(winner)+"'>"+esc(winner)+"</b></p>":
          "<p class='small-note'>No existe aquí un desglose electoral detallado acreditado para esta selección y fecha.</p>";
    }
    if(S.panel==="comparar")content="<div class='comparison'><div><small>Sistema actual</small><strong>"+(S.scope==="nacional"?"350":"Proporcional")+"</strong><small>Reparto por circunscripción</small></div><div><small>DDD mayoritario</small><strong>"+(S.scope==="nacional"?"407":"Distrito")+"</strong><small>Un diputado por distrito</small></div></div><p class='small-note'>La comparación de resultados se muestra solo con productos electorales de la misma elección y ámbito.</p>";
    if(S.panel==="evolucion")content="<p class='small-note'>Elige elecciones en el navegador inferior. La comparación temporal de una sección exige acreditar la identidad y geometría equivalentes; no se dibujan series ficticias.</p>";
    const headings={territorio:"Perfil territorial",resultados:"Resultados electorales",comparar:"Comparar sistemas",evolucion:"Evolución temporal"};
    $("detail-heading").textContent=headings[S.panel];$("detail-content").innerHTML=content;
  }
  function refresh(){
    if(!bootstrap)return;renderTimeline();
    note("");S.unit=S.unit||{kind:"pais",properties:{}};
    installSource("prov",{type:"FeatureCollection",features:overviewProps()});
    if(S.scope!=="nacional"){S.province=null;if(S.level!=="comunidad"){S.level="comunidad";$("level").value="comunidad";}}
    else if(S.level==="comunidad"&&!S.province){/* conservar nivel elegido */}
    paint();renderDetail();prepareArea();
  }
  function syncElection(){if(S.scope==="autonomico"&&!S.region){S.election="";}renderTimeline();}
  function search(q){
    const norm=normal(q);if(!norm)return;
    const p=provinceFeatures().find(x=>normal(x.properties.nombre).includes(norm)||normal(x.properties.cod)===norm);
    if(p){S.scope="nacional";updateSegments("scope",S.scope);openProvince(p.properties.cod,true);return;}
    const c=D.communities.features.find(x=>normal(x.properties.nombre).includes(norm));
    if(c){S.scope="autonomico";S.region=regionId(c.properties.nombre);updateSegments("scope",S.scope);
      S.unit={kind:"comunidad",properties:c.properties};syncElection();refresh();focus(c.geometry);return;}
    if(/^\d{10}$/.test(q)&&D.sectionsIndex?.provincias?.[q.slice(0,2)]){
      S.scope="nacional";S.level="seccion";S.province=q.slice(0,2);
      updateSegments("scope",S.scope);$("level").value="seccion";
      prepareArea().then(()=>{let f=D.sectionCache.get(S.province)?.features.find(x=>x.properties.s===q);
        if(f){focus(f.geometry);S.unit={kind:"seccion",properties:f.properties};renderDetail();}
        else note("La sección "+q+" no está en el producto INE publicado.");});
      return;
    }
    note("No se encontró ese territorio en los productos disponibles.");
  }
  function controls(){
    ["scope","system","view"].forEach(id=>document.querySelectorAll("#"+id+" button").forEach(b=>b.onclick=()=>{
      S[id==="scope"?"scope":id==="system"?"system":"view"]=b.dataset.value;
      updateSegments(id,b.dataset.value);
      if(id==="scope"){S.province=null;S.unit={kind:"pais",properties:{}};S.region="";
        S.level=S.scope==="autonomico"?"comunidad":"provincia";$("level").value=S.level;
        map.fitBounds([[-9.8,35.3],[4.5,44.2]],{padding:30,duration:350});}
      refresh();
    }));
    $("layer").onchange=e=>{S.layer=e.target.value;if(S.layer==="desviacion"&&S.view!=="territorial"){
      S.view="territorial";updateSegments("view","territorial");}
      if(S.layer==="ganador"&&S.view!=="electoral"){S.view="electoral";updateSegments("view","electoral");}
      note("");refresh();};
    $("level").onchange=e=>{S.level=e.target.value;note("");prepareArea();paint();};
    $("election-region").onchange=e=>{
      S.region=e.target.value;
      const community=D.communities?.features.find(f=>regionId(f.properties.nombre)===S.region);
      S.unit=community?{kind:"comunidad",properties:community.properties}:{kind:"pais",properties:{}};
      syncElection();refresh();
      if(community)focus(community.geometry);
    };
    $("search").addEventListener("keydown",e=>{if(e.key==="Enter")search(e.target.value);});
    ["boundaries","labels","auto-sections"].forEach(id=>$(id).onchange=()=>paint());
    document.querySelectorAll("[data-panel]").forEach(b=>b.onclick=()=>{
      S.panel=b.dataset.panel;document.querySelectorAll("[data-panel]").forEach(x=>x.setAttribute("aria-pressed",String(x===b)));renderDetail();
    });
    $("reset-map").onclick=()=>{S.province=null;S.unit={kind:"pais",properties:{}};S.level=S.scope==="nacional"?"provincia":"comunidad";$("level").value=S.level;
      map.fitBounds([[-9.8,35.3],[4.5,44.2]],{padding:30,duration:450});refresh();};
    $("peninsula").onclick=()=>map.fitBounds([[-9.8,35.6],[4.5,43.95]],{padding:25,duration:350});
    $("canarias").onclick=()=>map.fitBounds([[-18.5,27.4],[-13.3,29.5]],{padding:25,duration:350});
    $("help").onclick=()=>$("help-dialog").showModal();
  }
  async function init(){
    if(!window.maplibregl){note("No se pudo cargar la librería cartográfica MapLibre.");return;}
    controls();
    try{
      const [pr,cc,idx,sec,terr,products,calendar]=await Promise.all([
        getJson(BASE.provincias),getJson(BASE.comunidades),
        getJson(BASE.indices).catch(()=>null),getJson(BASE.secciones+"INDEX.json").catch(()=>null),
        getJson(BASE.territorial).catch(()=>null),getJson(BASE.productos).catch(()=>null),
        getJson(BASE.calendario).catch(()=>({}))
      ]);
      if(pr.type!=="FeatureCollection"||cc.type!=="FeatureCollection")throw Error("Fuentes base cartográficas inválidas");
      D.prov=pr;D.communities=cc;D.index=idx;D.sectionsIndex=sec;D.territorial=terr;D.products=products;
      D.calendar=calendar;
      $("places").innerHTML=pr.features.map(f=>"<option value='"+esc(f.properties.nombre)+"'></option>").join("")+
        cc.features.map(f=>"<option value='"+esc(f.properties.nombre)+"'></option>").join("");
      $("election-region").innerHTML='<option value="">Selecciona parlamento</option>'+
        Object.entries(REGION).map(([name,id])=>"<option value='"+esc(id)+"'>"+esc(name)+"</option>").join("");
      map=new maplibregl.Map({container:"map",style:styleInit(),bounds:[[-9.8,35.4],[4.5,44.2]],
        fitBoundsOptions:{padding:30},dragRotate:false,pitchWithRotate:false,renderWorldCopies:false,attributionControl:false});
      map.addControl(new maplibregl.NavigationControl({showCompass:false}),"top-right");
      map.on("load",()=>{bootstrap=true;install();});
      map.on("error",e=>{if(e?.error)console.error("MapLibre:",e.error);});
    }catch(e){note("No es posible inicializar V3: "+e.message);console.error(e);}
  }
  init();
})();
