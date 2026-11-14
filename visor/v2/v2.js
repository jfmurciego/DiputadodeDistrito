const HUECOS={
 marcaLema:"Lema corto bajo el nombre (3-5 palabras)",
 inicioAntetitulo:"Antetítulo de portada (3-6 palabras)",
 inicioTitulo:"Título de portada (frase corta y fuerte)",
 inicioEntradilla:"Entradilla de portada (2-3 frases: qué es y por qué importa)",
 inicioBotonNacional:"Botón hacia Nacional (2-4 palabras)",
 inicioBotonAutonomico:"Botón hacia Autonómico (2-4 palabras)",
 inicioBloqueTitulo:"Título del bloque de ideas",
 inicioBloqueTexto:"Texto del bloque de ideas (2-3 frases)",
 inicioIdea1Titulo:"Idea 1 · título",inicioIdea1Texto:"Idea 1 · texto (1-2 frases)",
 inicioIdea2Titulo:"Idea 2 · título",inicioIdea2Texto:"Idea 2 · texto (1-2 frases)",
 inicioIdea3Titulo:"Idea 3 · título",inicioIdea3Texto:"Idea 3 · texto (1-2 frases)",
 inicioCita:"Cita o frase para compartir",inicioCitaPie:"Pie de la cita (1 frase)",
 nacionalTitulo:"Título de Nacional",nacionalEntradilla:"Entradilla de Nacional (2-3 frases)",
 nacionalModelo407:"Qué es la propuesta de 407 (1-2 frases)",
 nacionalModelo350:"Qué es la comparación con 350 (1-2 frases)",
 nacionalNotaTitulo:"Título de la nota de comparación",nacionalNotaTexto:"Texto de la nota de comparación (2 frases)",
 nacionalVisorTitulo:"Título sobre el visor",nacionalVisorTexto:"Cómo usar el visor (1-2 frases)",
 autonomicoTitulo:"Título de Autonómico",autonomicoEntradilla:"Entradilla de Autonómico (2-3 frases)",
 autonomicoFichasPie:"Subtítulo de la lista de parlamentos",
 autonomicoBloqueTitulo:"Título del bloque final de Autonómico",autonomicoBloqueTexto:"Texto del bloque final (2-3 frases)",
 eleccionesTitulo:"Título de Elecciones",eleccionesEntradilla:"Entradilla de Elecciones (2-3 frases)",
 eleccionesIdea1Titulo:"Bloque 1 · título",eleccionesIdea1Texto:"Bloque 1 · texto",
 eleccionesIdea2Titulo:"Bloque 2 · título",eleccionesIdea2Texto:"Bloque 2 · texto",
 eleccionesIdea3Titulo:"Bloque 3 · título",eleccionesIdea3Texto:"Bloque 3 · texto",
 metodoTitulo:"Título de Método",metodoEntradilla:"Entradilla de Método (2-3 frases)",
 metodo1Titulo:"Paso 1 · título",metodo1Texto:"Paso 1 · texto",
 metodo2Titulo:"Paso 2 · título",metodo2Texto:"Paso 2 · texto",
 metodo3Titulo:"Paso 3 · título",metodo3Texto:"Paso 3 · texto",
 metodo4Titulo:"Paso 4 · título",metodo4Texto:"Paso 4 · texto",
 cierreCita:"Frase de cierre",cierreAviso:"Aviso legal corto (mapa de investigación sin valor oficial)",
 padron2026:"Aviso del padrón de las generales de 2026 (D-69)",
 pieTexto:"Texto del pie de página"
};
Object.keys(HUECOS).forEach(k=>{if(!document.querySelector('[data-k="'+k+'"]'))delete HUECOS[k]});
const AUTONOMICO=[["Andalucía",109],["Aragón",67],["Principado de Asturias",45],["Islas Baleares",59],["Canarias",70],["Cantabria",35],["Castilla y León",82],["Castilla-La Mancha",33],["Cataluña",135],["Comunidad Valenciana",99],["Extremadura",65],["Galicia",75],["Comunidad de Madrid",135],["Región de Murcia",45],["Comunidad Foral de Navarra",50],["País Vasco",75],["La Rioja",33],["Ceuta",25],["Melilla",25]];
let textos={};
const EDIT=/[?&]edit=1/.test(location.search);if(EDIT)document.body.classList.add("edit");
function leerMd(md){const t={};let k=null;md.split(/\r?\n/).forEach(l=>{const m=/^##\s+(\S+)\s*$/.exec(l);if(m){k=m[1];t[k]=[];return}if(k===null||/^\s*<!--.*-->\s*$/.test(l)||/^#\s/.test(l))return;t[k].push(l)});Object.keys(t).forEach(k=>t[k]=t[k].join("\n").trim());return t}
const TEXTOS_URL=document.currentScript.dataset.textos||"../../web/textos.md";
const esc=s=>s.replace(/&/g,"&amp;").replace(/</g,"&lt;");
function aplicar(){
 document.querySelectorAll("[data-k]").forEach(el=>{
  const k=el.dataset.k,t=(textos[k]||"").trim();
  el.innerHTML=t?esc(t).replace(/\n/g,"<br>"):(EDIT?`<span class="ph">[${HUECOS[k]||k}]</span>`:"");
 });
}
function aMarkdown(){
 return "# Textos de la web de Diputado de Distrito\n# Escribe debajo de cada «## clave». Una línea en blanco separa párrafos.\n\n"+Object.keys(HUECOS).map(k=>`## ${k}\n<!-- ${HUECOS[k]} -->\n${(textos[k]||"").trim()}\n`).join("\n");
}
const setTab=id=>{document.querySelectorAll(".page").forEach(p=>p.classList.toggle("active",p.id==="page-"+id));document.querySelectorAll(".tab").forEach(b=>{const on=b.dataset.tab===id;b.classList.toggle("active",on);on?b.setAttribute("aria-current","page"):b.removeAttribute("aria-current")});if(id==="inicio"&&map)setTimeout(()=>map.resize(),30);scrollTo({top:0});};
document.querySelectorAll("[data-tab]").forEach(b=>b.onclick=()=>setTab(b.dataset.tab));
document.querySelectorAll("[data-tab-go]").forEach(b=>b.onclick=e=>{e.preventDefault();setTab(b.dataset.tabGo)});
const max=135;
document.querySelector("#region-bars").innerHTML=[...AUTONOMICO].sort((a,b)=>b[1]-a[1]).map(([n,d])=>`<div class="region-row"><span class="name">${n}</span><span class="bar"><i style="width:${d/max*100}%"></i></span><b>${d}</b></div>`).join("");
document.querySelector("#region-grid").innerHTML=AUTONOMICO.map(([n,d])=>`<div class="region-chip"><span>${d}</span><b>${n}</b></div>`).join("");
fetch("datos/provincias.json").then(r=>r.json()).then(p=>{
 const rows=p.features.map(f=>f.properties).sort((a,b)=>a.cod.localeCompare(b.cod));
 const mk=59;
 document.querySelector("#province-comparison").innerHTML=rows.map(r=>`<div class="prov"><span class="prov-name">${r.nombre}</span><span class="mini-bar ddd"><i style="width:${r.k407/mk*100}%"></i></span><b>${r.k407}</b><span class="mini-bar cur"><i style="width:${r.escanos/mk*100}%"></i></span><b>${r.escanos}</b></div>`).join("");
}).catch(()=>{});
document.querySelectorAll(".model").forEach(m=>{
 m.tabIndex=0;m.setAttribute("role","button");m.setAttribute("aria-pressed",String(m.classList.contains("active")));
 const act=()=>{document.querySelectorAll(".model").forEach(x=>{x.classList.remove("active");x.setAttribute("aria-pressed","false")});m.classList.add("active");m.setAttribute("aria-pressed","true")};
 m.onclick=act;m.onkeydown=e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();act()}};
});
const editor=document.querySelector("#editor"),fields=document.querySelector("#editor-fields");
function pintarCampos(){fields.innerHTML=Object.keys(HUECOS).map(k=>`<label for="t-${k}">${k}<span style="font-weight:400;color:#8a8f8c"> · ${HUECOS[k]}</span><textarea id="t-${k}" data-key="${k}">${esc(textos[k]||"")}</textarea></label>`).join("")}
document.querySelector("#b-editar").onclick=()=>{pintarCampos();editor.classList.add("open")};
document.querySelector("#editor-close").onclick=()=>editor.classList.remove("open");
document.querySelector("#b-claves").onclick=e=>{document.body.classList.toggle("marcas");e.currentTarget.classList.toggle("on")};
function leerCampos(){fields.querySelectorAll("textarea").forEach(t=>textos[t.dataset.key]=t.value);}
document.querySelector("#aplicar").onclick=()=>{leerCampos();aplicar()};
document.querySelector("#vaciar").onclick=()=>{textos={};pintarCampos();aplicar()};
document.querySelector("#copiar").onclick=()=>{
 leerCampos();aplicar();const md=aMarkdown(),av=document.querySelector("#aviso-copia"),ta=document.querySelector("#copia-manual");
 const manual=()=>{ta.value=md;ta.hidden=false;ta.select();av.textContent="No se pudo copiar solo: selecciona el texto de abajo y cópialo.";av.hidden=false};
 try{navigator.clipboard.writeText(md).then(()=>{ta.hidden=true;av.textContent="Copiado. Pégalo en web/textos.md del repositorio.";av.hidden=false},manual)}catch(e){manual()}
};
fetch(TEXTOS_URL).then(r=>r.ok?r.text():"").catch(()=>"").then(md=>{textos=leerMd(md||"");aplicar()});
const NOMBRE={"PP":"PP","PSOE":"PSOE","VOX":"VOX","SUMAR":"SUMAR","ERC":"ERC","JUNTS":"Junts","EH Bildu":"EH Bildu","EAJ-PNV":"PNV","BNG":"BNG","UPN":"UPN","CCa":"CC"};
const VARP={"PP":"--pp","PSOE":"--psoe","VOX":"--vox","SUMAR":"--sumar","ERC":"--erc","JUNTS":"--junts","EH Bildu":"--bildu","EAJ-PNV":"--pnv","BNG":"--bng","UPN":"--upn","CCa":"--cca"};
const ORDEN=["SUMAR","ERC","EH Bildu","BNG","PSOE","EAJ-PNV","JUNTS","CCa","UPN","PP","VOX"];
const ELEC=[["2011","nov"],["2015","dic"],["2016","jun"],["2019","abr"],["2019","nov"],["2023","jul"],["2026","nov"]];
const css=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const col=p=>css(VARP[p]||"--otros");
const $=id=>document.getElementById(id);
let modo="electoral",terr=null,capa="ganador",rot=null,vista="congreso",prov=null,ccaa=null,map=null,sel=null,selId=null,selCcaa=null,hoverCcaa=null;
const NOTAS_ELECCION={"2026":"Los distritos de las generales de 2026 están trazados con el padrón y el seccionado de 2023; se actualizarán con el padrón de 2025."};
const barra=$("elecciones-barra");
const et=document.createElement("span");et.textContent="Elecciones generales";barra.appendChild(et);
ELEC.forEach(([a,m])=>{const b=document.createElement("button");b.className="eleccion";const on=a==="2023";b.disabled=!on;b.setAttribute("aria-pressed",String(on));b.innerHTML=a+"<small>"+m+(on?"":a==="2026"?" · 29-11":" · sin datos")+"</small>";b.addEventListener("click",()=>{const n=$("nota-eleccion");if(n){n.textContent=NOTAS_ELECCION[a]||"";n.hidden=!NOTAS_ELECCION[a]}});barra.appendChild(b)});
function totales(){const t={};prov.features.forEach(f=>{for(const[p,n]of Object.entries(f.properties.esc))t[p]=(t[p]||0)+n});return t}
function hemi(esc){
 const total=Object.values(esc).reduce((a,b)=>a+b,0),filas=9,r0=38,r1=96,pts=[];
 const R=[...Array(filas)].map((_,i)=>r0+(r1-r0)*i/(filas-1)),suma=R.reduce((a,b)=>a+b,0);
 let as=0;const pf=R.map((r,i)=>{const n=i===filas-1?total-as:Math.round(total*r/suma);as+=n;return n});
 R.forEach((r,i)=>{const n=pf[i];for(let j=0;j<n;j++){const a=Math.PI*(1-(n===1?.5:j/(n-1)));pts.push({x:100+r*Math.cos(a),y:104-r*Math.sin(a),a})}});
 pts.sort((p,q)=>q.a-p.a);const seq=[];ORDEN.forEach(p=>{for(let k=0;k<(esc[p]||0);k++)seq.push(p)});
 return `<svg class="hemi" viewBox="0 0 200 112" role="img" aria-label="Hemiciclo de ${total} escaños">${pts.map((p,i)=>`<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="3.1" fill="${col(seq[i])}"/>`).join("")}<text x="100" y="100" text-anchor="middle" font-family="Georgia,serif" font-size="15" fill="${css("--ink")}">${total}</text></svg>`;
}
const tabla=esc=>`<table class="tabla">${Object.entries(esc).sort((a,b)=>b[1]-a[1]).map(([p,n])=>`<tr><td><span class="sw" style="background:${col(p)}"></span>${NOMBRE[p]||p}</td><td>${n}</td></tr>`).join("")}</table>`;
function fichaC(){
 const f=$("ficha");
 if(modo==="territorial"&&terr){if(sel&&secIdx&&!secOn)secSet(true);fichaT();return}
 if(capa==="rotacion"&&rot&&sel&&rot.provincias[sel.properties.cod]){fichaRot();return}
 if(!sel){f.innerHTML=`<p class="eyebrow">Generales · julio de 2023</p><h2>España</h2>${hemi(totales())}${tabla(totales())}<p class="aviso">Pulsa una provincia del mapa para ver su reparto. Con «350 distritos» (T-102) aquí saldrá el mismo hemiciclo con el ganador de cada distrito.</p>`;return}
 const p=sel.properties;
 f.innerHTML=`<p class="eyebrow">Circunscripción · ${p.escanos} escaños</p><h2>${p.nombre}</h2><p class="nota">Más votado: <b>${NOMBRE[p.ganador]||p.ganador}</b> (${String(p.pct).replace(".",",")} % de los votos a candidaturas)</p>${hemi(p.esc)}${tabla(p.esc)}<p class="pend">Propuesta del proyecto: ${p.k407} ${p.k407===1?"distrito":"distritos"} uninominales en esta provincia. Su mapa y su ganador por distrito llegan con la capa «407 distritos».</p>`;
}
function fichaA(){
 const f=$("ficha");
 if(!ccaa){f.innerHTML=`<p class="eyebrow">Parlamentos autonómicos</p><h2>Elige una comunidad</h2><p class="nota">Pulsa una comunidad en el mapa. No hay desplegables: el mapa es el selector.</p><p class="pend">Esta vista no comparte controles con la del Congreso. Cada parlamento tendrá su propia barra de elecciones y sus distritos.</p>`;return}
 f.innerHTML=`<p class="eyebrow">Parlamento autonómico</p><h2>${ccaa.properties.nombre}</h2><p class="pend">Hemiciclo, distritos propuestos y elecciones autonómicas de este parlamento: próximamente.</p>`;
}
function leyenda(){
 const L=$("leyenda");
 if(vista==="autonomico"){L.innerHTML=`<span><span class="sw" style="background:${css("--red")}"></span>Comunidad elegida</span>`;return}
 if(secOn&&secCod&&secNDist&&vista==="congreso"){L.innerHTML=`<span><span class="sw" style="background:linear-gradient(90deg,#c0392b,#2e86c1,#27ae60,#d68910)"></span>Cada color es un distrito (${secNDist}); las líneas finas son secciones censales</span>`;return}
 if(modo==="territorial"&&terr){L.innerHTML=`<span><span class="sw" style="background:${ROT_COL(0)}"></span>0 %</span><span><span class="sw" style="background:${ROT_COL(1)}"></span>40 % o más: mayor desviación de un distrito respecto a la media de su provincia</span><span style="color:${css("--muted")}">· gris: sin datos</span>`;return}
 if(capa==="rotacion"&&rot){L.innerHTML=`<span><span class="sw" style="background:${ROT_COL(0)}"></span>0 cambios</span><span><span class="sw" style="background:${ROT_COL(1)}"></span>5 cambios de ganador (media por distrito, 2011-2023)</span><span style="color:${css("--muted")}">· gris: sin datos</span>`;return}
 const ps=[...new Set(prov.features.map(f=>f.properties.ganador))];
 L.innerHTML=ps.map(p=>`<span><span class="sw" style="background:${col(p)}"></span>${NOMBRE[p]||p}</span>`).join("")+`<span style="color:${css("--muted")}">· más votado por provincia</span>`;
}
function pintar(){
 if(!map||!map.getLayer("prov-fill"))return;
 const e=["match",["get","ganador"]];Object.keys(VARP).forEach(p=>e.push(p,col(p)));e.push(css("--otros"));
 map.setPaintProperty("prov-fill","fill-color",vista==="congreso"?(modo==="territorial"&&terr?terrColor():capa==="rotacion"&&rot?rotColor():e):css("--land"));
 map.setPaintProperty("prov-fill","fill-opacity",vista==="congreso"?["case",["boolean",["feature-state","sel"],false],1,.86]:.9);
 map.setPaintProperty("ccaa-fill","fill-opacity",vista==="autonomico"?["case",["boolean",["feature-state","sel"],false],.75,["boolean",["feature-state","hover"],false],.25,0]:0);
 map.setPaintProperty("ccaa-line","line-width",vista==="autonomico"?1.4:.7);
 leyenda();
}
const ESP=[[-13.2,33.7],[4.6,44.0]];
function bbox(g){let a=[180,90,-180,-90];const w=c=>{if(typeof c[0]==="number"){a[0]=Math.min(a[0],c[0]);a[1]=Math.min(a[1],c[1]);a[2]=Math.max(a[2],c[0]);a[3]=Math.max(a[3],c[1])}else c.forEach(w)};w(g.coordinates);return[[a[0],a[1]],[a[2],a[3]]]}
function setSel(src,id,key,prev){if(prev!==null)map.setFeatureState({source:src,id:prev},{[key]:false});if(id!==null)map.setFeatureState({source:src,id},{[key]:true})}
function irEspana(){
 if(selId!==null){setSel("prov",null,"sel",selId);selId=null}
 if(selCcaa!==null){setSel("ccaa",null,"sel",selCcaa);selCcaa=null}
 sel=null;ccaa=null;$("ruta").textContent="España";$("volver").hidden=true;
 map.fitBounds(ESP,{padding:20,duration:500});vista==="congreso"?fichaC():fichaA();secCod=null;secCargar();
}
function cambiar(v){vista=v;$("v-congreso").setAttribute("aria-pressed",String(v==="congreso"));$("v-autonomico").setAttribute("aria-pressed",String(v==="autonomico"));$("controles-congreso").hidden=v!=="congreso";$("modos").hidden=v!=="congreso";barra.hidden=v!=="congreso"||modo==="territorial";irEspana();pintar()}
$("v-congreso").onclick=()=>cambiar("congreso");$("v-autonomico").onclick=()=>cambiar("autonomico");$("volver").onclick=irEspana;
document.querySelectorAll('[data-tab="inicio"],[data-tab-go="inicio"]').forEach(b=>b.addEventListener("click",()=>setTimeout(()=>map&&map.resize(),30)));
Promise.all([fetch("datos/provincias.json").then(r=>r.json()),fetch("datos/comunidades.json").then(r=>r.json())]).then(([p,c])=>{
 prov=p;fichaC();
 map=new maplibregl.Map({container:"map",style:{version:8,sources:{},layers:[{id:"bg",type:"background",paint:{"background-color":css("--sea")}}]},bounds:ESP,fitBoundsOptions:{padding:20},attributionControl:false,dragRotate:false,pitchWithRotate:false,renderWorldCopies:false});
 map.touchZoomRotate.disableRotation();map.on("error",e=>console.error(String(e.error&&e.error.stack||e.message)));
 map.on("load",()=>{
  map.addSource("prov",{type:"geojson",data:p});map.addSource("ccaa",{type:"geojson",data:c});
  map.addSource("caja",{type:"geojson",data:{type:"Feature",geometry:{type:"LineString",coordinates:[[-12.9,33.95],[-7.75,33.95],[-7.75,36.25],[-12.9,36.25],[-12.9,33.95]]}}});
  map.addLayer({id:"prov-fill",type:"fill",source:"prov",paint:{"fill-color":"#999"}});
  map.addLayer({id:"prov-line",type:"line",source:"prov",paint:{"line-color":css("--stroke"),"line-width":.6}});
  map.addLayer({id:"ccaa-fill",type:"fill",source:"ccaa",paint:{"fill-color":css("--red"),"fill-opacity":0}});
  map.addLayer({id:"ccaa-line",type:"line",source:"ccaa",paint:{"line-color":css("--ink"),"line-width":.7}});
  map.addLayer({id:"caja",type:"line",source:"caja",paint:{"line-color":css("--muted"),"line-width":1,"line-dasharray":[3,2]}});
  pintar();iniciarSecciones();
  const tip=$("tip");
  map.on("mousemove",e=>{
   const f=map.queryRenderedFeatures(e.point,{layers:[vista==="congreso"?"prov-fill":"ccaa-fill"]})[0];
   if(vista==="autonomico"){const id=f?f.id:null;if(id!==hoverCcaa){if(hoverCcaa!==null)map.setFeatureState({source:"ccaa",id:hoverCcaa},{hover:false});if(id!==null)map.setFeatureState({source:"ccaa",id},{hover:true});hoverCcaa=id}}
   if(!f){tip.hidden=true;map.getCanvas().style.cursor="";return}
   map.getCanvas().style.cursor="pointer";const q=f.properties;
   tip.innerHTML=vista==="congreso"?`<b>${q.nombre}</b> · ${q.escanos} escaños · más votado: ${NOMBRE[q.ganador]||q.ganador}`:`<b>${q.nombre}</b>`;
   tip.hidden=false;tip.style.left=Math.max(6,Math.min(e.point.x+12,map.getCanvas().clientWidth-tip.offsetWidth-6))+"px";tip.style.top=(e.point.y+12)+"px";
  });
  map.on("mouseout",()=>{tip.hidden=true});
  map.on("click",e=>{
   if(vista==="congreso"){if(secOn&&map.getLayer("sec-fill")&&map.queryRenderedFeatures(e.point,{layers:["sec-fill"]}).length)return;const f=map.queryRenderedFeatures(e.point,{layers:["prov-fill"]})[0];if(!f)return;const full=prov.features.find(x=>x.id===f.id);setSel("prov",f.id,"sel",selId);selId=f.id;sel=full;$("ruta").textContent="España › "+full.properties.nombre;$("volver").hidden=false;map.fitBounds(bbox(full.geometry),{padding:50,maxZoom:8,duration:500});fichaC()}
   else{const f=map.queryRenderedFeatures(e.point,{layers:["ccaa-fill"]})[0];if(!f)return;const full=c.features.find(x=>x.id===f.id);setSel("ccaa",f.id,"sel",selCcaa);selCcaa=f.id;ccaa=full;$("ruta").textContent="España › "+full.properties.nombre;$("volver").hidden=false;map.fitBounds(bbox(full.geometry),{padding:50,maxZoom:8,duration:500});fichaA()}
  });
 });
}).catch(err=>{$("ficha").innerHTML=`<p class="aviso">No se pudo cargar el mapa: ${err.message}. Recarga la página.</p>`});

/* Capa de secciones censales (T-119): opcional; solo existe si la publicación trae datos/secciones/INDEX.json. */
let secOn=false,secIdx=null,secCod=null,secNDist=0;
const SEC_COL=["#c0392b","#2e86c1","#27ae60","#d68910","#8e44ad","#17a589","#cb4335","#5d6d7e","#b7950b","#2874a6"];
const secProv=()=>sel&&vista==="congreso"?sel.properties.cod:null;
function secFicha(p){
 const f=$("ficha");
 f.innerHTML=`<p class="eyebrow">Sección censal ${p.s}</p><h2>${esc(String(p.m||"Sin municipio"))}</h2><p class="nota">Distrito <b>${Number(p.d)}</b> · ${Number(p.p).toLocaleString("es-ES")} habitantes</p><p class="aviso">Geometría: seccionado del INE. Mapa de investigación sin valor oficial.</p>`;
}
function secCargar(){
 const cod=secProv();
 if(!map||!map.getLayer("sec-fill"))return;
 map.setLayoutProperty("sec-fill","visibility",secOn&&cod?"visible":"none");
 map.setLayoutProperty("sec-line","visibility",secOn&&cod?"visible":"none");
 if(!secOn||!cod||!secIdx||!secIdx.provincias[cod]){if(secOn&&cod&&secIdx&&!secIdx.provincias[cod])$("ruta").textContent+=" (sin secciones)";return}
 if(secCod===cod)return;secCod=cod;
 fetch("datos/secciones/"+cod+".geojson").then(r=>{if(!r.ok)throw new Error(r.status);return r.json()}).then(g=>{
  if(secCod!==cod)return;
  const ds=[...new Set(g.features.map(f=>Number(f.properties.d)))].sort((x,y)=>x-y),e=["match",["to-number",["get","d"]]];
  ds.forEach((d,i)=>e.push(d,"hsl("+Math.round((i*137.508)%360)+","+(i%2?52:68)+"%,"+(i%3===0?44:i%3===1?56:50)+"%)"));e.push("#999");
  map.setPaintProperty("sec-fill","fill-color",e);secNDist=ds.length;leyenda();
  map.getSource("sec").setData(g);
 }).catch(e=>{secCod=null;console.error("secciones "+cod+": "+e.message)});
}
function secSet(v){secOn=v;$("c-secciones").setAttribute("aria-pressed",String(v));secCargar();leyenda()}
function iniciarSecciones(){
 const chip=$("c-secciones");
 fetch("datos/secciones/INDEX.json").then(r=>r.ok?r.json():null).catch(()=>null).then(idx=>{
  if(!idx||!idx.provincias||!map)return;secIdx=idx;
  const col=["match",["%",["to-number",["get","d"]],SEC_COL.length]];SEC_COL.forEach((c,i)=>col.push(i,c));col.push("#999");
  map.addSource("sec",{type:"geojson",data:{type:"FeatureCollection",features:[]}});
  map.addLayer({id:"sec-fill",type:"fill",source:"sec",minzoom:6,layout:{visibility:"none"},paint:{"fill-color":col,"fill-opacity":.7}});
  map.addLayer({id:"sec-line",type:"line",source:"sec",minzoom:6,layout:{visibility:"none"},paint:{"line-color":"#fff","line-width":.4}});
  chip.removeAttribute("aria-disabled");chip.removeAttribute("data-motivo");chip.title="Colorea cada sección por su distrito (elige antes una provincia)";const sm=chip.querySelector("small");if(sm)sm.remove();
  chip.onclick=()=>secSet(!secOn);
  map.on("click","sec-fill",e=>{const f=e.features&&e.features[0];if(f)secFicha(f.properties)});
  map.on("click",()=>setTimeout(secCargar,0));
 });
}

/* Capas y chips (T-119, PR-B): solo datos que existen; lo demás queda «sin datos» con motivo visible. */
const ROT_COL=t=>{const a=[241,233,220],b=[179,58,45],m=a.map((x,i)=>Math.round(x+(b[i]-x)*t));return`rgb(${m})`};
const mediaRot=cod=>{const d=rot.provincias[cod].distritos;return d.reduce((s,x)=>s+x.c,0)/d.length};
function rotColor(){const e=["match",["get","cod"]];Object.keys(rot.provincias).forEach(c=>e.push(c,ROT_COL(Math.min(mediaRot(c)/5,1))));e.push("#c9c9c4");return e}
function fichaRot(){
 const p=sel.properties,R=rot.provincias[p.cod],ys=rot.elecciones.map(e=>[e.slice(2,4)+(e==="201904"?"a":e==="201911"?"n":""),e.slice(0,4)+" ("+e.slice(4)+")"]);
 $("ficha").innerHTML=`<p class="eyebrow">Rotación 2011-2023 · distritos de la propuesta</p><h2>${p.nombre}</h2><p class="nota">Ganador por distrito y elección (homologado). Cambios de ganador: media ${mediaRot(p.cod).toFixed(1).replace(".",",")}.</p><div style="overflow-x:auto"><table class="rot-tabla"><tr><th>D.</th>${ys.map(y=>`<th title="${y[1]}">${y[0]}</th>`).join("")}<th>Δ</th></tr>${R.distritos.map(x=>`<tr><td>${x.d}</td>${x.g.map(g=>`<td title="${esc(g)}"><span class="sw" style="background:${col(g)}"></span></td>`).join("")}<td>${x.c}</td></tr>`).join("")}</table></div><p class="aviso">Datos: histórico T-110 sobre los distritos vigentes; sin valor oficial.</p>`;
}
function motivo(t){const m=$("motivo");m.textContent=t||"";m.hidden=!t}
document.querySelectorAll(".chip[data-motivo]").forEach(b=>b.addEventListener("click",()=>{if(b.getAttribute("aria-disabled")==="true")motivo(b.dataset.motivo)}));
$("s-407").onclick=()=>{motivo("");setTab("nacional")};
function ponCapa(c){capa=c;$("c-ganador").setAttribute("aria-pressed",String(c==="ganador"));$("c-rotacion").setAttribute("aria-pressed",String(c==="rotacion"));motivo("");pintar();vista==="congreso"&&fichaC()}
$("c-ganador").onclick=()=>ponCapa("ganador");
fetch("datos/rotacion.json").then(r=>r.ok?r.json():null).catch(()=>null).then(d=>{
 if(!d||!d.provincias)return;rot=d;const b=$("c-rotacion");b.removeAttribute("aria-disabled");b.removeAttribute("data-motivo");const sm=b.querySelector("small");if(sm)sm.remove();b.onclick=()=>ponCapa("rotacion");
});

/* Vista territorial (T-119 PR-C): del M06 publicado, sin resultados electorales. */
const pc=x=>(x>=0?"+":"−")+Math.abs(x*100).toFixed(1).replace(".",",")+" %",num=x=>Math.round(x).toLocaleString("es-ES");
const maxDev=c=>Math.max(...terr.provincias[c].distritos.map(x=>Math.abs(x.dev)));
function terrColor(){const e=["match",["get","cod"]];Object.keys(terr.provincias).forEach(c=>e.push(c,ROT_COL(Math.min(maxDev(c)/.4,1))));e.push("#c9c9c4");return e}
function fichaT(){
 const f=$("ficha");
 if(!sel||!terr.provincias[sel.properties.cod]){
  const P=Object.values(terr.provincias),D=P.flatMap(x=>x.distritos);
  f.innerHTML=`<p class="eyebrow">Territorial · sin resultados electorales</p><h2>España</h2><div class="terr-resumen"><div><b>${P.length}</b><span>provincias con datos</span></div><div><b>${D.length}</b><span>distritos</span></div><div><b>${num(D.reduce((a,x)=>a+x.p,0))}</b><span>habitantes</span></div><div><b>${D.filter(x=>!x.tol).length}</b><span>fuera de la tolerancia · ${D.filter(x=>x.exenta).length} con suelo exento</span></div></div><p class="aviso">Pulsa una provincia: verás sus distritos con población, desviación, municipios y secciones.</p>`;return}
 const p=sel.properties,R=terr.provincias[p.cod],D=R.distritos,tot=D.reduce((a,x)=>a+x.p,0);
 f.innerHTML=`<p class="eyebrow">Territorial · ${D.length} ${D.length===1?"distrito":"distritos"}</p><h2>${p.nombre}</h2><div class="terr-resumen"><div><b>${num(tot)}</b><span>habitantes</span></div><div><b>${num(D[0].o)}</b><span>objetivo por distrito (media)</span></div><div><b>${num(D[0].techo)}</b><span>techo de población</span></div><div><b>${D.some(x=>x.exenta)?"con exención":"sin exención"}</b><span>suelo ${num(Math.max(...D.map(x=>x.suelo)))} (0 = exento)</span></div></div>`+D.map(x=>`<details class="terr-dist"><summary><b>${esc(x.n||"Distrito "+x.d)}</b><span class="dev${x.tol?"":" mal"}">${pc(x.dev)}</span><small>${num(x.p)} hab. · ${x.s} secciones · ${x.m.length} ${x.m.length===1?"municipio":"municipios"}${x.exenta?" · suelo exento":""}${x.tol?"":" · fuera de tolerancia"}</small></summary><p>${x.m.map(esc).join(", ")}</p></details>`).join("")+`<p class="aviso">Datos: M06 publicado (sha256 ${R.sha256_m06.slice(0,12)}…). Las secciones se ven en el mapa. Sin valor oficial.</p>`;
}
function ponModo(m){
 modo=m;document.body.classList.toggle("modo-territorial",m==="territorial");
 $("m-electoral").setAttribute("aria-pressed",String(m==="electoral"));$("m-territorial").setAttribute("aria-pressed",String(m==="territorial"));
 motivo("");barra.hidden=vista!=="congreso"||m==="territorial";pintar();vista==="congreso"&&fichaC();
}
$("m-electoral").onclick=()=>ponModo("electoral");
fetch("datos/territorial.json").then(r=>r.ok?r.json():null).catch(()=>null).then(d=>{
 if(!d||!d.provincias)return;terr=d;const b=$("m-territorial");b.removeAttribute("aria-disabled");b.removeAttribute("data-motivo");const sm=b.querySelector("small");if(sm)sm.remove();b.onclick=()=>ponModo("territorial");
});
