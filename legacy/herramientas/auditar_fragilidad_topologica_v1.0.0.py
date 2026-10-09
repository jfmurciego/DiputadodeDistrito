#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: auditar_fragilidad_topologica.py
VERSIÓN: 1.0.0
NOMBRE: Auditor global de fragilidad topológica distrital
FECHA: 2026-09-11
ESTADO: diagnóstico; no modifica asignaciones.
FUNCIÓN: medir, para todos los distritos de una solución M04/M05, puntos de articulación a nivel de unidad
DDD y la población de los lóbulos que dependen de cada articulación. Produce una firma topológica comparable.
MOTIVO: EXT-07/08 demostraron que el mínimo residual de Extremadura es topológico. EXT-10 demostró que el
`seed` configurado en M04 v7.4.5 no se consume. Antes de introducir variantes se necesita una función de
medida explícita de robustez topológica que permita comparación A/B reproducible.
ANTERIOR: ninguno — herramienta nueva.
"""
from __future__ import annotations
import argparse, io, json, sys, zipfile
from collections import deque
from pathlib import Path
import geopandas as gpd
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from ddd_core.config import load_params_yaml, module_cfg

def load_geo(path):
    p=Path(path)
    if p.suffix.lower()=='.zip':
        with zipfile.ZipFile(p) as z:
            n=next(n for n in z.namelist() if n.lower().endswith(('.geojson','.json')) and not n.endswith('/'))
            return gpd.read_file(io.BytesIO(z.read(n)))
    return gpd.read_file(p)

def comps(nodes,adj):
    rem=set(nodes); out=[]
    while rem:
        s=min(rem,key=str); rem.remove(s); seen={s}; q=deque([s])
        while q:
            u=q.popleft()
            for v in adj.get(u,set()):
                if v in rem: rem.remove(v); seen.add(v); q.append(v)
        out.append(seen)
    return sorted(out,key=lambda x:(-len(x),min(map(str,x))))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--params',required=True); ap.add_argument('--geojson',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    cfg=load_params_yaml(a.params)
    s5=module_cfg(cfg,'modulo_05_optimizar_distritos','step5_optimize_swaps')
    s4=module_cfg(cfg,'modulo_04_generar_semillas','step4_seed_districts')
    graph_path=s5.get('in_graph_json') or s4.get('in_graph_json')
    G=json.loads(Path(graph_path).read_text(encoding='utf-8'))
    pop={str(n['id']):int(n.get('pop',0)) for n in G['nodes']}; sadj={n:set() for n in pop}
    for e in G['edges']:
        u,v=str(e['u']),str(e['v']); sadj[u].add(v); sadj[v].add(u)
    g=load_geo(a.geojson); idf=s5.get('id_field') or s4.get('id_field','CUSEC_KEY'); did=s5.get('district_field','district_id'); munf=s5.get('municipality_field','CUMUN')
    g[idf]=g[idf].astype(str); g[did]=g[did].astype(int)
    if 'ddd_unit_id' not in g.columns: raise SystemExit('Se requiere ddd_unit_id')
    g['ddd_unit_id']=g['ddd_unit_id'].astype(str)
    sec_unit=dict(zip(g[idf],g.ddd_unit_id)); unit_nodes={u:set(x[idf].astype(str)) for u,x in g.groupby('ddd_unit_id')}; unit_pop={u:sum(pop[n] for n in ns) for u,ns in unit_nodes.items()}; unit_mun={u:sorted(set(x[munf].astype(str))) if munf in x.columns else [] for u,x in g.groupby('ddd_unit_id')}; unit_dist={u:int(x[did].iloc[0]) for u,x in g.groupby('ddd_unit_id')}
    uadj={u:set() for u in unit_nodes}
    for n,u in sec_unit.items():
        for nb in sadj.get(n,set()):
            v=sec_unit.get(nb)
            if v is not None and v!=u:uadj[u].add(v)
    d_units={d:set(x.ddd_unit_id.astype(str)) for d,x in g.groupby(did)}; d_pop={d:sum(unit_pop[u] for u in us) for d,us in d_units.items()}; target=sum(pop.values())/len(d_units)
    rows=[]; total_arts=0; vulnerable_sum=0; max_vulnerable=0
    for d in sorted(d_units):
        us=d_units[d]; ia={u:{v for v in uadj[u] if v in us} for u in us}; arts=[]
        for cut in sorted(us,key=str):
            rest=us-{cut}
            if len(rest)<=1:continue
            cc=comps(rest,ia)
            if len(cc)<=1:continue
            lobes=[]
            for c in cc:
                cp=sum(unit_pop[u] for u in c); lobes.append({'units':sorted(c,key=str),'population':cp,'ratio_target':cp/target,'municipalities':sorted({m for u in c for m in unit_mun[u]})})
            small=min(x['population'] for x in lobes); large=max(x['population'] for x in lobes)
            arts.append({'unit':cut,'population':unit_pop[cut],'municipalities':unit_mun[cut],'lobes':sorted(lobes,key=lambda x:x['population']),'smallest_lobe_population':small,'largest_lobe_population':large})
            vulnerable_sum+=small; max_vulnerable=max(max_vulnerable,small)
        total_arts+=len(arts)
        rows.append({'district':d,'population':d_pop[d],'relative_deviation':(d_pop[d]-target)/target,'unit_count':len(us),'articulation_count':len(arts),'articulations':arts})
    districts_with=sum(bool(r['articulation_count']) for r in rows)
    result={'target':target,'districts':len(rows),'districts_with_articulations':districts_with,'total_articulation_units':total_arts,'smallest_lobes_population_sum':vulnerable_sum,'max_smallest_lobe_population':max_vulnerable,'fragility_signature':[districts_with,total_arts,round(vulnerable_sum/target,12),round(max_vulnerable/target,12)],'detail':rows}
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('districts','districts_with_articulations','total_articulation_units','smallest_lobes_population_sum','max_smallest_lobe_population','fragility_signature')},ensure_ascii=False))
if __name__=='__main__':main()
