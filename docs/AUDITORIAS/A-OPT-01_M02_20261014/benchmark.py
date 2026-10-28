import hashlib, importlib.util, json, platform, statistics, sys, time, tracemalloc
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('ddd_m02_benchmark', ROOT/'modulos/02_construir_adyacencias.py')
M02 = importlib.util.module_from_spec(spec); spec.loader.exec_module(M02)
old_spec = importlib.util.spec_from_file_location('ddd_m02_legacy_benchmark', ROOT/'legacy/modulo02/02_construir_adyacencias_v7.3.2.py')
OLD_M02 = importlib.util.module_from_spec(old_spec); old_spec.loader.exec_module(OLD_M02)

def section(outer, holes=()):
    return Polygon(outer, holes=holes)

features=[]
# Two large, adjacent polygons; each has 56 non-touching section fragments in holes.
for side, x0 in [('L',0),('R',100)]:
    holes=[]
    inner=[]
    for ix in range(7):
        for iy in range(8):
            cx=x0+32+ix*5; cy=30+iy*5
            holes.append([(cx-1.4,cy-1.4),(cx+1.4,cy-1.4),(cx+1.4,cy+1.4),(cx-1.4,cy+1.4),(cx-1.4,cy-1.4)])
            inner.append((f'{side}F{ix:02d}{iy:02d}',Polygon([(cx-.5,cy-.5),(cx+.5,cy-.5),(cx+.5,cy+.5),(cx-.5,cy+.5)])))
    if side=='L': outer=[(0,0),(100,0),(100,100),(0,100),(0,0)]
    else: outer=[(100,0),(200,0),(200,100),(100,100),(100,0)]
    features.append((f'{side}BIG',section(outer,holes)))
    features.extend(inner)
gdf=gpd.GeoDataFrame({'CUSEC_KEY':[x[0] for x in features]},geometry=[x[1] for x in features],crs='EPSG:3035')

def m02(max_candidates):
    return sorted(m02_module_edges(gdf,max_candidates))

def m02_module_edges(frame,limit):
    return M02.iter_edges(frame,'CUSEC_KEY','contact',1.0,1.0,0.0,0.0,limit,0,'EPSG:3035')

def legacy_module_edges(frame,limit):
    return OLD_M02.iter_edges(frame,'CUSEC_KEY','contact',1.0,1.0,0.0,0.0,limit,0,'EPSG:3035')

def strtree_exact(frame):
    # Isolated prototype: vectorized STRtree candidate enumeration; exact M02 predicate remains authoritative.
    work=frame.to_crs('EPSG:3035').reset_index(drop=True)
    geoms=list(work.geometry)
    ids=work['CUSEC_KEY'].astype(str).tolist()
    tree=__import__('shapely').STRtree(geoms)
    pairs=tree.query(geoms,predicate='intersects')
    candidate_pairs={(int(i),int(j)) for i,j in zip(pairs[0],pairs[1]) if i<j}
    accepted=[]
    checks=0
    for i,j in sorted(candidate_pairs):
        checks+=1
        if M02._relation_ok(geoms[i],geoms[j],'contact',1.0,1.0):
            accepted.append(tuple(sorted((ids[i],ids[j]))))
    return sorted(set(accepted)),len(candidate_pairs),checks


def timed(fn, reps=5):
    times=[]; result=None
    tracemalloc.start()
    for _ in range(reps):
        start=time.perf_counter(); result=fn(); times.append(time.perf_counter()-start)
    _, peak=tracemalloc.get_traced_memory(); tracemalloc.stop()
    return {'times_s':times,'median_s':statistics.median(times),'peak_python_bytes':peak,'result':result}

exhaustive=timed(lambda:m02(0))
limited=timed(lambda:m02(50))
legacy_limited=timed(lambda:sorted(legacy_module_edges(gdf,50)))
proto=timed(lambda:strtree_exact(gdf))
expected=exhaustive['result']; actual=proto['result'][0]
report={
 'schema':'ddd.a-opt-01.synthetic-benchmark.v1',
 'runtime':{'python':platform.python_version(),'geopandas':gpd.__version__,'shapely':__import__('shapely').__version__},
 'code':{'m02_sha256':hashlib.sha256((ROOT/'modulos/02_construir_adyacencias.py').read_bytes()).hexdigest(),'legacy_v732_sha256':hashlib.sha256((ROOT/'legacy/modulo02/02_construir_adyacencias_v7.3.2.py').read_bytes()).hexdigest()},
 'fixture':{'features':len(gdf),'large_adjacent_sections':2,'hole_fill_sections':112,'crs':gdf.crs.to_string(),'purpose':'adversarial candidate-cap completeness fixture; synthetic and not a territorial input'},
 'budget':{'max_wall_seconds':60,'runs_per_variant':5,'max_candidates_under_test':50},
 'variants':{
   'm02_exhaustive':{k:v for k,v in exhaustive.items() if k!='result'}|{'edges':expected},
   'm02_max_candidates_50':{k:v for k,v in limited.items() if k!='result'}|{'edges':limited['result']},
   'legacy_v7_3_2_max_candidates_50':{k:v for k,v in legacy_limited.items() if k!='result'}|{'edges':legacy_limited['result']},
   'strtree_exact_prototype':{k:v for k,v in proto.items() if k!='result'}|{'edges':actual,'candidate_pairs':proto['result'][1],'exact_predicate_checks':proto['result'][2]},
 },
 'comparisons':{'legacy_v732_max50_missing_edges':sorted(set(expected)-set(legacy_limited['result'])),'current_max50_missing_edges':sorted(set(expected)-set(limited['result'])),'current_max50_extra_edges':sorted(set(limited['result'])-set(expected)),'prototype_equals_exhaustive':actual==expected,'prototype_deterministic':all(strtree_exact(gdf)[0]==actual for _ in range(2))},
 'limitations':['Synthetic adversarial fixture only; authentic M01 geometry is unavailable locally.','Peak Python allocations exclude GEOS/native allocations and are not a process RSS measurement.','No authentic territorial runtime, RSS, serialization or topology result is claimed.']
}
print(json.dumps(report,indent=2,sort_keys=True))
