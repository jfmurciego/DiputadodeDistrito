/* DDD · Galería territorial V3 1.0.0 · Sin datos electorales ni inferencias fotográficas.
 * Fuente: fotografías de portada de artículos locales en Wikipedia en español;
 * licencia y autor leídos de Wikimedia Commons antes de mostrar el recurso.
 * Una foto de la capital representa la provincia, NO un distrito ni sección.
 */
"use strict";
(function(){
  const titles={
    "alava":"Vitoria","araba":"Vitoria","albacete":"Albacete","alicante":"Alicante","alacant":"Alicante",
    "almeria":"Almería","asturias":"Oviedo","avila":"Ávila","badajoz":"Badajoz",
    "barcelona":"Barcelona","burgos":"Burgos","caceres":"Cáceres","cadiz":"Cádiz","cantabria":"Santander",
    "castellon":"Castellón de la Plana","castello":"Castellón de la Plana","ciudadreal":"Ciudad Real",
    "cordoba":"Córdoba (España)","acoruna":"La Coruña","coruna":"La Coruña","lacoruna":"La Coruña","cuenca":"Cuenca (España)",
    "gerona":"Gerona","girona":"Gerona","granada":"Granada","guadalajara":"Guadalajara (España)",
    "guipuzcoa":"San Sebastián","gipuzkoa":"San Sebastián","huelva":"Huelva","huesca":"Huesca",
    "islasbaleares":"Palma de Mallorca","illesbalears":"Palma de Mallorca","jaen":"Jaén (España)",
    "leon":"León (España)","lerida":"Lérida","lleida":"Lérida","lugo":"Lugo","madrid":"Madrid",
    "malaga":"Málaga","murcia":"Murcia","navarra":"Pamplona","orense":"Orense","ourense":"Orense",
    "palencia":"Palencia","laspalmas":"Las Palmas de Gran Canaria","pontevedra":"Pontevedra",
    "larioja":"Logroño","salamanca":"Salamanca","santacruzdetenerife":"Santa Cruz de Tenerife",
    "segovia":"Segovia","sevilla":"Sevilla","soria":"Soria","tarragona":"Tarragona",
    "teruel":"Teruel","toledo":"Toledo","valencia":"Valencia",
    "valladolid":"Valladolid","vizcaya":"Bilbao","bizkaia":"Bilbao","zamora":"Zamora","zaragoza":"Zaragoza",
    "ceuta":"Ceuta","melilla":"Melilla",
    "andalucia":"Sevilla","aragon":"Zaragoza","principadodeasturias":"Oviedo",
    "canarias":"Las Palmas de Gran Canaria","castillayleon":"Valladolid",
    "castillalamancha":"Toledo","cataluna":"Barcelona","comunidadvalenciana":"Valencia",
    "extremadura":"Mérida (España)","galicia":"Santiago de Compostela",
    "comunidaddemadrid":"Madrid","regiondemurcia":"Murcia",
    "comunidadforaldenavarra":"Pamplona","paisvasco":"Vitoria"
  };
  const normalize=t=>String(t||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]/g,"");
  const cache=new Map();
  let revision=0;
  function plain(s){const x=document.createElement("div");x.innerHTML=String(s||"");return (x.textContent||"").trim();}
  async function json(base,params){
    const u=new URL(base);Object.entries(params).forEach(([k,v])=>u.searchParams.set(k,v));
    u.searchParams.set("format","json");u.searchParams.set("origin","*");
    const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),9000);
    try{const r=await fetch(u.toString(),{signal:controller.signal,credentials:"omit"});if(!r.ok)throw Error("HTTP "+r.status);return await r.json();}
    finally{clearTimeout(timeout);}
  }
  async function resolve(title){
    const q=await json("https://es.wikipedia.org/w/api.php",{
      action:"query",prop:"pageimages",piprop:"thumbnail|name",pithumbsize:"900",titles:title,redirects:"1"
    });
    const page=Object.values(q.query?.pages||{})[0];
    if(!page?.thumbnail?.source||!page.pageimage)throw Error("No hay fotografía verificable");
    const file="File:"+page.pageimage;
    const meta=await json("https://commons.wikimedia.org/w/api.php",{
      action:"query",prop:"imageinfo",iiprop:"extmetadata|url",titles:file
    });
    const entry=Object.values(meta.query?.pages||{})[0]?.imageinfo?.[0];
    const m=entry?.extmetadata||{};
    const license=plain(m.LicenseShortName?.value);
    const author=plain(m.Artist?.value||m.Attribution?.value);
    const link=entry?.descriptionurl;
    // No imagen de licencia desconocida: impedir uso sin atribución comprobable.
    if(!license||!link)throw Error("Fotografía sin licencia verificable");
    return {src:page.thumbnail.source,license,author,link,place:page.title};
  }
  function showEmpty(container,label,kind){
    container.replaceChildren();
    const p=document.createElement("p");
    p.className="gallery-unavailable";
    p.textContent=kind==="pais"?"Fotografía nacional no disponible.": "Sin fotografía acreditada para "+label+".";
    container.append(p);
  }
  async function render(kind,name,provinceName){
    const root=document.getElementById("territory-gallery");
    if(!root)return;
    const label=(kind==="distrito"||kind==="seccion")?provinceName:name;
    const target= titles[normalize(label)];
    const ticket=++revision;
    root.hidden=false;
    const heading=root.querySelector(".gallery-heading"),container=root.querySelector(".gallery-content");
    heading.textContent=kind==="distrito"||kind==="seccion"?"Imagen de la provincia":"Conoce el territorio";
    if(!target){showEmpty(container,label,kind);return;}
    container.replaceChildren();
    const loading=document.createElement("p");loading.className="gallery-unavailable";loading.textContent="Buscando fotografía con licencia…";
    container.append(loading);
    try{
      if(!cache.has(target))cache.set(target,resolve(target).catch(e=>{cache.delete(target);throw e;}));
      const photo=await cache.get(target);
      if(ticket!==revision)return;
      const figure=document.createElement("figure");figure.className="gallery-figure";
      const a=document.createElement("a");a.href=photo.link;a.target="_blank";a.rel="noopener noreferrer";
      a.title="Ver fotografía, licencia y procedencia en Wikimedia Commons";
      const img=document.createElement("img");img.src=photo.src;img.alt="Imagen representativa de "+photo.place;
      img.loading="lazy";img.decoding="async";img.referrerPolicy="no-referrer";
      a.append(img);figure.append(a);
      const cap=document.createElement("figcaption");
      const place=document.createElement("strong");place.textContent=photo.place;
      const origin=document.createElement("span");origin.textContent=(kind==="distrito"||kind==="seccion"?"Referencia provincial · ":"")+"Imagen ilustrativa · Wikimedia Commons";
      const credit=document.createElement("small");
      credit.textContent=(photo.author?photo.author+" · ":"")+photo.license+" · Ver atribución completa y condiciones";
      cap.append(place,origin,credit);figure.append(cap);container.replaceChildren(figure);
      img.addEventListener("error",()=>{if(ticket===revision)showEmpty(container,label,kind);},{once:true});
    }catch(e){if(ticket===revision)showEmpty(container,label,kind);}
  }
  window.DDDGaleria={render};
})();
