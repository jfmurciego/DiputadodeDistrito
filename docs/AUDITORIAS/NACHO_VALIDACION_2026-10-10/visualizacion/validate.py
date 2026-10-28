#!/usr/bin/env python3
"""V1.0.0 2026-10-10; isolated validation of frozen candidates, no new partitions."""
import hashlib, html, importlib.util, json, os, platform, resource, shutil
import signal, subprocess, sys, time
from pathlib import Path
sys.dont_write_bytecode=True
from shapely.geometry import box, mapping
from shapely import union_all
from pyproj import Transformer

ROOT=Path(__file__).resolve().parent
DDD=Path('/Users/macbookpro/Desarrollo/DDD-distritos-autonomicos')
SOURCE=DDD/'docs/AUDITORIAS/NACHO_2026-10-10/experimentos'
CHROME='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
PALETTE=['#264653','#2a9d8f','#e9c46a','#f4a261']

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False))
def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()
def load_module(name,p):
    spec=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def provenance_snapshot():
    paths=[SOURCE/'results.json',SOURCE/'ranking_plan.json',SOURCE/'ensemble_summary.json',
           SOURCE/'experiments.py',DDD/'ddd_ensemble/ensemble_assembler.py',DDD/'ddd_ensemble/gallery.py',
           DDD/'docs/AUDITORIAS/NACHO_2026-10-10/INFORME.md']
    paths+=list((SOURCE/'ranking_reports').rglob('report.json'))
    return {str(p):sha(p) for p in paths}

def svg(name,assignment):
    cells=[]
    for i,d in enumerate(assignment):
        x,y=i%4,i//4
        cells.append(f'<rect x="{x*80}" y="{y*80}" width="80" height="80" fill="{PALETTE[d]}" data-section="{i}" data-district="{d}"/><text x="{x*80+40}" y="{y*80+45}" text-anchor="middle" fill="white">s{i} · d{d}</text>')
    return f'<svg aria-label="{name} · mismo universo sintético" viewBox="0 0 320 320"><g>{"".join(cells)}</g><g class="grid-lines" stroke="#172033" fill="none">'+''.join(f'<path d="M{n*80},0V320M0,{n*80}H320"/>' for n in range(5))+'</g></svg>'

def offline_diagnostic(details,assignments,provenance):
    parts=[]
    for name in ['A_lower_L1','B_lower_max']:
        m=details[name]
        rows=''.join(f'<tr><td>{d}</td><td>{p}</td><td>800</td><td>1750</td><td>800–1200</td><td>{abs(p-1000)/10:.1f}%</td><td>{str(abs(p-1000)>200).lower()}</td><td>0</td><td>Ninguno</td></tr>' for d,p in enumerate(m['population']))
        parts.append(f'<article id="{name}"><h2>{name}</h2>{svg(name,assignments[name])}<p>L1={m["L1"]}; máximo={m["max_relative"]:.0%}; PP mediana={m["shape_polsby_popper_median"]:.6f}; retención comarcal=100%; municipios divididos=0.</p><table><thead><tr><th>Distrito</th><th>Población</th><th>Floor</th><th>Cap</th><th>Banda dura</th><th>Desviación</th><th>Outlier</th><th>Municipios divididos</th><th>Incumplimientos</th></tr></thead><tbody>{rows}</tbody></table></article>')
    c=details['C_hard_invalid']
    crows=''.join(f'<tr><td>{d}</td><td>{p}</td><td>800</td><td>1750</td><td>800–1200</td><td>{abs(p-1000)/10:.1f}%</td><td>{str(abs(p-1000)>200).lower()}</td><td>0</td><td>{"; ".join(v for v in c["violations"] if v.endswith(":"+str(d))) or "Ninguno"}</td></tr>' for d,p in enumerate(c['population']))
    text=f'''<!doctype html><html lang="es"><meta charset="utf-8"><title>Diagnóstico congelado Nacho–DDD</title><style>body{{font:15px system-ui;margin:2rem;color:#172033}}.maps{{display:grid;grid-template-columns:1fr 1fr;gap:2rem}}svg{{max-width:400px;width:100%}}table{{border-collapse:collapse;font-size:12px}}th,td{{border:1px solid #aaa;padding:.4rem}}.reject{{background:#ffe9e9;padding:1rem}}label{{margin-right:1rem}}.hide-grid .grid-lines{{display:none}}@media(max-width:900px){{.maps{{grid-template-columns:1fr}}}}</style>
<h1>Comparación de los candidatos existentes A y B</h1><p>DIAGNÓSTICO SINTÉTICO · misma geometría/universo · K4 · P4000 · target1000 · tolerancia dura±20% · ninguna certificación ni promoción.</p>
<label><input type="checkbox" id="sections" checked>Mostrar fronteras sección/unidad/municipio (coinciden en este fixture)</label><label><input type="checkbox" id="showInvalid" checked>Mostrar candidato rechazado</label>
<section class="maps">{''.join(parts)}</section><section id="ranking"><h2>Explicación de selección y Pareto</h2><p>B reduce el máximo relativo del15% al10%. Mantiene igual compactación0,502655, retención comarcal1, alertas0 y assignment_delta0 del informe de ensemble. Por ello domina A en los cinco objetivos del ensamblador; B es el único Pareto y el primer shortlist. L1 histórico preferiría A (300 frente400), pero no es el objetivo de este ensamblador. A sigue siendo admisible; no se altera el score.</p><p>Selección técnica B · selección de campo PENDING_FIELD_REVIEW. El cambio de assignment real del motor tiene churn distinto: no confundirlo con assignment_delta0 congelado del report de ensemble.</p></section>
<section id="invalid" class="reject"><h2>C_hard_invalid: RECHAZADO, sin opción de promoción</h2><p>Universo/K conservados; fallos: {html.escape('; '.join(c['violations']))}. No aparece en shortlist ni controles de selección. Sólo se conserva aquí como evidencia negativa.</p><table><thead><tr><th>Distrito</th><th>Población</th><th>Floor</th><th>Cap</th><th>Banda dura</th><th>Desviación</th><th>Outlier</th><th>Municipios divididos</th><th>Incumplimientos</th></tr></thead><tbody>{crows}</tbody></table></section>
<h2>Capas y trazabilidad</h2><p>Secciones, unidades y municipios:16 elementos idénticos en este fixture. Distritos:4 por alternativa. Provincia:universo completo. Comarcas:singleton. No hay capa de códigos postales ni datos reales; no se fabrica. Ideas históricas de Kepler/GeoJSON/Excel tomadas del informe ya acreditado, sin cargar datos históricos ni añadir dependencias.</p><p>Las SVG usan coordenadas cartesianas locales originales; GeoJSON web tiene embedding sintético explícito y no es una fuente oficial.</p><p><a href="comparison.csv">Tabla CSV</a> · <a href="provenance.json">Proveniencia SHA y configuración</a> · <a href="gallery/index.html">Galería DDD generada sin cambios (MapLibre CDN)</a></p><script>sections.onchange=()=>document.body.classList.toggle('hide-grid',!sections.checked);showInvalid.onchange=()=>invalid.hidden=!showInvalid.checked;</script></html>'''
    (ROOT/'diagnostico.html').write_text(text)
    lines=['candidate,district,population,floor,cap,tolerance_min,tolerance_max,outlier,municipality_splits,violations']
    for name,m in details.items():
        for d,p in enumerate(m['population']):
            violations=';'.join(v for v in m['violations'] if v.endswith(':'+str(d)))
            lines.append(f'{name},{d},{p},800,1750,800,1200,{abs(p-1000)>200},0,{violations}')
    (ROOT/'comparison.csv').write_text('\n'.join(lines)+'\n')

HARNESS=r'''<script>
window.mapCalls=[];window.downloadedSelections=[];
window.maplibregl={Map:class{constructor(o){mapCalls.push(o)}remove(){}fitBounds(b){this.bounds=b}addControl(){}},NavigationControl:class{}};
URL.createObjectURL=b=>{b.text().then(t=>downloadedSelections.push(JSON.parse(t)));return 'blob:diagnostic';};HTMLAnchorElement.prototype.click=function(){};
async function verify(){if(typeof DATA==='undefined'||!DATA){setTimeout(verify,20);return;}let tests={};tests.initialCards=cards.children.length;tests.initialIDs=[...cards.children].map(x=>x.querySelector('h2').textContent);tests.invalidOptionsAbsent=![...selected.options].some(o=>o.value==='C_hard_invalid');tests.mapsLoaded=mapCalls.length;pareto.checked=true;pareto.onchange();tests.paretoIDs=[...cards.children].map(x=>x.querySelector('h2').textContent);pareto.checked=false;pareto.onchange();profile.value='';profile.onchange();cards.children[1].querySelector('button').onclick();tests.selected=selected.value;reviewer.value='DIAGNOSTIC_ONLY';reason.value='Fixture congelado; ninguna promoción autorizada';download.onclick();await new Promise(r=>setTimeout(r,20));tests.downloaded=downloadedSelections;tests.visibleLabels=[...cards.querySelectorAll('.metric span')].map(x=>x.textContent);tests.visibleCardText=cards.textContent;tests.maps=mapCalls.map(o=>({container:o.container,featureCount:o.style.sources.candidate.data.features.length}));let p=document.createElement('pre');p.id='test-results';p.textContent=JSON.stringify(tests);document.body.appendChild(p);}
window.addEventListener('load',()=>setTimeout(verify,200));
</script>'''

def chrome_dump(url,label):
    cmd=[CHROME,'--headless=new','--no-sandbox','--disable-gpu','--disable-background-networking',
         '--disable-component-update','--disable-sync','--disable-extensions','--no-first-run',
         '--disable-breakpad','--host-resolver-rules=MAP * ~NOTFOUND','--allow-file-access-from-files',
         '--user-data-dir='+str(ROOT/('browser_'+label)),'--dump-dom','--virtual-time-budget=1500',url]
    out=ROOT/(label+'.dom.html');err=ROOT/(label+'.stderr.log')
    started=time.perf_counter();peak=0
    with out.open('w') as o,err.open('w') as e:
        p=subprocess.Popen(cmd,stdout=o,stderr=e,start_new_session=True)
        while p.poll() is None:
            try:
                ps=subprocess.run(['/bin/ps','-axo','pgid=,rss='],capture_output=True,text=True,timeout=3)
            except PermissionError:
                try: os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError: pass
                p.wait()
                return {'status':'BLOCKED_SANDBOX','reason':'Process memory inspection unavailable (ps EPERM); Chrome bootstrap denied by sandbox; no browser rendering claimed','seconds':time.perf_counter()-started,'command':cmd}
            rss=sum(int(line.split()[1])*1024 for line in ps.stdout.splitlines() if len(line.split())==2 and line.split()[0]==str(p.pid))
            peak=max(peak,rss)
            if rss>640*1024*1024 or time.perf_counter()-started>45:
                os.killpg(p.pid,signal.SIGKILL);p.wait();return {'status':'LIMIT_REACHED','peak_process_group_RSS_bytes':peak,'seconds':time.perf_counter()-started,'command':cmd}
            time.sleep(.1)
    return {'status':'COMPLETED' if p.returncode==0 else 'FAILED','exit_code':p.returncode,
            'peak_process_group_RSS_bytes':peak,'seconds':time.perf_counter()-started,'command':cmd}

def main():
    started=time.perf_counter();before=provenance_snapshot()
    shutil.copytree(SOURCE/'ranking_reports',ROOT/'copied_reports',dirs_exist_ok=True)
    for name in ['results.json','ranking_plan.json','ensemble_summary.json']:
        shutil.copy2(SOURCE/name,ROOT/('frozen_'+name))
    frozen=json.loads((SOURCE/'results.json').read_text())['ranking'];matrix=frozen['cell_population_matrix']
    populations=[p for row in matrix for p in row]
    assignments={'A_lower_L1':[y for y in range(4) for x in range(4)],
                 'B_lower_max':[x for y in range(4) for x in range(4)]}
    assignments['C_hard_invalid']=list(assignments['A_lower_L1']);assignments['C_hard_invalid'][4]=assignments['C_hard_invalid'][5]=0
    geoms=[box(x,y,x+1,y+1) for y in range(4) for x in range(4)]
    forward=Transformer.from_crs(4326,3857,always_xy=True);reverse=Transformer.from_crs(3857,4326,always_xy=True)
    anchor=forward.transform(-3.7,40.4)
    details={};hashes={}
    for name,a in assignments.items():
        assert digest(a)==frozen['candidates'][name]['assignment_sha256']
        report=json.loads((ROOT/'copied_reports'/name/'report.json').read_text())
        assert report['assignment_hash']==digest(a)
        hashes[name]=digest(a);ds=[union_all([g for g,d in zip(geoms,a) if d==i]) for i in range(4)]
        assert [sum(p for p,d in zip(populations,a) if d==i) for i in range(4)]==frozen['candidates'][name]['population']
        features=[];webfeatures=[]
        for i,g in enumerate(geoms):
            props={'section_id':str(i),'district_id':a[i],'population':populations[i],'municipality':str(i),'ddd_unit_id':str(i),'comarca':str(i),'province':'SYNTHETIC'}
            f={'type':'Feature','properties':props,'geometry':mapping(g)};features.append(f)
            def coord(v):
                if isinstance(v,(list,tuple)) and len(v)>=2 and isinstance(v[0],(int,float)):
                    return list(reverse.transform(anchor[0]+v[0],anchor[1]+v[1]))
                return [coord(x) for x in v]
            webfeatures.append({'type':'Feature','properties':props,'geometry':{'type':g.geom_type,'coordinates':coord(mapping(g)['coordinates'])}})
        local={'type':'FeatureCollection','synthetic_crs':'LOCAL:CARTESIAN_FIXTURE','features':features}
        web={'type':'FeatureCollection','synthetic_embedding':{'crs':'EPSG:3857','anchor_lon_lat':[-3.7,40.4],'unit_metre':1,'purpose':'derived illustration, not official geometry'},'features':webfeatures}
        localpath=ROOT/'assets_metric'/f'{name}.geojson';webpath=ROOT/'assets_web'/f'{name}.geojson'
        dump(localpath,local);dump(webpath,web)
        report['geojson']=str(webpath);report['fields']={'district':'district_id'}
        report['metrics']['shape']['elongation_max']=max(max(g.bounds[2]-g.bounds[0],g.bounds[3]-g.bounds[1])/min(g.bounds[2]-g.bounds[0],g.bounds[3]-g.bounds[1]) for g in ds)
        report['metrics']['comarca']['split_count']=0
        report['diagnostic']={'district_population':frozen['candidates'][name]['population'],'population_floor':800,'population_cap':1750,'target':1000,'tolerance_min':800,'tolerance_max':1200,'municipality_splits':0,'violations':frozen['actual_DDD_engine_results'][name]['violations'],'provenance':{'assignment_sha256':digest(a),'source_report_sha256':before[str(SOURCE/'ranking_reports'/name/'report.json')],'metric_geometry_sha256':sha(localpath),'web_geometry_sha256':sha(webpath)}}
        dump(ROOT/'copied_reports'/name/'report.json',report)
        details[name]={**frozen['candidates'][name],'violations':report['diagnostic']['violations']}
    assembler=load_module('real_assembler',DDD/'ddd_ensemble/ensemble_assembler.py')
    gallery=load_module('real_gallery',DDD/'ddd_ensemble/gallery.py')
    t=time.perf_counter();summary=assembler.assemble(str(ROOT/'frozen_ranking_plan.json'),str(ROOT/'copied_reports'),shortlist_size=2);assemble_seconds=time.perf_counter()-t
    original=json.loads((SOURCE/'ensemble_summary.json').read_text())
    for field in ['pareto_candidates','shortlist','invalid_candidates','candidate_count_valid']:
        assert summary[field]==original[field]
    assert summary['shortlist']==['B_lower_max'] and summary['invalid_candidates']==['C_hard_invalid']
    dump(ROOT/'summary.json',summary);t=time.perf_counter();gallery.build_gallery(str(ROOT/'summary.json'),str(ROOT/'gallery'));gallery_seconds=time.perf_counter()-t
    portable=json.loads((ROOT/'gallery/data/summary.json').read_text())
    assert [c['candidate_id'] for c in portable['candidates']]==['A_lower_L1','B_lower_max']
    assert not (ROOT/'gallery/assets/C_hard_invalid.geojson').exists()
    for c in portable['candidates']:
        assert sha(ROOT/'gallery'/c['asset'])==sha(ROOT/'assets_web'/f'{c["candidate_id"]}.geojson')
    prov={'source_sha256':before,'assignment_sha256':hashes,'config_frozen':json.loads((SOURCE/'ranking_plan.json').read_text()),'synthetic_contract':{'K':4,'P':4000,'target':1000,'tolerance':.20,'floor':800,'cap':1750,'municipality_atomicity':True},'assets_are_reconstruction_of_existing_assignments':True,'synthetic_embedding_only_for_web':web['synthetic_embedding']}
    dump(ROOT/'provenance.json',prov);offline_diagnostic(details,assignments,prov)
    harness=gallery.HTML.replace('<link href="https://unpkg.com/maplibre-gl@5.6.0/dist/maplibre-gl.css" rel="stylesheet">','').replace('<script src="https://unpkg.com/maplibre-gl@5.6.0/dist/maplibre-gl.js"></script>',HARNESS)
    assert 'https://' not in harness
    (ROOT/'gallery/dom-harness.html').write_text(harness)
    # Browser startup was attempted once and failed under sandbox. Do not retry.
    browser={'status':'BLOCKED_SANDBOX','reason':'Chrome crashpad bootstrap EPERM; ps EPERM. Prior attempt preserved in gallery_dom.stderr.log. No browser DOM/render.'}
    dom=(ROOT/'gallery_dom.dom.html').read_text()
    marker='<pre id="test-results">';dynamic=None
    if marker in dom:
        dynamic=json.loads(html.unescape(dom.split(marker,1)[1].split('</pre>',1)[0]))
        assert dynamic['initialCards']==2 and dynamic['paretoIDs']==['B_lower_max']
        assert dynamic['invalidOptionsAbsent'] and dynamic['selected']=='B_lower_max'
        assert dynamic['mapsLoaded']==2 and len(dynamic['maps'])==2
        assert dynamic['downloaded'][0]['candidate_id']=='B_lower_max'
    diagnostic_browser={'status':'NOT_EXECUTED','reason':'Same documented sandbox block; no second browser attempted.'}
    dd=(ROOT/'diagnostico.html').read_text()
    offline_checks={'two_svg_maps':dd.count('<svg ')==2,'has_floor_cap_tolerance':'Floor' in dd and 'Cap' in dd and '800–1200' in dd,'has_rejected_C':'C_hard_invalid: RECHAZADO' in dd,'has_population_2000_100':'>2000<' in dd and '>100<' in dd,'has_explanation_Pareto':'domina A' in dd,'has_split_municipalities':'Municipios divididos' in dd}
    assert all(offline_checks.values())
    assert provenance_snapshot()==before
    result={'schema':'ddd.nacho-visual-validation/1.0','scope':'existing frozen candidates only; diagnostic function, not generation or production visor',
            'assembler_seconds':assemble_seconds,'gallery_build_seconds':gallery_seconds,'browser_gallery':browser,'real_app_js_with_MapLibre_stub_DOM':dynamic,'browser_diagnostic':diagnostic_browser,'diagnostic_offline_checks':offline_checks,'source_and_production_files_unchanged':True,
            'original_ranking_unchanged':True,'C_excluded_from_selection':True,
            'baseline_missing_diagnostic_features':['district population table','floor/cap/tolerance shown','municipal splits shown','invalid causes shown','selection objective explanation','config/assignment hashes visible'],
            'classification':'MEJORA_DEMOSTRADA','classification_scope':'additional diagnostic information on frozen fixture, never algorithm benefit or approval to implement',
            'offline_checks_are':'Static HTML checks, not rendered browser DOM',
            'process_peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'python':sys.version,'platform':platform.platform(),'seconds_total':time.perf_counter()-started}
    dump(ROOT/'validation_results.json',result)
    dump(ROOT/'source_unchanged.json',{'before':before,'after':provenance_snapshot(),'equal':True})
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=='__main__':main()
