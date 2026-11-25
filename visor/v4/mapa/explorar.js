/* PROYECTO: Diputado de Distrito
 * CLASE: visor V4 · Explorar (V3 completa + doble vuelta)
 * VERSIÓN: 1.6.0
 * FECHA: 2026-11-25
 * ESTADO: candidato
 * ANTERIOR: legacy/visor/v4/mapa/explorar_v1.5.0_20261125.js
 * CAMBIOS: 1.6.0 (T-500, diseño T-499 1.0.1): capa «Situación actual · puntos», activa por defecto en Congreso · 2023 · Provincia: un punto por diputado en un racimo
 *   ordenado por partido (placa en Madrid, Barcelona, Vizcaya y Tenerife; línea guía en Barcelona), provincia en el color del más votado con 4 clases de intensidad,
 *   recuadros de Canarias, Ceuta y Melilla, leyenda en el panel derecho con % sobre votos a candidaturas y ventana con la tabla de la provincia. Datos de mapa/puntos_v5_2023.json
 *   (herramientas/datos_puntos_v5.py, BOE-A-2023-18907) y disposición en mapa/puntos.js. Sin datos, vuelve a la doble vuelta.
 *   1.5.0 (T-459, diseño T-458 1.4.1 §1.3.0/1.4.0): colores fijos por bloque (#d32b2b, #1d6fb8, #0f7a52, #5b6470) en los dos temas, sin aclarado (la ventaja ajustada
 *   solo en el texto); panel con cifras de lo seleccionado arriba y sin foto/«407 / 350»; clic en distrito = resaltado + ventana (población, votos, bloque ganador y %) sin zoom;
 *   fuera nivel sección/municipio, zoom a secciones y búsqueda por CUSEC.
 *   1.4.0 (T-456): el producto autonómico se busca con la clave del visor y con el id autNN del índice (toma el más reciente; antes un M08 publicado
 *   solo bajo autNN no casaba con el run del índice y la doble vuelta caía); fuera los carteles «Doble vuelta no disponible», «Simulación sin valor oficial»,
 *   el rótulo del mapa (map-tag) y el «fuente no oficial / copia archivada» de la fila Resultados de Procedencia (el dato sigue en el calendario).
 *   1.3.0 (T-430, D-186/D-188/D-194, paso 1 de REDISENO_R2 §9): origen de los datos configurable en `mapa/datos.json`. Con
 *   `actual` vacío o sin el fichero, todo igual que en 1.2.1 (rutas relativas del sitio). Con `actual` = dirección de `web/actual/actual.json`
 *   (datos.diputadodedistrito.es), cada dato se pide en `web/actual/<ruta de hoy en el sitio>` y se comprueba su sha256 contra el índice;
 *   si no casa, se recarga el índice una vez sin caché (ventana de 60 s de «solo la vigente») y, si sigue sin casar, no se pinta y se dice.
 *   El calendario es de la web, no un dato: siempre local.
 *   1.2.1 (T-429): regla «Mayoría simple en el distrito» (antes «Más votado») y, en la ficha, línea fija sobre el trasvase de votos como hipótesis de simulación.
 *   1.2.0 (T-428, D-184): la V4 se sirve en la raíz del sitio y Explorar en /mapa/, a la misma profundidad que la V3: las rutas
 *   del sitio pasan de ../../ a ../ (las mismas que la V3); la doble vuelta sigue en datos/ junto a la página (P40 la escribe en mapa/datos/).
 *   1.1.0 (T-427): la capa «Doble vuelta» también en el ámbito «Autonómico» con la autonómica vigente de cada comunidad (índice 1.1):
 *   pinta los distritos del M08 publicado solo si su ejecución es la del índice (`run_m08`); id público = district_id interno + 1 (T-135);
 *   comunidades sin doble vuelta, con su motivo declarado. El ámbito nacional, idéntico.
 *   1.0.0: copia íntegra de v3.js 1.3.0 de la V3 (MapLibre, vista nacional, comunidad, provincia, distrito, municipio y sección
 *   censal, calendario, paletas, paneles, procedencia, galería y tabla) con rutas a ../../ y una capa electoral más, «Doble vuelta»
 *   (D-172): reglas «Tres bloques» (dv_A, por defecto), «Dos bloques» (dv_B), «Sin coaliciones» (dv_base) y «Mayoría simple en el distrito» (primero),
 *   coloreado por bloque (claro si la ventaja es < 5 puntos), ficha por distrito con primera y segunda vuelta y aviso fijo
 *   «Simulación sin valor oficial». Lee lo que deja P40 en mapa/datos/ (antes v4/mapa/datos/) (herramientas/publicar_doble_vuelta.py) y verifica sha256.
 * MOTIVO: T-423, la V4 es la portada de la autora + la V3 completa enriquecida con la doble vuelta (decisión del propietario, 19-11).
 * ANTERIOR (1.3.0): legacy/visor/v4/mapa/explorar_v1.2.1_20261122.js (1.2.1: legacy/visor/v4/mapa/explorar_v1.2.0_20261120.js; 1.2.0: legacy/visor/v4/mapa/explorar_v1.1.0_20261120.js; 1.1.0: legacy/visor/v4/mapa/explorar_v1.0.0_20261120.js) */
"use strict";
(function () {
  const BASE={provincias:"../v2/datos/provincias.json",comunidades:"../v2/datos/comunidades.json",
    indices:"../datos/INDEX.json",secciones:"../v2/datos/secciones/",territorial:"../v2/datos/territorial.json",
    productos:"../data/viewer-results.json",calendario:"calendario.json",procedencia:"../datos/catalogo_procedencia.json",dv:"datos/",puntos:"puntos_v5_2023.json"};
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
  const LOCALE_ES={"NavigationControl.ZoomIn":"Acercar","NavigationControl.ZoomOut":"Alejar","NavigationControl.ResetBearing":"Orientar al norte"};
  // T-423 (D-165): el texto visible usa la nomenclatura P; los ids de datos (M06, M08…) no cambian (T-313).
  const NOMBRE_P={M01:"P21",M02:"P22",M03:"P23",M04:"P24",M05:"P25",M06:"P26",M07:"P31",M08:"P32"};
  function textoP(t){return String(t??"").replace(/\bM0([1-8])\b/g,m=>NOMBRE_P[m]);}
  function esc(s){return String(s??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;");}
  function color(n){return PALETA[family(n)]||PALETA.OTROS;}
  function randomNeutral(n){const pal=["#91aabb","#a5bcc8","#b5c8d0","#9baac2","#c2d0da","#afbeca","#8eabb7"];let h=0;for(const ch of String(n))h=(h*31+ch.charCodeAt(0))>>>0;return pal[h%pal.length];}
  const REGLA0=(window.DV&&typeof location!=="undefined")?DV.leerEnlace(location.search).regla:"tres";
  const S={regla:REGLA0,scope:"nacional",system:"proporcional",view:"electoral",layer:"puntos",level:"provincia",election:"202307",region:"",panel:"territorio",province:null,unit:null,selected:null};
  const D={puntos:null,v5:null,prov:null,communities:null,index:null,sectionsIndex:null,territorial:null,products:null,provenance:null,calendar:{},
    districtCache:new Map(),sectionCache:new Map(),regionCache:new Map(),allDistricts:new Map(),allSections:new Map()};
  let districtBulkPromise=null, renderRevision=0;
  D.districtFailures=new Map();
  let map=null,bootstrap=false,loading=false;
  const empty=()=>({type:"FeatureCollection",features:[]});
  // ---- Doble vuelta (T-423, D-172): solo lee los CSV publicados y verificados; nunca decide ganadores.
  const REGLAS=window.DV?DV.REGLAS:[];
  const DVD={indice:null,error:"",datos:new Map(),fallos:new Map(),pend:new Map()};
  const BLOQUE0={izq:"#d32b2b",nac:"#0f7a52",pat:"#1d6fb8",sin:"#5b6470"}; // fijos en los dos temas (T-459, diseño T-458 §1)
  function dvActiva(){return S.layer==="doblevuelta";}
  // ---- Situación actual · puntos (T-500): solo pinta lo que dice mapa/puntos_v5_2023.json (BOE-A-2023-18907); la disposición es de puntos.js.
  const PT=window.PUNTOS||null;
  function puntosActiva(){return S.layer==="puntos";}
  function puntosDisp(){return !!(PT&&D.puntos);}
  const NOM5={VOX:"Vox",SUMAR:"Sumar","EAJ-PNV":"PNV",CCa:"CC"},nom5=p=>NOM5[p]||p;
  const pc1v=x=>x.toLocaleString("es-ES",{minimumFractionDigits:1,maximumFractionDigits:1})+" %";
  function toPuntos(){
    closePopup();
    S.scope="nacional";S.region="";S.province=null;S.unit={kind:"pais",properties:{}};S.system="proporcional";S.view="electoral";S.election="202307";S.level="provincia";
    updateSegments("scope","nacional");updateSegments("system","proporcional");updateSegments("view","electoral");$("level").value="provincia";
  }
  function colorProvincia(cod){
    const d=D.puntos?.provincias?.[cod];if(!d||!PT)return null;
    const g=PT.ganador(d);return PT.mezcla(PALETA[family(g.p)]||PALETA.OTROS,PT.clase(g.pct).mezcla);
  }
  function puntosCifras(cod){
    if(cod){const d=D.puntos.provincias[cod],g=PT.ganador(d);
      return [["Escaños 2023",fmt(d.escanos)],["Votos a candidaturas",fmt(d.votos_candidaturas)],["Más votado",nom5(g.p)+" · "+pc1v(g.pct)]];}
    const T=PT.totales(D.puntos);
    return [["Escaños 2023",fmt(T.escanos)],["Votos a candidaturas",fmt(T.estatal)],["Más escaños",nom5(T.lista[0].p)+" · "+T.lista[0].escanos]];
  }
  function puntosLeyenda(){
    const T=PT.totales(D.puntos),pc=v=>pc1v(100*v/T.estatal),sw=p=>"<i class='dot' style='background:"+(PALETA[family(p)]||PALETA.OTROS)+"'></i>";
    return "<h3>Congreso 2023 · situación actual</h3><p class='v5-sub'>Un punto por diputado ("+T.escanos+").</p>"+
      "<table class='v5-tab'><thead><tr><th>Partido</th><th>% voto</th><th>Escaños</th></tr></thead><tbody>"+
      T.lista.map(x=>"<tr><td>"+sw(x.p)+esc(x.p==="PSOE"?"PSOE (con PSC)":nom5(x.p))+"</td><td>"+pc(x.votos)+"</td><td>"+x.escanos+"</td></tr>").join("")+
      "<tr><td><i class='dot' style='background:"+PALETA.OTROS+"'></i>Resto (sin escaño)</td><td>"+pc(T.resto)+"</td><td>0</td></tr>"+
      "<tr class='total'><td>Total</td><td>100 %</td><td>"+T.escanos+"</td></tr></tbody></table>"+
      "<h4>Intensidad: % de voto del partido más votado en la provincia</h4><ul class='v5-esc'>"+
      PT.CLASES.map(k=>"<li><span style='background:"+PT.mezcla(PALETA.PP,k.mezcla)+"'></span>"+esc(k.texto)+"</li>").join("")+"</ul>"+
      "<small>% sobre votos a candidaturas (sin votos en blanco ni nulos). Fuente: BOE-A-2023-18907, Junta Electoral Central; sin estimaciones ni encuestas.</small>";
  }
  function puntosPopupHtml(cod){
    const d=D.puntos.provincias[cod],resto=d.votos_candidaturas-d.partidos.reduce((s,x)=>s+x.votos,0),pc=v=>pc1v(100*v/d.votos_candidaturas);
    const filas=[...d.partidos].sort((a,b)=>b.votos-a.votos);
    return "<div class='dv-popup'><strong>"+esc(d.nombre)+" · "+d.escanos+" escaños</strong><table class='v5-tab'><thead><tr><th>Partido</th><th>Votos</th><th>%</th><th>Esc.</th></tr></thead><tbody>"+
      filas.map(x=>"<tr><td>"+esc(nom5(x.p))+"</td><td>"+fmt(x.votos)+"</td><td>"+pc(x.votos)+"</td><td>"+x.escanos+"</td></tr>").join("")+
      "<tr><td>Resto</td><td>"+fmt(resto)+"</td><td>"+pc(resto)+"</td><td>0</td></tr></tbody></table><p class='small-note'>% sobre votos a candidaturas.</p></div>";
  }
  // Clic en una provincia: resalta, abre la tabla y no acerca el mapa.
  function puntosSelect(cod,lngLat){
    const f=provinceByCode(cod);if(!f||!D.puntos?.provincias?.[cod])return;
    S.unit={kind:"provincia",properties:f.properties};S.selected=cod;
    if(popup){popup.remove();popup=null;}
    if(map.getLayer("prov-sel"))map.setFilter("prov-sel",["==",["get","cod"],cod]);
    if(typeof maplibregl.Popup==="function"&&lngLat){
      popup=new maplibregl.Popup({closeButton:true,maxWidth:"300px"}).setLngLat(lngLat).setHTML(puntosPopupHtml(cod)).addTo(map);
      popup.on?.("close",()=>{popup=null;clearSel();});
    }
    renderDetail();
  }
  // Elección de la doble vuelta: generales de 2023 en el Congreso; en «Autonómico», la autonómica vigente del índice (T-427).
  function dvEleccionOk(){
    if(S.scope!=="autonomico")return S.election==="202307";
    const t=DVD.indice&&S.region?DV.entrada(DVD.indice,S.region):null;
    return !t||String(t.eleccion).replace("-","")===S.election;
  }
  function regla(){return REGLAS.find(r=>r.id===S.regla)||REGLAS[0];}
  function bloques(){return {...BLOQUE0};}
  function dvAjustada(f){if(!f||String(f.vuelta_decisiva)!=="2")return false;const a=Number(f.votos_a_2v),b=Number(f.votos_b_2v);return Math.abs(a-b)/((a+b)||1)<.05;}
  function dvExpression(){
    const c=bloques(),e=["match",["coalesce",["get","dv_"+regla().id],"nodato"]];
    for(const k of ["izq","nac","pat","sin"])e.push(k,c[k],k+"-claro",c[k]);
    e.push("#a8bac7");return e;
  }
  function dvClase(f){
    if(!f)return "nodato";
    const seg=String(f.vuelta_decisiva)==="2",a=Number(f.votos_a_2v),b=Number(f.votos_b_2v);
    const margen=seg?Math.abs(a-b)/((a+b)||1):1;
    return DV.claseBloque(f.bloque_ganador)+(margen<.05?"-claro":"");
  }
  /* T-430: origen de los datos (mapa/datos.json). ACT = {base, fich: {ruta de hoy en el sitio: sha256}} o null (rutas relativas). */
  let ACT=null;
  function claveSitio(p){return p.startsWith("../")?p.slice(3):"mapa/"+p;}
  async function cargarActual(){
    let cfg=null;
    try{const r=await fetch("datos.json",{cache:"no-cache"});if(r&&r.ok)cfg=await r.json();}catch(e){cfg=null;}
    const url=cfg&&typeof cfg.actual==="string"?cfg.actual.trim():"";
    if(!url){ACT=null;return;}
    if(!/^https:\/\/[a-z0-9.-]+\/[^?#]*actual\.json$/.test(url))throw Error("la dirección del índice de datos no es válida");
    const r=await fetch(url,{cache:"no-cache"});if(!r.ok)throw Error("índice de datos: HTTP "+r.status);
    const idx=await r.json(),fich={};
    if(!idx||idx.version_formato!==1)throw Error("formato del índice de datos desconocido");
    for(const g of [idx.comunes||{},...Object.values(idx.mapas||{})])Object.assign(fich,g.ficheros||{});
    ACT={base:url.replace(/actual\.json$/,""),fich};
  }
  async function datoBytes(p){
    const k=claveSitio(p);
    for(let intento=0;intento<2;intento++){
      const h=ACT.fich[k];if(!h)throw Error(k+": no está en el índice de datos");
      const r=await fetch(ACT.base+k,{cache:intento?"no-cache":"default"});if(!r.ok)throw Error(k+": HTTP "+r.status);
      const b=await r.arrayBuffer();if(await dvHuella(b)===h)return b;
      if(!intento)await cargarActual();  // ventana de «solo la vigente» (D-188): índice nuevo, una vez
    }
    throw Error("la huella de "+k+" no coincide con el índice de datos");
  }
  async function dvBytes(ruta){
    if(ACT)return datoBytes(BASE.dv+ruta);
    const r=await fetch(BASE.dv+ruta,{cache:"no-cache"});if(!r.ok)throw Error(ruta+": HTTP "+r.status);return r.arrayBuffer();}
  async function dvHuella(b){
    const c=globalThis.crypto;if(!(c&&c.subtle))throw Error("sin verificación de huella");
    return Array.from(new Uint8Array(await c.subtle.digest("SHA-256",b)),x=>x.toString(16).padStart(2,"0")).join("");
  }
  async function dvVerificado(f){const b=await dvBytes(f.ruta);if(await dvHuella(b)!==f.sha256)throw Error("la huella de "+f.ruta+" no coincide");return new TextDecoder("utf-8").decode(b);}
  async function loadDVIndex(){
    try{DVD.indice=DV.leerIndice(new TextDecoder("utf-8").decode(await dvBytes("INDEX.json")));}
    catch(e){DVD.indice=null;DVD.error="Aún no hay datos de doble vuelta publicados en este sitio.";}
  }
  function loadDV(key){
    if(!DVD.indice||!key)return Promise.resolve(null);
    if(DVD.datos.has(key))return Promise.resolve(DVD.datos.get(key));
    if(DVD.fallos.has(key))return Promise.resolve(null);
    const t=DV.entrada(DVD.indice,key);
    if(!t){DVD.fallos.set(key,DV.motivoSin(DVD.indice,key)||"sin doble vuelta publicada");return Promise.resolve(null);}
    if(!DVD.pend.has(key))DVD.pend.set(key,(async()=>{
      try{const [r,d]=await Promise.all([dvVerificado(t.resultados),dvVerificado(t.detalle)]);const x=DV.cargar(r,d);DVD.datos.set(key,x);return x;}
      catch(e){DVD.fallos.set(key,String(e.message||e));return null;}
      finally{DVD.pend.delete(key);}
    })());
    return DVD.pend.get(key);
  }
  function dvProps(key,d){
    const x=DVD.datos.get(key),out={};
    for(const r of REGLAS){const f=x&&x.porDistrito[String(d)]&&x.porDistrito[String(d)][r.esc];out["dv_"+r.id]=dvClase(f);}
    return out;
  }
  async function dvDecorate(fc,keyOf,distOf){
    const keys=[...new Set(fc.features.map(keyOf).filter(Boolean))];
    let next=0;async function w(){while(next<keys.length)await loadDV(keys[next++]);}
    await Promise.all(Array.from({length:Math.min(6,keys.length)},w));
    return {type:"FeatureCollection",features:fc.features.map(f=>({...f,properties:{...f.properties,...dvProps(keyOf(f),distOf(f))}}))};
  }
  let shownDistricts={features:[]};
  const NOMBRE_BLOQUE={izq:"Izquierdas",nac:"Nacionalistas",pat:"Patriotas",sin:"Sin bloque"};
  const pc1=x=>(Math.round(x*1000)/10).toFixed(1).replace(".",",")+" %";
  // Cifras de un distrito con la regla elegida: votos (suma de votos_1v de su detalle), bloque ganador y su % en la vuelta que decide.
  function dvCifras(p){
    if(!dvActiva()||!DVD.indice)return null;
    const aut=S.scope==="autonomico",key=aut?S.region:(p.identity||provinceKey(p.province)),d=aut?p.dvDistrito:p.distrito;
    const x=DVD.datos.get(key),r=REGLAS.find(q=>q.id===S.regla)||REGLAS[0],fila=x?.porDistrito?.[d]?.[r.esc],det=x?.detalle?.[d]?.[r.esc];
    if(!fila||!det)return null;
    const cuota=String(fila.vuelta_decisiva)==="2"?+fila.cuota_ganador_2v:+fila.cuota_1v;
    return {votos:det.reduce((t,q)=>t+(+q.votos_1v||0),0),bloque:fila.bloque_ganador,cuota,ajustada:dvAjustada(fila)};
  }
  function distritoCifras(p){
    const c=dvCifras(p),r=[["Población",fmt(p.population)]];
    if(c){r.push(["Votos",fmt(c.votos)],["Bloque ganador",c.bloque+" · "+pc1(c.cuota)]);if(c.ajustada)r.push(["Ventaja","Ajustada (menos de 5 puntos)"]);}
    else r.push(["Partido ganador del distrito",S.scope==="nacional"&&validElection()&&S.view==="electoral"?(p.ganador||"Sin datos electorales"):"No disponible para la elección/vista"]);
    return r;
  }
  function distritoPopup(p){
    const prov=provinceByCode(p.province)?.properties.nombre||"";
    return "<div class='dv-popup'><strong>Distrito "+esc(p.distrito)+(prov?" · "+esc(prov):"")+"</strong><dl>"+
      distritoCifras(p).map(([a,b])=>"<div><dt>"+esc(a)+"</dt><dd>"+esc(b)+"</dd></div>").join("")+"</dl></div>";
  }
  // Cifras de España o de una provincia: escaños 2023, distritos DDD, bloques ganadores con la regla y población.
  function territorioCifras(kind,pr){
    const feats=(shownDistricts.features||[]).filter(f=>kind!=="provincia"||f.properties.province===pr.cod); // los ya decorados con el bloque de cada regla
    const cont={},pop=feats.reduce((t,f)=>t+(Number(f.properties.population)||0),0);
    if(dvActiva())for(const f of feats){const k=String(f.properties["dv_"+regla().id]||"").replace("-claro","");if(k)cont[k]=(cont[k]||0)+1;}
    const bl=Object.keys(NOMBRE_BLOQUE).filter(k=>cont[k]).map(k=>NOMBRE_BLOQUE[k]+" "+cont[k]).join(" · ");
    return [["Escaños 2023",kind==="provincia"?fmt(pr.escanos):"350"],["Distritos DDD",kind==="provincia"?fmt(pr.k407):"407"],
      ["Bloques ganadores · "+regla().texto,bl||"—"],["Población",pop?fmt(pop):"—"]];
  }
  function provinceKey(cod){return getProvinceEntry(provinceByCode(cod))?.key||"";}
  function dvFicha(key,d){
    const x=DVD.datos.get(key),f=x?DV.ficha(String(d),regla().id,x):null;
    if(!f)return "";
    const sw=b=>"<span class='sw "+DV.claseBloque(b)+"' aria-hidden='true'></span>";
    const aj=f.segunda&&Math.abs(f.segunda.a.votos-f.segunda.b.votos)/((f.segunda.a.votos+f.segunda.b.votos)||1)<.05;
    let h="<p class='dv-titular'>"+esc(f.titular)+"</p>"+(aj?"<p class='dv-empate'>Ventaja ajustada: menos de 5 puntos sobre el otro finalista.</p>":"")+"<h3>1.ª vuelta</h3><p class='small-note'>"+esc(f.nota1)+"</p>"+
      "<table class='comparison-table'><thead><tr><th>Candidatura</th><th>Votos</th><th>%</th></tr></thead><tbody>"+
      f.primera.map(c=>"<tr><td>"+sw(c.bloque)+esc(c.nombre)+(c.partidos.length>1?" <span class='small-note'>("+c.partidos.map(p=>esc(p.partido)+" "+fmt(p.votos)).join(" + ")+")</span>":"")+"</td><td>"+esc(c.texto)+"</td><td>"+esc(c.pct)+"</td></tr>").join("")+"</tbody></table>";
    if(f.segunda){
      h+="<h3>Finalistas</h3><p>"+f.finalistas.map(esc).join(" y ")+"</p>";
      h+=f.transferencias?"<h3>Transferencias</h3><table class='comparison-table'><tbody>"+f.transferencias.map(t=>"<tr><td>"+esc(t.de)+"</td><td>"+(t.a?"→ "+esc(t.a):"→ abstención ("+esc(t.motivo)+")")+"</td><td>"+fmt(t.votos)+"</td></tr>").join("")+"</tbody></table>":"<p class='small-note'>Cuadro de transferencias no disponible para este distrito.</p>";
      h+="<h3>2.ª vuelta</h3><p>"+esc(f.segunda.a.nombre)+" "+fmt(f.segunda.a.votos)+" · "+esc(f.segunda.b.nombre)+" "+fmt(f.segunda.b.votos)+" · abstención "+fmt(f.segunda.abstencion)+"</p>";
    }else h+="<h3>2.ª vuelta</h3><p class='small-note'>No hay segunda vuelta en este distrito con esta regla.</p>";
    if(f.avisoEmpate)h+="<p class='dv-empate'>"+esc(f.avisoEmpate)+"</p>";
    h+="<h3>Con otra regla</h3><p class='dv-comp'>"+DV.comparacion(String(d),x).map(c=>"<button type='button' class='chip' data-regla='"+esc(c.id)+"' aria-pressed='"+(c.id===regla().id)+"'>"+sw(c.bloque)+esc(c.texto)+" → "+esc(c.ganador)+"</button>").join(" ")+"</p>";
    h+="<p class='small-note dv-hipotesis'>El trasvase de votos entre partidos del mismo bloque es una hipótesis de simulación, no un comportamiento observado.</p>";
    return h;
  }
  function setRegla(id){
    if(!REGLAS.some(r=>r.id===id))return;
    S.regla=id;updateSegments("regla",id);$("regla-ayuda").textContent=regla().ayuda;
    try{history.replaceState(null,"","?regla="+id);}catch(e){/* sin historial: sigue funcionando */}
    if(!dvActiva()){S.layer="doblevuelta";$("layer").value="doblevuelta";}
    toDV();refresh();
  }
  function toDV(){
    // Doble vuelta: distritos DDD del Congreso de 2023 o, en «Autonómico» (T-427), de la autonómica vigente; sistema mayoritario y vista electoral.
    if(S.scope==="autonomico"){S.system="mayoritario";updateSegments("system","mayoritario");S.view="electoral";updateSegments("view","electoral");return;}
    if(S.scope!=="nacional"){S.scope="nacional";S.region="";S.province=null;S.unit={kind:"pais",properties:{}};updateSegments("scope","nacional");}
    S.system="mayoritario";updateSegments("system","mayoritario");S.view="electoral";updateSegments("view","electoral");
    if(S.election!=="202307")S.election="202307";
    if(S.level==="provincia"||S.level==="comunidad"){S.level=S.province?"distrito":"provincia";$("level").value=S.level;}
  }
  async function getLocal(path){const r=await fetch(path,{cache:"default"});if(!r.ok)throw Error(path+": HTTP "+r.status);return r.json();}
  async function getJson(path){
    if(!ACT)return getLocal(path);
    return JSON.parse(new TextDecoder("utf-8").decode(await datoBytes(path)));}
  function dur(n){return typeof matchMedia==="function"&&matchMedia("(prefers-reduced-motion: reduce)").matches?0:n;}
  function announce(t){const e=$("sr-status");if(e)e.textContent=t||"";}
  function note(t){$("map-notice").textContent=t||"";}
  function legend(t){$("legend").innerHTML=t;}
  function helpText(t){$("election-note").textContent=t;}
  function bbox(geometry){let box=[180,90,-180,-90];function walk(coords){if(typeof coords[0]==="number"){box[0]=Math.min(box[0],coords[0]);box[1]=Math.min(box[1],coords[1]);box[2]=Math.max(box[2],coords[0]);box[3]=Math.max(box[3],coords[1]);}else coords.forEach(walk);}walk(geometry.coordinates||[]);return [[box[0],box[1]],[box[2],box[3]]];}
  let popup=null;
  function clearSel(){if(map?.getLayer("dist-sel"))map.setFilter("dist-sel",["==",["get","distrito"],-1]);if(map?.getLayer("prov-sel"))map.setFilter("prov-sel",["==",["get","cod"],""]);}
  function closePopup(){if(popup){popup.remove();popup=null;}clearSel();}
  // Clic en un distrito (T-459): resalta y abre la ventana; el mapa no se acerca ni cambia de nivel.
  function selectDistrict(f,lngLat){
    const p=f.properties;
    if(map.getLayer("dist-sel"))map.setFilter("dist-sel",["all",["==",["get","distrito"],p.distrito],["==",["coalesce",["get","identity"],""],p.identity??""]]);
    if(popup){popup.remove();popup=null;}
    if(typeof maplibregl.Popup!=="function"||!lngLat)return;
    popup=new maplibregl.Popup({closeButton:true,maxWidth:"280px"}).setLngLat(lngLat).setHTML(distritoPopup(p)).addTo(map);
    popup.on?.("close",()=>{popup=null;clearSel();}); // cierre con la X: también quita el resaltado
  }
  function focus(g){if(map&&g&&g.coordinates){map.fitBounds(bbox(g),{padding:65,maxZoom:12,duration:dur(420)});}}
  function updateSegments(id,val){document.querySelectorAll("#"+id+" button").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.value===val)));}
  function paletteExpression(){const e=["match",["get","party"]];Object.entries(PALETA).forEach(([k,c])=>{e.push(k,c);});e.push(PALETA.OTROS);return e;}
  function paintWith(layer,fill){if(map?.getLayer(layer))map.setPaintProperty(layer,"fill-color",fill);}
  function showLayer(id,show){if(map?.getLayer(id))map.setLayoutProperty(id,"visibility",show?"visible":"none");}
  function rows(partyColorsAvailable){
    const parties=["PP","PSOE","VOX","SUMAR","PODEMOS","EAJ-PNV","EH BILDU","ERC","JUNTS","BNG","CC","OTROS"];
    if(S.view==="electoral"&&!partyColorsAvailable){
      legend("<h3>Resultados no disponibles</h3><ul><li><i style='background:#a8bac7'></i>Sin color partidista acreditado</li></ul><small>La geometría es real. No se atribuyen ganadores de otra elección o sistema.</small>");
      return;
    }
    legend("<h3>"+(S.view==="electoral"?"Partido más votado":"Unidades territoriales")+"</h3><ul>"+
      (S.view==="electoral"?parties.map(p=>"<li><i style='background:"+PALETA[p]+"'></i>"+esc(p)+"</li>").join(""):
      "<li><i style='background:#9caebc'></i>Territorio</li><li><i style='background:#9c2733'></i>Seleccionado</li>")+"</ul>"+
      "<small>"+(S.view==="electoral"?"PP azul · PSOE rojo · VOX verde · Sumar rosa.":"Colores territoriales sin significado partidista.")+"</small>");
  }
  function validElection(){return S.scope==="nacional"&&S.election==="202307";}
  function availability(){
    if(S.scope==="autonomico"&&S.system==="proporcional"&&S.view==="electoral")
      return "Todavía no se ha publicado aquí un producto de resultados autonómicos proporcionales con cartografía para la elección seleccionada.";
    if(S.scope==="nacional"&&!validElection()&&S.view==="electoral")
      return "Elección histórica elegida. La serie existe en el repositorio, pero no está materializada aquí como capa electoral de sección/distrito V3. No se reutilizan los colores de 2023.";
    if(S.scope==="autonomico"&&S.view==="electoral"&&!S.region)
      return "Selecciona una comunidad para consultar sus resultados por distrito publicados (P32); no se mezclan resultados de parlamentos distintos.";
    if(S.scope==="autonomico"&&S.view==="electoral"&&S.region)
      return "Los resultados por distrito autonómicos (P32) no acreditan en este visor la identidad de la elección seleccionada: la cartografía se muestra neutra hasta disponer de esa correspondencia.";
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
      e=Object.entries(D.index.territorios).find(([key,v])=>candidates.some(c=>normal(key.replace(/^[a-z]+_/,""))===c));}
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
      const devs=D.territorial?.provincias?.[p.cod]?.distritos||[];
      const deviation=devs.length?Math.max(...devs.map(d=>Math.abs(Number(d.dev)))):null;
      return {...x,properties:{...p,party:family(S.system==="mayoritario"?winner:p.ganador),
        population:pop||null,...(deviation===null?{}:{deviation}),dominant:winner,...(colorProvincia(p.cod)?{v5color:colorProvincia(p.cod)}:{})}};
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
    map.addLayer({id:"dist-sel",type:"line",source:"distritos",filter:["==",["get","distrito"],-1],paint:{"line-color":"#111","line-width":3.2}});
    map.addLayer({id:"sec-fill",type:"fill",source:"secciones",paint:{"fill-color":paletteExpression(),"fill-opacity":.82}});
    map.addLayer({id:"sec-line",type:"line",source:"secciones",paint:{"line-color":"#fff","line-width":.45}});
    map.addLayer({id:"prov-sel",type:"line",source:"prov",filter:["==",["get","cod"],""],paint:{"line-color":"#111","line-width":2.6}});
    installPuntos();
    map.on("click",e=>{
      const visible=["dist-fill","prov-fill","ccaa-fill"].filter(id=>map.getLayoutProperty(id,"visibility")!=="none");
      const hits=map.queryRenderedFeatures(e.point,{layers:visible});
      if(!hits.length){closePopup();return;}
      const f=hits[0],p=f.properties;
      if(f.layer.id==="dist-fill"){
        if(p.province)S.province=p.province;
        S.unit={kind:"distrito",properties:p};S.selected=p.distrito||p.id;
        S.level="distrito";$("level").value="distrito";selectDistrict(f,e.lngLat);renderDetail();return;}
      if(f.layer.id==="prov-fill"){if(puntosActiva())puntosSelect(p.cod,e.lngLat);else openProvince(p.cod,true);return;}
      if(f.layer.id==="ccaa-fill"){S.region=regionId(p.nombre);$("election-region").value=S.region;
        S.unit={kind:"comunidad",properties:p};S.selected=p.cod;syncElection();focus(f.geometry);refresh();return;}
    });
    if(typeof document.addEventListener==="function")document.addEventListener("keydown",e=>{if(e.key==="Escape")closePopup();});
    document.body.dataset.ready="1";
    refresh();
    if(D.puntosError)note(D.puntosError);
  }
  // Capas de la situación actual: puntos (racimo nacional y, al acercar, el de cerca), placas, líneas guía, marco de Canarias y rótulos.
  const V5CAPAS=["v5-placa-fill","v5-placa-line","v5-guia","v5-guia-pt","v5-marco","v5-n","v5-c"];
  const fc5=features=>({type:"FeatureCollection",features});
  function v5Datos(L,ini){
    if(ini)D.v5={puntos:[],placas:[],guias:[],cerca:false};
    D.v5.puntos.push(...L.puntos.map(q=>({type:"Feature",properties:{lay:q.lay,c:PALETA[q.p]||PALETA.OTROS,n:q.nombre,partido:q.partido},geometry:{type:"Point",coordinates:[q.lng,q.lat]}})));
    D.v5.placas.push(...L.placas.map(q=>({type:"Feature",properties:{lay:q.lay},geometry:{type:"Polygon",coordinates:[q.anillo]}})));
    D.v5.guias.push(...L.guias.flatMap(q=>[{type:"Feature",properties:{lay:q.lay},geometry:{type:"LineString",coordinates:[q.desde,q.hasta]}},{type:"Feature",properties:{lay:q.lay},geometry:{type:"Point",coordinates:q.desde}}]));
    installSource("v5pts",fc5(D.v5.puntos));installSource("v5placas",fc5(D.v5.placas));installSource("v5guias",fc5(D.v5.guias));
    document.body.dataset.puntos=String(D.v5.puntos.filter(q=>q.properties.lay==="n").length);
  }
  function installPuntos(){
    if(!puntosDisp())return;
    const L=PT.disponer(D.prov,D.puntos,family,["n"]);
    v5Datos(L,true);
    installSource("v5marco",fc5(L.marcoCanarias?[{type:"Feature",properties:{},geometry:{type:"LineString",coordinates:L.marcoCanarias}}]:[]));
    const z=PT.ZC,filtro=l=>["==",["get","lay"],l],oculto={layout:{visibility:"none"}};
    map.addLayer({id:"v5-placa-fill",type:"fill",source:"v5placas",filter:filtro("n"),maxzoom:z,...oculto,paint:{"fill-color":"#ffffff","fill-opacity":.85}});
    map.addLayer({id:"v5-placa-line",type:"line",source:"v5placas",filter:filtro("n"),maxzoom:z,...oculto,paint:{"line-color":"#3a4652","line-width":.8}});
    map.addLayer({id:"v5-guia",type:"line",source:"v5guias",filter:["all",filtro("n"),["==",["geometry-type"],"LineString"]],maxzoom:z,...oculto,paint:{"line-color":"#3a4652","line-width":1}});
    map.addLayer({id:"v5-guia-pt",type:"circle",source:"v5guias",filter:["all",filtro("n"),["==",["geometry-type"],"Point"]],maxzoom:z,...oculto,paint:{"circle-radius":2,"circle-color":"#3a4652"}});
    map.addLayer({id:"v5-marco",type:"line",source:"v5marco",maxzoom:z,...oculto,paint:{"line-color":"#5b6470","line-width":1,"line-dasharray":[4,3]}});
    const borde={"circle-color":["get","c"],"circle-opacity":.98,"circle-stroke-color":"#ffffff","circle-stroke-width":1.1};
    map.addLayer({id:"v5-n",type:"circle",source:"v5pts",filter:filtro("n"),maxzoom:z,...oculto,
      paint:{...borde,"circle-radius":["interpolate",["linear"],["zoom"],3.5,1.4,4.5,2.8,5.3,4.1,z,5.6]}});
    map.addLayer({id:"v5-c",type:"circle",source:"v5pts",filter:filtro("c"),minzoom:z,...oculto,
      paint:{...borde,"circle-radius":["interpolate",["linear"],["zoom"],z,5.6,8,9,10,12,13,16]}});
    D.v5.marcas=[];
    if(typeof maplibregl.Marker==="function"&&typeof document.createElement==="function"){
      const marca=(html,cls,lng,lat,anchor)=>{const el=document.createElement("div");el.className=cls;el.innerHTML=html;
        D.v5.marcas.push(new maplibregl.Marker({element:el,anchor}).setLngLat([lng,lat]).addTo(map));};
      for(const q of L.etiquetas)marca(esc(q.texto),"v5-lbl",q.lng,q.lat,"bottom");
      if(L.marcoCanarias)marca("Canarias","v5-lbl v5-can",L.marcoCanarias[0][0],L.marcoCanarias[0][1],"top-left");
      const rec=["51","52"].map(c=>{const f=provinceByCode(c),d=D.puntos.provincias[c];if(!f||!d)return "";
        const g=PT.ganador(d),col=PALETA[family(g.p)]||PALETA.OTROS;
        return "<div class='v5-rb'><b>"+esc(d.nombre)+" · "+Math.round(g.pct)+" %</b><svg viewBox='0 0 92 74' width='92' height='74' role='img' aria-label='"+esc(d.nombre+", ampliada ×8")+"'><path d='"+PT.recuadro(f)+
          "' fill='"+colorProvincia(c)+"' fill-opacity='.88' stroke='#fff'/><circle cx='46' cy='40' r='4.1' fill='"+col+"' stroke='#fff' stroke-width='1.1'/></svg></div>";}).join("");
      marca(rec,"v5-rec",-7.3,36.25,"top-left");
    }
    map.on("zoom",v5Zoom);
  }
  // Al acercar se pasa al racimo de cerca (se calcula la primera vez que hace falta); placas, rótulos y recuadros solo en la vista nacional.
  function v5Zoom(){
    if(!puntosDisp()||!D.v5||!map)return;
    if(!D.v5.cerca&&map.getZoom()>=PT.ZC-.5){D.v5.cerca=true;v5Datos(PT.disponer(D.prov,D.puntos,family,["c"]),false);}
    v5Marcas();
  }
  function v5Marcas(){
    const on=puntosActiva()&&S.scope==="nacional"&&(map.getZoom()<PT.ZC);
    for(const m of D.v5?.marcas||[])if(m.getElement)m.getElement().style.display=on?"":"none";
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
      const gp=g.properties||{};
      return {...g,properties:{...gp,province:cod,provinceName:f.properties.nombre,distrito:d,
        party:m?family(m.ganador):"OTROS",ganador:m?.ganador||"",
        population:gp.district_pop??m?.poblacion??null,
        deviation:gp.relative_deviation??null,
        neutralColor:randomNeutral(cod+":"+d),
        sections:gp.section_count??m?.secciones??null,
        municipios:gp.municipality_count??m?.municipios??null,
        run_id:e.data.run_id,identity:e.key}};
    });
    const fc={type:"FeatureCollection",features};
    D.districtCache.set(cod,fc);return fc;
  }
  async function loadNationalDistricts(){
    if(!districtBulkPromise){
      districtBulkPromise=(async()=>{
        const pending=provinceFeatures().filter(p=>
          !D.allDistricts.has(p.properties.cod)&&!D.districtFailures.has(p.properties.cod));
        let next=0,done=0;
        async function worker(){
          while(next<pending.length){
            const p=pending[next++];
            try{D.allDistricts.set(p.properties.cod,await loadDistricts(p));}
            catch(e){D.districtFailures.set(p.properties.cod,String(e.message||e));}
            done++;
            if(S.scope==="nacional"&&S.system==="mayoritario"&&!S.province&&pending.length)
              $("map-caption").textContent="Cargando distritos DDD: "+done+"/"+pending.length+" provincias";
          }
        }
        await Promise.all(Array.from({length:Math.min(5,pending.length)},worker));
      })().finally(()=>{districtBulkPromise=null;});
    }
    await districtBulkPromise;
    return {type:"FeatureCollection",features:Array.from(D.allDistricts.values()).flatMap(fc=>fc.features)};
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
  async function loadAutonomic(region,view){
    if(!region)return {collection:empty(),product:null};
    const cacheKey=region+":"+view;
    if(D.regionCache.has(cacheKey))return D.regionCache.get(cacheKey);
    const items=D.products?.results||[];
    const kind=view==="electoral"?"canonical_m08":"canonical_m06";
    const aid=window.DV&&DVD.indice?(DV.entrada(DVD.indice,region)||{}).id||((DVD.indice.sin_doble_vuelta||[]).find(x=>x.clave_visor===region)||{}).id:null;
    const mine=items.filter(x=>x.territory_id===region||(aid&&x.territory_id===aid));
    let product=newest(mine,kind);
    if(!product&&kind==="canonical_m08")product=newest(mine,"canonical_m06");
    if(!product)return {collection:empty(),product:null};
    const raw=await getJson("../"+product.viewer_path);
    if(raw.type!=="FeatureCollection"||!Array.isArray(raw.features))
      throw Error("Producto territorial inválido "+product.id);
    const collection={type:"FeatureCollection",features:raw.features.map((x,i)=>{
      const p=x.properties||{},winner=p.winner_party||p.ganador||p.winner||"";
      const id=p.distrito??p.district_id??i+1;
      return {...x,properties:{...p,distrito:id,party:family(winner),ganador:winner,
        population:p.population??p.district_pop??p.poblacion??null,region,run_id:product.run_id,
        dvDistrito:p.district_id!=null&&p.district_id!==""?Number(p.district_id)+1:Number(id),
        neutralColor:randomNeutral(region+":"+id)}};
    })};
    const result={collection,product};
    D.regionCache.set(cacheKey,result);
    return result;
  }
  async function prepareArea(){
    if(!map||!bootstrap)return;
    // Solo la última selección puede mutar las fuentes del mapa.
    const revision=++renderRevision;
    const {scope,system,view,region,province,level}=S;
    let districts=empty(),sections=empty(),product=null;
    const faults=[];
    if(scope==="autonomico"&&system==="mayoritario"&&region){
      try{({collection:districts,product}=await loadAutonomic(region,view));}
      catch(e){faults.push("No se ha podido cargar el territorio autonómico: "+e.message);}
    }else if(scope==="nacional"&&system==="mayoritario"&&!province){
      try{districts=await loadNationalDistricts();}
      catch(e){faults.push("No se ha podido cargar el mapa nacional: "+e.message);}
      if(D.districtFailures.size)faults.push("Provincias sin distrito certificado: "+
        [...D.districtFailures.keys()].map(code=>provinceByCode(code)?.properties.nombre||code).join(", "));
    }else if(scope==="nacional"&&province&&
        (level==="distrito"||level==="seccion"||level==="municipio"||system==="mayoritario")){
      const f=provinceByCode(province);
      try{districts=await loadDistricts(f);}
      catch(e){faults.push("Sin distritos acreditados para esta provincia: "+e.message);}
    }
    if(scope==="nacional"&&province&&(level==="seccion"||level==="municipio")){
      try{sections=await loadSections(provinceByCode(province));}
      catch(e){faults.push("Sin secciones INE publicadas: "+e.message);}
    }
    if(dvActiva()&&DVD.indice&&scope==="autonomico"&&region&&districts.features.length){
      const t=DV.entrada(DVD.indice,region);
      if(t&&product&&String(product.run_id)!==String(t.run_m08)){DVD.fallos.set(region,"el mapa publicado (ejecución "+product.run_id+") no es el de la doble vuelta ("+t.run_m08+")");}
      else districts=await dvDecorate(districts,()=>region,f=>f.properties.dvDistrito);
    }
    if(dvActiva()&&DVD.indice&&scope==="nacional"){
      if(districts.features.length)districts=await dvDecorate(districts,f=>f.properties.identity,f=>f.properties.distrito);
      if(sections.features.length)sections=await dvDecorate(sections,f=>provinceKey(f.properties.province),f=>f.properties.parentDistrict);
    }
    if(revision!==renderRevision)return;
    shownDistricts=districts;
    installSource("distritos",districts);
    installSource("secciones",sections);
    document.body.dataset.distritos=String(districts.features.length);document.body.dataset.secciones=String(sections.features.length);
    if(product)$("source-label").textContent=textoP(product.label||"Producto certificado P26 / resultados P32")+
      " · "+(product.certification_status||"sin certificación")+
      " · ejecución "+product.run_id;
    paint();renderDetail();
    if(faults.length)note([D.puntosError,...faults].filter(Boolean).join(" "));
  }

  function paint(){
    if(!bootstrap)return;
    const isN=S.scope==="nacional",isElect=S.view==="electoral",good=validElection();
    const showC=!isN||S.level==="comunidad";
    const showS=isN&&S.province&&(S.level==="seccion"||S.level==="municipio")&&D.sectionsIndex?.provincias?.[S.province];
    const showD=(isN&&S.system==="mayoritario"&&(!!S.province||D.allDistricts.size>0))
     ||(!isN&&S.system==="mayoritario"&&!!S.region);
    const pt=puntosActiva()&&isN&&puntosDisp();
    for(const id of V5CAPAS)showLayer(id,pt);showLayer("prov-sel",pt);
    if(D.v5)v5Marcas();
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
    const devColor=["case",["has","deviation"],
      ["interpolate",["linear"],["abs",["to-number",["get","deviation"],0]],0,"#dcebdc",.12,"#c2d4b4",.25,"#f3cb84",.6,"#b64c53"],neutral];
    function thematic(base){if(S.layer==="poblacion")return popColor;if(S.layer==="desviacion")return devColor;
      if(S.layer==="unidades")return ["coalesce",["get","neutralColor"],neutral];return base;}
    const dvAut=dvActiva()&&!isN&&isElect&&S.system==="mayoritario"&&!!S.region&&DVD.datos.has(S.region)&&dvEleccionOk();
    const dv=dvActiva()&&(permitColors||dvAut)&&DVD.indice?dvExpression():null;
    paintWith("prov-fill",pt?["coalesce",["get","v5color"],neutral]:dvActiva()?neutral:thematic(permitColors?party:neutral));
    paintWith("dist-fill",dv||thematic(permitColors?party:S.view==="territorial"?["coalesce",["get","neutralColor"],neutral]:neutral));
    const secPop=["interpolate",["linear"],["to-number",["get","p"],0],0,"#eff6f9",500,"#bbd6df",2000,"#497e9b",5000,"#193f61"];
    const secTerr=["coalesce",["get","territorialColor"],neutral];
    paintWith("sec-fill",S.layer==="poblacion"?secPop:
      (S.layer==="desviacion"?neutral:S.view==="territorial"?secTerr:
      (dv&&isN?dv:permitColors&&isN&&S.system==="mayoritario"&&!dvActiva()?party:neutral)));
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
    const partyVisible=permitColors&&S.layer==="ganador"&&
      (!showS||S.system==="mayoritario");
    rows(partyVisible);
    if(S.layer==="poblacion"||S.layer==="desviacion"){
      legend("<h3>"+(S.layer==="poblacion"?"Población":"Desviación de población")+"</h3><div style='height:12px;background:linear-gradient(90deg,#dcebdc,#f3cb84,#b64c53);border-radius:6px'></div><small>Capa basada en la población del producto certificado (P26), donde está publicada; no representa partidos.</small>");
    }
    if(dvActiva()){
      const c=bloques();
      legend("<h3>Doble vuelta · "+esc(regla().texto)+"</h3>"+(dv?"<ul>"+[["izq","Izquierdas"],["nac","Nacionalistas"],["pat","Patriotas"],["sin","Sin bloque"]].map(([k,n])=>"<li><i style='background:"+c[k]+"'></i>"+n+"</li>").join("")+
        "<li><i style='background:#a8bac7'></i>Sin dato</li></ul><small>La ventaja ajustada (menos de 5 puntos sobre el otro finalista) y los empates se indican en el texto de la ficha.</small>":""));
    }
    $("v5-mode").hidden=!pt;$("v5-content").innerHTML=pt?puntosLeyenda():"";
    if(pt)legend("");  // la leyenda de la situación actual va en el panel derecho (T-499 §3), no tapa el mapa
    if(showS)legend($("legend").innerHTML+"<small><b>Importante:</b> la geometría es de la sección censal INE; el color electoral, cuando exista, es heredado del distrito DDD, no de un escrutinio propio de la sección.</small>");
    const caption=S.scope==="nacional"?
      (S.view==="territorial"?"Geometrías territoriales DDD / INE":
       good?(pt?"Situación actual · generales de 2023 · un punto por diputado":dvActiva()?"Doble vuelta · "+regla().texto+" · generales de 2023 · simulación":S.system==="mayoritario"?"Ganador por distrito DDD · generales de 2023":"Partido más votado por provincia · generales de 2023"):"Sin capa electoral certificada para la fecha elegida"):
      (S.system==="mayoritario"?(dvAut?"Doble vuelta · "+regla().texto+" · autonómicas · "+regionName(S.region)+" · simulación":"Distritos autonómicos publicados · "+regionName(S.region)):"Comunidades autónomas · cartografía");
    $("map-caption").textContent=caption;
  }
  function findDistrict(d){return D.districtCache.get(S.province)?.features.find(x=>Number(x.properties.distrito)===Number(d));}
  function openProvince(cod,move){
    const f=provinceByCode(cod);if(!f)return;
    if(puntosActiva()){const b=bbox(f.geometry);puntosSelect(cod,{lng:(b[0][0]+b[1][0])/2,lat:(b[0][1]+b[1][1])/2});if(move)focus(f.geometry);return;}
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
      b.onclick=()=>{S.election=id;if(dvActiva()&&!dvEleccionOk()||puntosActiva()&&id!=="202307"){S.layer="ganador";$("layer").value="ganador";}renderTimeline();note("");refresh();};
      container.appendChild(b);
    });
    const pn=$("padron-note");if(pn)pn.hidden=!(S.scope==="nacional"&&String(S.election).startsWith("2026"));
    helpText(auto?"Calendario derivado de las ediciones históricas almacenadas; el mapa solo usa el producto acreditado disponible.":"Histórico documentado en el repositorio. Mapa electoral detallado disponible para 2023.");
  }
  function compareModels(){
    if(S.scope!=="nacional"||!validElection()||!D.index?.territorios)
      return "<p class='small-note'>Comparación electoral no disponible para este parlamento o elección. No se mezclan convocatorias.</p>";
    const selected=S.province?provinceByCode(S.province):null;
    const subset=selected?[selected]:provinceFeatures();
    const official={},proposed={};
    for(const f of subset){
      const p=f.properties;
      for(const [name,seats]of Object.entries(p.esc||{})){
        const party=family(name);official[party]=(official[party]||0)+Number(seats);
      }
      for(const district of (getProvinceEntry(f)?.data.distritos||[])){
        const party=family(district.ganador);proposed[party]=(proposed[party]||0)+1;
      }
    }
    const parties=[...new Set([...Object.keys(official),...Object.keys(proposed)])]
      .sort((a,b)=>(proposed[b]||0)-(proposed[a]||0)||(official[b]||0)-(official[a]||0));
    const actual=Object.values(official).reduce((a,b)=>a+b,0);
    const ddd=Object.values(proposed).reduce((a,b)=>a+b,0);
    return "<p class='small-note'>"+esc(selected?selected.properties.nombre:"España")+
      " · Elecciones generales de julio de 2023 · reparto proporcional oficial frente a ganadores por distrito DDD.</p>"+
      "<table class='comparison-table'><thead><tr><th>Partido</th><th>Actual</th><th>DDD</th></tr></thead><tbody>"+
      parties.map(p=>"<tr><td><i style='background:"+PALETA[p]+"'></i>"+esc(p)+"</td><td>"+
        fmt(official[p]||0)+"</td><td><strong>"+fmt(proposed[p]||0)+"</strong></td></tr>").join("")+
      "<tr class='total'><td>Total</td><td>"+fmt(actual)+"</td><td>"+fmt(ddd)+"</td></tr></tbody></table>"+
      "<p class='small-note'>DDD: un escaño para el partido más votado en cada distrito (resultados P32). No es el reparto proporcional oficial.</p>";
  }
  function provenanceHtml(kind,obj){
    const aviso=t=>"<p class='small-note'>"+esc(t)+"</p>";
    const cat=D.provenance;
    if(kind==="pais")return aviso("Selecciona una provincia, comunidad, distrito o sección para ver de dónde sale su mapa.");
    if(!cat?.territorios)return aviso("Procedencia no disponible: el catálogo de procedencia no está publicado. No se muestran fuentes sin acreditar.");
    let key=null;
    if(S.scope==="autonomico"||kind==="comunidad")key=S.scope==="autonomico"&&S.region?S.region:regionId(obj.nombre||"");
    else key=getProvinceEntry(selectedProvince())?.key||null;
    const t=key&&cat.territorios[key];
    if(!t)return aviso("Procedencia no disponible para esta selección en el catálogo publicado.");
    const prefix=S.election.slice(0,4)+"-"+S.election.slice(4,6);
    const vig=(t.productos||[]).filter(p=>p.vigente&&String(p.eleccion||"").startsWith(prefix));
    const want=S.view==="electoral"?["M08","M06"]:["M06","M08"];
    const prod=want.map(k=>vig.find(p=>p.producto===k)).find(Boolean);
    if(!prod)return aviso("Sin producto vigente en el catálogo de procedencia para la elección seleccionada.");
    const safe=u=>/^https?:\/\//.test(String(u||""))?String(u):null;
    const link=(label,u)=>safe(u)?"<a href='"+esc(safe(u))+"' target='_blank' rel='noopener noreferrer'>"+esc(label)+"</a>":esc(label);
    const fo=cat.fuentes_oficiales||{},ft=t.fuente_territorial||{};
    const elDate=prod.eleccion||"";
    const res=(fo.resultados_electorales||{})[elDate];
    const rows=[];
    const pad=fo.poblacion_por_sexo_y_edad;
    rows.push(["Padrón"+(ft.population_year?" "+ft.population_year:""),pad?link((pad.proveedor||"Fuente oficial"),pad.url):"No consta"]);
    const sec=fo.secciones_censales;
    rows.push(["Seccionado"+(ft.section_year?" "+ft.section_year:""),sec?link((sec.proveedor||"Fuente oficial"),sec.url):"No consta"]);
    rows.push(["Resultados "+(elDate?elDate.slice(0,4):""),res?link(String(res.proveedor||"Fuente oficial").replace(/:\s*copia archivada.*$/i,""),res.url):"No consta en el catálogo"]);
    rows.push(["Huella sha256",prod.sha256?String(prod.sha256).slice(0,12)+"…":"No consta"]);
    rows.push(["Motor Deslinde (versión actual)",cat.motor?.nombre?cat.motor.nombre+(cat.motor.version?" "+cat.motor.version:"")+" (no necesariamente la de este mapa)":"No consta"]);
    rows.push(["Elección",elDate?elDate+(prod.eleccion_declarada===false?" (por defecto)":""):"No consta"]);
    rows.push(["Fecha de generación",prod.generado||"No consta en el catálogo"]);
    return "<div class='context'><dl>"+rows.map(([a,b])=>"<div><dt>"+esc(a)+"</dt><dd>"+(/^<a /.test(b)?b:esc(b))+"</dd></div>").join("")+"</dl></div>";
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
    const records=[];
    if(kind==="provincia"){
      const pr=selectedProvince()?.properties||obj;
      records.push(...(puntosActiva()&&puntosDisp()&&D.puntos.provincias[pr.cod]?puntosCifras(pr.cod):S.scope==="nacional"?territorioCifras("provincia",pr):[["Escaños proporcionales 2023",fmt(pr.escanos)],["Distritos propuestos DDD",fmt(pr.k407)]]));
      if(!validElection())records.push(["Resultados de "+S.election,"Sin capa electoral certificada para esta fecha"]);
    }else if(kind==="distrito"){
      records.push(...distritoCifras(obj));
    }else if(kind==="comunidad"){
      records.push(["Territorio",obj.nombre],["Modelo consultado",S.system==="mayoritario"?"Distritos uninominales":"Proporcional"]);
    }else if(S.scope==="nacional")records.push(...(puntosActiva()&&puntosDisp()?puntosCifras(null):territorioCifras("pais")));
    else records.push(["Ámbito","Parlamentos autonómicos"],["Escaños actuales",SEATS[S.region]??"—"],["Sistema",S.system==="mayoritario"?"Mayoritario DDD":"Proporcional actual"],["Vista",S.view]);
    $("context").innerHTML="<dl>"+records.map(([a,b])=>"<div><dt>"+esc(a)+"</dt><dd>"+esc(b)+"</dd></div>").join("")+"</dl>";
    const source=kind==="distrito"?"Producto certificado P26 publicado; resultado P32 solo para elección acreditada · "+(obj.run_id||"sin identidad de producto"):
      kind==="provincia"?(validElection()?"Resultados oficiales generales 2023 / catálogo DDD":"Cartografía DDD · capa electoral histórica no disponible"):
        "Productos del registro durable de DDD";
    $("source-label").textContent=source;
    let content="";
    if(S.panel==="territorio")content="<p class='small-note'>Selecciona cualquier territorio en el mapa. Al pulsar un distrito se abre su ventana con población, votos y bloque ganador.</p>";
    if(S.panel==="resultados"){
      const data=kind==="provincia"&&validElection()&&S.scope==="nacional"?(selectedProvince()?.properties||obj).esc:null;
      const winner=kind==="distrito"&&S.scope==="nacional"&&S.view==="electoral"&&validElection()&&obj.ganador?obj.ganador:null;
      if(data){const entries=Object.entries(data).sort((a,b)=>b[1]-a[1]);const max=Math.max(1,...entries.map(x=>x[1]));
        content=entries.map(([p,n])=>"<div class='party-row'><b>"+esc(p)+"</b><div class='track'><b style='width:"+(n/max*100)+"%;background:"+color(p)+"'></b></div><strong>"+fmt(n)+"</strong></div>").join("")+
          "<p class='small-note'>Escaños oficiales de esta provincia en el Congreso de 2023.</p>";}
      else content=winner?"<p>Ganador acreditado (P32): <b style='color:"+color(winner)+"'>"+esc(winner)+"</b></p>":
          "<p class='small-note'>No existe aquí un desglose electoral detallado acreditado para esta selección y fecha.</p>";
    }
    if(S.panel==="comparar")content=compareModels();
    if(S.panel==="evolucion")content="<p class='small-note'>Elige elecciones en el navegador inferior. La comparación temporal de una sección exige acreditar la identidad y geometría equivalentes; no se dibujan series ficticias.</p>";
    const headings={territorio:"Perfil territorial",resultados:"Resultados electorales",comparar:"Comparar sistemas",evolucion:"Evolución temporal"};
    $("detail-heading").textContent=headings[S.panel];$("detail-content").innerHTML=content;
    $("prov-content").innerHTML=provenanceHtml(kind,obj);
    const aut=S.scope==="autonomico";
    const dvBox=$("dv-mode"),dvDist=aut?(kind==="distrito"?obj.dvDistrito:null):kind==="distrito"?obj.distrito:kind==="seccion"?(obj.parentDistrict??obj.d):null;
    const dvKey=aut?S.region:kind==="distrito"?(obj.identity||provinceKey(obj.province)):kind==="seccion"?provinceKey(obj.province):"";
    dvBox.hidden=!(dvActiva()&&dvDist!=null&&(S.scope==="nacional"||(aut&&!!S.region)));
    const dvHtml=dvBox.hidden?"":dvFicha(dvKey,dvDist);
    if(!dvHtml)dvBox.hidden=true;
    if(!dvBox.hidden){
      $("dv-heading").textContent="Doble vuelta · distrito "+dvDist+" · "+regla().texto;
      const te=aut&&DVD.indice?DV.entrada(DVD.indice,dvKey):null;
      $("dv-content").innerHTML=(te?"<p class='small-note'>Elecciones autonómicas de "+esc(te.eleccion.split("-").reverse().join("/"))+
        (te.nivel==="municipio"?" · votos por municipio repartidos a sus secciones según la población":te.aproximado_en_distrito?" · algunas secciones nuevas se asignan al distrito más cercano":"")+"</p>":"")+dvHtml;
      $("dv-content").querySelectorAll?.(".chip").forEach(b=>{b.onclick=()=>setRegla(b.dataset.regla);});
    }else $("dv-content").innerHTML="";
    renderTable();
    announce($("selection-type").textContent+": "+name+". "+$("selection-path").textContent+". "+
      records.map(([a,b])=>a+": "+b).join(". "));
  }
  function renderTable(){
    const box=$("results-table");if(!box)return;
    const prov=provinceFeatures();
    if(S.scope!=="nacional"||!prov.length){box.dataset.key="";box.innerHTML="<p class='small-note'>La tabla de provincias está disponible en el ámbito nacional.</p>";return;}
    const ok=validElection()&&S.view==="electoral";
    const key=S.scope+"|"+ok;if(box.dataset.key===key&&box.innerHTML)return; // no recrear la tabla al seleccionar: conserva el foco
    box.dataset.key=key;
    const head=ok?"<tr><th scope='col'>Provincia</th><th scope='col'>Partido más votado</th><th scope='col'>% del ganador</th><th scope='col'>Escaños</th></tr>":
      "<tr><th scope='col'>Provincia</th><th scope='col'>Escaños</th><th scope='col'>Distritos DDD</th></tr>";
    const body=prov.map(f=>{const p=f.properties;
      const btn="<button type='button' data-prov='"+esc(p.cod)+"'>"+esc(p.nombre)+"</button>";
      return ok?"<tr><th scope='row'>"+btn+"</th><td><i style='background:"+color(p.ganador)+"'></i>"+esc(p.ganador||"—")+"</td><td>"+esc(pct(p.pct))+"</td><td>"+esc(fmt(p.escanos))+"</td></tr>":
        "<tr><th scope='row'>"+btn+"</th><td>"+esc(fmt(p.escanos))+"</td><td>"+esc(fmt(p.k407))+"</td></tr>";}).join("");
    box.innerHTML="<table><caption>"+(ok?"Resultados generales 2023 por provincia":"Provincias (sin capa electoral certificada para esta vista)")+"</caption><thead>"+head+"</thead><tbody>"+body+"</tbody></table>";
    if(box.querySelectorAll)box.querySelectorAll("button[data-prov]").forEach(b=>{b.onclick=()=>openProvince(b.dataset.prov,true);});
  }
  function syncLevels(){
    const auto=S.scope==="autonomico";
    for(const option of $("level").options||[]){
      const unavailable=auto&&option.value==="provincia";
      option.disabled=unavailable;
      if(unavailable)option.title="Capa autonómica a este nivel todavía no publicada";
      else option.removeAttribute?.("title");
    }
    if(auto&&!["comunidad","distrito"].includes(S.level)){
      S.level="comunidad";$("level").value=S.level;
    }
    $("tools-note").textContent=puntosActiva()?"Situación actual: los 350 escaños oficiales del Congreso de 2023, un punto por diputado, sobre la provincia coloreada por su partido más votado.":auto?
      "Ámbito autonómico: distritos certificados (P26) publicados; la capa autonómica provincial aún no está publicada.":
      "El color de cada distrito es el del bloque que gana con la regla elegida; la ventaja ajustada se indica solo en el texto.";
  }
  function refresh(){
    if(!bootstrap)return;renderTimeline();
    note("");S.unit=S.unit||{kind:"pais",properties:{}};
    installSource("prov",{type:"FeatureCollection",features:overviewProps()});
    if(S.scope!=="nacional")S.province=null;
    syncLevels();
    paint();renderDetail();prepareArea();
  }
  function syncElection(){if(S.scope==="autonomico"&&!S.region){S.election="";}renderTimeline();}
  function search(q){
    const norm=normal(q);if(!norm)return;
    const p=provinceFeatures().find(x=>normal(x.properties.nombre).includes(norm)||normal(x.properties.cod)===norm);
    if(p){S.scope="nacional";updateSegments("scope",S.scope);openProvince(p.properties.cod,true);return;}
    const c=D.communities.features.find(x=>normal(x.properties.nombre).includes(norm));
    if(c){if(puntosActiva()){S.layer="ganador";$("layer").value="ganador";}S.scope="autonomico";S.region=regionId(c.properties.nombre);updateSegments("scope",S.scope);
      S.unit={kind:"comunidad",properties:c.properties};syncElection();refresh();focus(c.geometry);return;}
    note("No se encontró ese territorio en los productos disponibles.");
  }
  function controls(){
    ["scope","system","view"].forEach(id=>document.querySelectorAll("#"+id+" button").forEach(b=>b.onclick=()=>{
      S[id==="scope"?"scope":id==="system"?"system":"view"]=b.dataset.value;
      updateSegments(id,b.dataset.value);
      if(dvActiva()&&(S.system!=="mayoritario"||S.view!=="electoral")){S.layer="ganador";$("layer").value="ganador";}
      if(puntosActiva()&&(S.scope!=="nacional"||S.system!=="proporcional"||S.view!=="electoral")){S.layer="ganador";$("layer").value="ganador";}
      if(id==="view"&&b.dataset.value==="territorial"&&S.layer==="ganador"){
        S.layer="desviacion";$("layer").value=S.layer;
      }else if(id==="view"&&b.dataset.value==="electoral"&&S.layer==="desviacion"){
        S.layer="ganador";$("layer").value=S.layer;
      }
      if(id==="scope"){S.province=null;S.unit={kind:"pais",properties:{}};S.region="";
        S.level=S.scope==="autonomico"?"comunidad":"provincia";$("level").value=S.level;
        map.fitBounds([[-9.8,35.3],[4.5,44.2]],{padding:30,duration:dur(350)});}
      refresh();
    }));
    document.querySelectorAll("#regla button").forEach(b=>b.onclick=()=>setRegla(b.dataset.value));
    $("layer").onchange=e=>{S.layer=e.target.value;if(dvActiva()){toDV();note("");refresh();return;}if(puntosActiva()){toPuntos();note("");refresh();return;}if(S.layer==="desviacion"&&S.view!=="territorial"){
      S.view="territorial";updateSegments("view","territorial");}
      if(S.layer==="ganador"&&S.view!=="electoral"){S.view="electoral";updateSegments("view","electoral");}
      note("");refresh();};
    $("level").onchange=e=>{S.level=e.target.value;note("");prepareArea();paint();};
    $("election-region").onchange=e=>{
      if(dvActiva()&&S.scope!=="autonomico"){S.layer="ganador";$("layer").value="ganador";}
      S.region=e.target.value;
      const community=D.communities?.features.find(f=>regionId(f.properties.nombre)===S.region);
      S.unit=community?{kind:"comunidad",properties:community.properties}:{kind:"pais",properties:{}};
      syncElection();refresh();
      if(community)focus(community.geometry);
    };
    $("search").addEventListener("keydown",e=>{if(e.key==="Enter")search(e.target.value);});
    ["boundaries","labels"].forEach(id=>$(id).onchange=()=>paint());
    document.querySelectorAll("[data-panel]").forEach(b=>b.onclick=()=>{
      S.panel=b.dataset.panel;document.querySelectorAll("[data-panel]").forEach(x=>x.setAttribute("aria-pressed",String(x===b)));renderDetail();
    });
    $("reset-map").onclick=()=>{S.province=null;S.unit={kind:"pais",properties:{}};S.level=S.scope==="nacional"?"provincia":"comunidad";$("level").value=S.level;
      map.fitBounds([[-9.8,35.3],[4.5,44.2]],{padding:30,duration:dur(450)});refresh();};
    $("peninsula").onclick=()=>map.fitBounds([[-9.8,35.6],[4.5,43.95]],{padding:25,duration:dur(350)});
    $("canarias").onclick=()=>map.fitBounds([[-18.5,27.4],[-13.3,29.5]],{padding:25,duration:dur(350)});
    $("help").onclick=()=>$("help-dialog").showModal();
  }
  async function init(){
    if(!window.maplibregl){note("No se pudo cargar la librería cartográfica MapLibre.");return;}
    controls();
    try{
      await cargarActual();
      const [pr,cc,idx,sec,terr,products,calendar,prov,puntos]=await Promise.all([
        getJson(BASE.provincias),getJson(BASE.comunidades),
        getJson(BASE.indices).catch(()=>null),getJson(BASE.secciones+"INDEX.json").catch(()=>null),
        getJson(BASE.territorial).catch(()=>null),getJson(BASE.productos).catch(()=>null),
        getLocal(BASE.calendario).catch(()=>({})),getJson(BASE.procedencia).catch(()=>null),getLocal(BASE.puntos).catch(()=>null)
      ]);
      if(pr.type!=="FeatureCollection"||cc.type!=="FeatureCollection")throw Error("Fuentes base cartográficas inválidas");
      if(window.DV)await loadDVIndex();else DVD.error="No se pudo cargar el lector de la doble vuelta.";
      updateSegments("regla",S.regla);$("regla-ayuda").textContent=regla()?.ayuda||"";
      D.prov=pr;D.communities=cc;D.index=idx;D.sectionsIndex=sec;D.territorial=terr;D.products=products;
      D.calendar=calendar;D.provenance=prov;
      D.puntos=puntos&&puntos.provincias&&Object.keys(puntos.provincias).length===52?puntos:null;
      if(!(PT&&D.puntos)){ // sin los datos de la situación actual: la capa de siempre, y se dice
        D.puntos=null;D.puntosError="Los datos de la situación actual no están disponibles; se muestra la doble vuelta.";
        S.layer="doblevuelta";S.system="mayoritario";$("layer").value="doblevuelta";updateSegments("system","mayoritario");}
      $("places").innerHTML=pr.features.map(f=>"<option value='"+esc(f.properties.nombre)+"'></option>").join("")+
        cc.features.map(f=>"<option value='"+esc(f.properties.nombre)+"'></option>").join("");
      $("election-region").innerHTML='<option value="">Selecciona parlamento</option>'+
        Object.entries(REGION).map(([name,id])=>"<option value='"+esc(id)+"'>"+esc(name)+"</option>").join("");
      map=new maplibregl.Map({container:"map",style:styleInit(),bounds:[[-9.8,35.4],[4.5,44.2]],
        fitBoundsOptions:{padding:30},dragRotate:false,pitchWithRotate:false,renderWorldCopies:false,attributionControl:false,locale:LOCALE_ES});
      map.addControl(new maplibregl.NavigationControl({showCompass:false}),"top-right");
      map.on("load",()=>{bootstrap=true;install();});
      map.on("error",e=>{if(e?.error)console.error("MapLibre:",e.error);});
    }catch(e){note("No es posible inicializar el visor: "+e.message);console.error(e);}
  }
  init();
})();
