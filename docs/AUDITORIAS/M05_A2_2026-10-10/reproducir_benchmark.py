import json, pathlib, sys, time, resource
ROOT=pathlib.Path('/Users/macbookpro/Desarrollo/DDD-distritos-autonomicos')
sys.path.insert(0,str(ROOT))
sys.path.insert(0,'/private/tmp/MADRID-M05-REPAIR-EXPERIMENT')
from madrid110 import case,kw,base,S,pops,check
from ddd_core import m05_population_repair as c
limits=c.SearchLimits(max_seconds=180,expanded_max_seconds=180,expanded_max_states=400000,
    expanded_max_memory_mib=640,expanded_max_depth=96,expanded_beam_per_district=2,
    expanded_beam_width=128,expanded_max_radius=8)
started=time.monotonic()
cpu_started=time.process_time()
fixed,steps,meta=c._expanded_hard_search(**{k:v for k,v in kw.items() if k!='assignments'},
    state=S,limits=limits)
result={'elapsed_wall':time.monotonic()-started,'cpu_seconds':time.process_time()-cpu_started,'max_rss_platform_units':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'meta':meta,'steps':steps,
    'populations':{str(k):v for k,v in pops(fixed).items()},
    'constraints':check(fixed),'assignments':{str(k):v for k,v in fixed.items()}}
pathlib.Path('/private/tmp/madrid110-a2-result-v18.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({k:result[k] for k in ('elapsed_wall','meta','constraints')},ensure_ascii=False))
