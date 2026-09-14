from __future__ import annotations

import json
import shutil
from pathlib import Path


HTML = """<!doctype html>
<html lang=\"es\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>DDD · Revisión territorial</title><link href=\"https://unpkg.com/maplibre-gl@5.6.0/dist/maplibre-gl.css\" rel=\"stylesheet\"><link rel=\"stylesheet\" href=\"style.css\"></head>
<body><header><h1>Revisión de alternativas territoriales</h1><p id=\"meta\"></p></header>
<main><section class=\"toolbar\"><label>Perfil <select id=\"profile\"><option value=\"\">Todos</option></select></label>
<label><input id=\"pareto\" type=\"checkbox\"> Solo frente de Pareto</label><button id=\"download\">Descargar selection.json</button></section>
<section class=\"compare\"><div><label>Mapa A <select id=\"compareA\"></select></label><div id=\"mapA\" class=\"map\"></div></div>
<div><label>Mapa B <select id=\"compareB\"></select></label><div id=\"mapB\" class=\"map\"></div></div></section>
<section id=\"cards\" class=\"cards\"></section><section class=\"decision\"><h2>Decisión de campo</h2>
<label>Candidato <select id=\"selected\"><option value=\"\">Sin seleccionar</option></select></label>
<label>Responsable <input id=\"reviewer\"></label><label>Justificación <textarea id=\"reason\"></textarea></label></section></main>
<script src=\"https://unpkg.com/maplibre-gl@5.6.0/dist/maplibre-gl.js\"></script><script src=\"app.js\"></script></body></html>"""

CSS = """body{font-family:system-ui;margin:0;color:#172033;background:#f5f7fa}header,main{max-width:1200px;margin:auto;padding:1rem 1.5rem}header{background:#14213d;color:white;max-width:none}header>*{max-width:1200px;margin-left:auto;margin-right:auto}.toolbar{display:flex;gap:1rem;align-items:center;flex-wrap:wrap}.compare{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:1rem}.compare>div{background:white;padding:.75rem}.map{height:430px;margin-top:.5rem;background:#e8edf3}.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem;margin-top:1rem}.card{background:white;border:1px solid #d8dee9;border-radius:8px;padding:1rem}.card.pareto{border-left:6px solid #2a9d8f}.metric{display:flex;justify-content:space-between;border-bottom:1px solid #eee;padding:.25rem 0}.decision{margin-top:2rem;background:white;padding:1rem}.decision label{display:block;margin:.75rem 0}.decision input,.decision textarea,.decision select{width:100%;max-width:700px;padding:.5rem}button{padding:.6rem 1rem;background:#14213d;color:white;border:0;border-radius:4px;cursor:pointer}small{color:#52606d}@media(max-width:760px){.compare{grid-template-columns:1fr}.map{height:340px}}"""

JS = r"""let DATA,maps={};const palette=['#264653','#2a9d8f','#e9c46a','#f4a261','#e76f51','#457b9d','#8d5a97','#588157','#bc6c25','#6d597a'];const fmt=n=>Number(n).toFixed(3);
async function load(){DATA=await(await fetch('data/summary.json')).json();meta.textContent=`${DATA.territory_id} · ${DATA.candidate_count_valid}/${DATA.candidate_count_expected} candidatos válidos · selección de campo pendiente`;const profiles=[...new Set(DATA.candidates.map(c=>c.profile))];profiles.forEach(p=>profile.add(new Option(p,p)));DATA.candidates.forEach(c=>{selected.add(new Option(c.candidate_id,c.candidate_id));compareA.add(new Option(c.candidate_id,c.candidate_id));compareB.add(new Option(c.candidate_id,c.candidate_id));});compareB.selectedIndex=Math.min(1,DATA.candidates.length-1);render();draw('mapA',compareA.value);draw('mapB',compareB.value);}
function coords(g,out=[]){if(typeof g[0]==='number')out.push(g);else g.forEach(x=>coords(x,out));return out}
async function draw(container,id){let c=DATA.candidates.find(x=>x.candidate_id===id);if(!c||!c.asset)return;let geo=await(await fetch(c.asset)).json();if(maps[container])maps[container].remove();let all=coords(geo.features.map(f=>f.geometry.coordinates)),xs=all.map(p=>p[0]),ys=all.map(p=>p[1]);let field=(c.fields&&c.fields.district)||'district_id',values=[...new Set(geo.features.map(f=>String(f.properties[field])))],match=['match',['to-string',['get',field]]];values.forEach((v,i)=>match.push(v,palette[i%palette.length]));match.push('#999');let map=maps[container]=new maplibregl.Map({container,style:{version:8,sources:{candidate:{type:'geojson',data:geo}},layers:[{id:'fill',type:'fill',source:'candidate',paint:{'fill-color':match,'fill-opacity':.65}},{id:'line',type:'line',source:'candidate',paint:{'line-color':'#172033','line-width':1}}]},attributionControl:false});map.fitBounds([[Math.min(...xs),Math.min(...ys)],[Math.max(...xs),Math.max(...ys)]],{padding:18,duration:0});map.addControl(new maplibregl.NavigationControl(),'top-right');}
function render(){const only=pareto.checked,p=profile.value,front=new Set(DATA.pareto_candidates);cards.innerHTML='';DATA.candidates.filter(c=>(!p||c.profile===p)&&(!only||front.has(c.candidate_id))).forEach(c=>{let m=c.metrics;let el=document.createElement('article');el.className='card '+(front.has(c.candidate_id)?'pareto':'');el.innerHTML=`<h2>${c.candidate_id}</h2><small>${c.profile} · semilla ${c.seed}</small><div class=metric><span>Desviación población</span><b>${fmt(m.population.max_deviation)}</b></div><div class=metric><span>PP mediana</span><b>${fmt(m.shape.polsby_popper_median)}</b></div><div class=metric><span>Elongación máx.</span><b>${fmt(m.shape.elongation_max)}</b></div><div class=metric><span>Retención comarca</span><b>${fmt(m.comarca.retention_ratio)}</b></div><div class=metric><span>Comarcas divididas</span><b>${m.comarca.split_count}</b></div><div class=metric><span>Alertas corredor</span><b>${m.shape.corridor_alerts.length}</b></div><p><a href="${c.asset||'#'}">Abrir GeoJSON</a></p><button data-id="${c.candidate_id}">Seleccionar</button>`;el.querySelector('button').onclick=()=>selected.value=c.candidate_id;cards.append(el);});}
profile.onchange=render;pareto.onchange=render;compareA.onchange=()=>draw('mapA',compareA.value);compareB.onchange=()=>draw('mapB',compareB.value);download.onclick=()=>{let out={schema:'ddd.selection/1.0',territory_id:DATA.territory_id,prepared_bundle_id:DATA.prepared_bundle_id,candidate_id:selected.value,reviewer:reviewer.value,justification:reason.value,status:selected.value?'SELECTED_FOR_PROMOTION':'NO_SELECTION'};let a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(out,null,2)],{type:'application/json'}));a.download='selection.json';a.click();};load();"""


def build_gallery(summary_path: str, output_dir: str) -> Path:
    summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    output = Path(output_dir)
    data_dir = output / "data"
    assets_dir = output / "assets"
    data_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    portable = dict(summary)
    portable_candidates = []
    for candidate in summary.get("candidates", []):
        item = dict(candidate)
        source = candidate.get("geojson")
        if source and Path(source).is_file():
            destination = assets_dir / f"{candidate['candidate_id']}.geojson"
            shutil.copy2(source, destination)
            item["asset"] = f"assets/{destination.name}"
        portable_candidates.append(item)
    portable["candidates"] = portable_candidates
    (data_dir / "summary.json").write_text(json.dumps(portable, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "index.html").write_text(HTML, encoding="utf-8")
    (output / "style.css").write_text(CSS, encoding="utf-8")
    (output / "app.js").write_text(JS, encoding="utf-8")
    return output / "index.html"
