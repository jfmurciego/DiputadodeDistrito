/* DDD — Visor aislado del candidato Congreso de León. */
const palette=["#2a6fbd","#e88c40","#209779","#aa69bd"];
const map=new maplibregl.Map({container:"map",center:[-5.65,42.65],zoom:7.5,style:{
  version:8,sources:{osm:{type:"raster",tiles:["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],tileSize:256,attribution:"© OpenStreetMap contributors"}},
  layers:[{id:"osm",type:"raster",source:"osm"}]}});
map.addControl(new maplibregl.NavigationControl(),"top-right");
const status=document.querySelector("#status"),detail=document.querySelector("#detail"),list=document.querySelector("#district-list");
const fmt=n=>new Intl.NumberFormat("es-ES").format(n);
function render(data){
  if(data?.type!=="FeatureCollection"||!Array.isArray(data.features)||data.features.length!==4)throw Error("El GeoJSON debe contener exactamente cuatro distritos.");
  const ids=new Set(),bounds=new maplibregl.LngLatBounds(),rows=[];
  for(const f of data.features){
    const p=f.properties||{};
    if(typeof p.district_id!=="string"||ids.has(p.district_id)||p.certification_status!=="NOT_CERTIFIED"||p.pilot_only!==true||!Number.isInteger(p.population)||!Number.isInteger(p.cusec_count)||p.cusec_count<1)throw Error("Identidad, estado o población inválidos.");
    ids.add(p.district_id);rows.push(p);
    function visit(x){if(typeof x?.[0]==="number"){if(x.length<2||!Number.isFinite(x[0])||!Number.isFinite(x[1])||Math.abs(x[0])>180||Math.abs(x[1])>90)throw Error("Coordenadas inválidas");bounds.extend(x)}else if(Array.isArray(x))x.forEach(visit);else throw Error("Coordenadas inválidas")}
    if(!["Polygon","MultiPolygon"].includes(f.geometry?.type))throw Error("Geometría no poligonal");
    visit(f.geometry.coordinates);
  }
  if(map.getLayer("nacional-fill")){map.removeLayer("nacional-fill");map.removeLayer("nacional-border");map.removeSource("nacional")}
  map.addSource("nacional",{type:"geojson",data});
  const match=["match",["get","district_id"]];
  rows.sort((a,b)=>a.district_id.localeCompare(b.district_id));
  rows.forEach((p,i)=>match.push(p.district_id,palette[i]));match.push("#999999");
  map.addLayer({id:"nacional-fill",type:"fill",source:"nacional",paint:{"fill-color":match,"fill-opacity":.57}});
  map.addLayer({id:"nacional-border",type:"line",source:"nacional",paint:{"line-color":"#283747","line-width":2}});
  map.fitBounds(bounds,{padding:35,maxZoom:10});
  list.replaceChildren();
  rows.forEach((p,i)=>{
    const div=document.createElement("div");div.className="legend-item";
    const swatch=document.createElement("span");swatch.className="swatch";swatch.style.backgroundColor=palette[i];
    const t=document.createElement("span");t.textContent=p.district_id+" · "+fmt(p.population)+" hab. · "+fmt(p.cusec_count)+" CUSEC";
    div.append(swatch,t);list.appendChild(div);
  });
  status.textContent="León: 4 distritos candidatos · "+fmt(rows.reduce((a,p)=>a+p.population,0))+" habitantes. Geometría cargada.";
}
map.on("click","nacional-fill",e=>{
  const p=e.features?.[0]?.properties;if(!p)return;
  detail.textContent=p.district_id+" — "+fmt(Number(p.population))+" habitantes; "+fmt(Number(p.cusec_count))+" secciones CUSEC. Producto no certificado.";
});
map.on("mouseenter","nacional-fill",()=>map.getCanvas().style.cursor="pointer");
map.on("mouseleave","nacional-fill",()=>map.getCanvas().style.cursor="");
document.querySelector("#geojson-file").addEventListener("change",async e=>{
  const file=e.target.files?.[0];if(!file)return;
  try{const data=JSON.parse(await file.text());if(map.isStyleLoaded())render(data);else map.once("load",()=>render(data))}
  catch(err){status.textContent="No se pudo cargar: "+err.message}
});
