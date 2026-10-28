#!/usr/bin/env python3
"""V1.0.0; bounded local JavaScriptCore execution, no browser/no network."""
import json,resource,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
JSC='/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc'
def limits():
    resource.setrlimit(resource.RLIMIT_CPU,(55,55))
    resource.setrlimit(resource.RLIMIT_DATA,(640*1024*1024,640*1024*1024))
start=time.perf_counter()
cmd=[JSC,str(ROOT/'dom_simulation.js')]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=60,preexec_fn=limits)
(ROOT/'dom_simulation.stderr.log').write_text(r.stderr)
(ROOT/'dom_simulation_results.json').write_text(r.stdout)
metrics={'command':cmd,'seconds':time.perf_counter()-start,'exit_code':r.returncode,
         'peak_child_RSS_bytes':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
         'memory_limit_DATA_bytes':640*1024*1024,'timeout_seconds':60,
         'DOM_simulated':True,'MapLibre_simulated':True,'render_browser':False}
(ROOT/'js_execution.json').write_text(json.dumps(metrics,indent=2))
assert r.returncode==0,r.stderr
json.loads(r.stdout)
print(json.dumps(metrics,indent=2))
