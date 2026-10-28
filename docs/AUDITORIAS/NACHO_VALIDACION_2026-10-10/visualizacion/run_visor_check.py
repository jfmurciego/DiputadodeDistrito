#!/usr/bin/env python3
"""V1.0.0, 2026-10-10. Extract exact pure current visor functions; bounded JSC test."""
import hashlib,json,resource,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
APP=Path('/Users/macbookpro/Desarrollo/DDD-distritos-autonomicos/visor/app.js')
INDEX=APP.parent/'index.html'
JSC='/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={str(APP):sha(APP),str(INDEX):sha(INDEX)}
lines=APP.read_text().splitlines()
assert lines[10].startswith('const scalar=') and lines[11].startswith('const formatNumber=') and lines[12].startswith('const formatPercent=')
assert lines[68].startswith('function districtHtml(') and lines[76]=='}'
fragment='\n'.join(lines[10:13]+lines[68:77])+'\n'
(ROOT/'visor_pure_functions.js').write_text(fragment)
def limits():
 resource.setrlimit(resource.RLIMIT_CPU,(55,55))
 resource.setrlimit(resource.RLIMIT_DATA,(640*1024*1024,640*1024*1024))
cmd=[JSC,str(ROOT/'visor_check.js')]
start=time.perf_counter();r=subprocess.run(cmd,capture_output=True,text=True,timeout=60,preexec_fn=limits)
(ROOT/'visor_check.stderr.log').write_text(r.stderr)
(ROOT/'visor_check_results.json').write_text(r.stdout)
assert r.returncode==0,r.stderr
tests=json.loads(r.stdout);assert tests['case_count']==12
assert before=={str(APP):sha(APP),str(INDEX):sha(INDEX)}
result={'command':cmd,'seconds':time.perf_counter()-start,'exit_code':r.returncode,
 'peak_child_RSS_bytes':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
 'timeout_seconds':60,'memory_DATA_limit_bytes':640*1024*1024,'source_sha256':before,
 'extraction_source_lines':{'helpers':[11,13],'districtHtml':[69,77]},
 'extraction_sha256':sha(ROOT/'visor_pure_functions.js'),'source_unchanged':True,
 'render_browser':False,'new_territorial_candidates':False,'cases':12}
(ROOT/'visor_execution.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
