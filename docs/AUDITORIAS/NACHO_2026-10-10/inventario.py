"""Inventario independiente de investigación DDD/Nacho, 1.0.0, 2026-10-10.
No ejecuta notebooks ni imprime configuración de conexión o consultas.
"""
import ast
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path('/Users/macbookpro/Desarrollo/DDD-distritos-autonomicos')
REF = Path('/private/tmp/nplaton-diputado-distrito')
OUT = Path(sys.argv[1]) if len(sys.argv)>1 else Path(tempfile.mkdtemp(prefix='ddd-nacho-inventory-'))
OUT.mkdir(parents=True, exist_ok=True)
def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])
def sha(b): return hashlib.sha256(b).hexdigest()
def dump(name, obj):
    (OUT/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n')

paths = git(REF, 'ls-tree','-r','--name-only','HEAD').decode().splitlines()
commits = git(REF,'rev-list','--reverse','--all').decode().splitlines()
all_paths = set()
history=[]
for commit in commits:
    tree=git(REF,'ls-tree','-r','--name-only',commit).decode().splitlines()
    all_paths.update(tree)
    notebook=git(REF,'show',commit+':diputado-distrito.ipynb')
    nb=json.loads(notebook)
    cells=[]
    for i,c in enumerate(nb['cells']):
        src=''.join(c.get('source',[]))
        # Solo fuente algorítmica; no reproducir conexiones ni consultas antiguas.
        relevant=any(s in src for s in ['recursive_tree_part','MarkovChain(', 'partial(', 'graph.islands','node_connected_component','flipstep','residuals','municipality_agg','grouped_islands','Watchdog','random.seed','random.random.seed','pop_col='])
        safe=relevant and not any(s in src for s in ['psql_config','password','create_engine','query =','from_postgis'])
        mechanisms={term:[n for n,line in enumerate(src.splitlines(),1) if term in line] for term in ['recursive_tree_part','MarkovChain','recom','graph.islands','node_connected_component','flipstep','residuals','municipality_agg','grouped_islands','Watchdog','random.random.seed','dissolve'] if term in src}
        cells.append({'cell':i,'type':c['cell_type'],'lines':len(src.splitlines()),'source_sha256':sha(src.encode()),'execution_count':c.get('execution_count'),'output_types':[x.get('output_type') for x in c.get('outputs',[])],'mechanisms':mechanisms})
    config=None
    if 'config.py' in tree:
        config={}
        for stmt in ast.parse(git(REF,'show',commit+':config.py').decode()).body:
            if isinstance(stmt,ast.Assign):
                try: value=ast.literal_eval(stmt.value)
                except (ValueError,TypeError): continue
                for target in stmt.targets:
                    if isinstance(target,ast.Name):config[target.id]=value
    history.append({'commit':commit,'metadata':git(REF,'show','-s','--format=%cs %s',commit).decode().strip(),'tree':tree,'notebook_sha256':sha(notebook),'cells':cells,'config':config})
dump('historial.json',{'schema':'ddd.nacho-history/1.0','ref_head':git(REF,'rev-parse','HEAD').decode().strip(),'shallow':git(REF,'rev-parse','--is-shallow-repository').decode().strip(),'commit_count':len(commits),'all_paths':sorted(all_paths),'license_paths':[p for p in all_paths if any(x in p.lower() for x in ['license','licence','copying'])],'history':history})

pre={}
status=git(ROOT,'status','--porcelain=v1').decode()
for l in status.splitlines():
    p=l[3:]
    if p.startswith('docs/AUDITORIAS/NACHO_2026-10-10'):continue
    f=ROOT/p
    pre[p]={'status':l[:2],'sha256':sha(f.read_bytes()) if f.is_file() else None}
sources={p:sha((REF/p).read_bytes()) for p in paths}
ddd_sources={}
for folder in ['ddd_core','ddd_ensemble','modulos','herramientas','visor']:
    for f in sorted((ROOT/folder).rglob('*')):
        if f.is_file() and f.suffix in ['.py','.js','.css','.html'] and '__pycache__' not in str(f):
            ddd_sources[str(f.relative_to(ROOT))]=sha(f.read_bytes())
dump('manifiesto-inicio.json',{'schema':'ddd.nacho-research/1.0','date':'2026-10-10','ddd_root':str(ROOT),'ddd_branch':git(ROOT,'branch','--show-current').decode().strip(),'ddd_head':git(ROOT,'rev-parse','HEAD').decode().strip(),'ddd_tree':git(ROOT,'rev-parse','HEAD^{tree}').decode().strip(),'reference_root':str(REF),'reference_head':git(REF,'rev-parse','HEAD').decode().strip(),'reference_sources_sha256':sources,'preexisting_worktree':pre,'ddd_sources_sha256':ddd_sources,'authorization':'Investigación y pruebas aisladas; sin cambios funcionales productivos ni campañas territoriales','control_note':'DDD-control solo lectura por sandbox; checkpoint nuevo conservado aquí; ningún estado maestro modificado'})

# Examinar binario retirado sin extraerlo ni cargarlo como fuente DDD.
blob=git(REF,'show','d80000b:data.zip')
with zipfile.ZipFile(io.BytesIO(blob)) as z:
    members=[{'path':x.filename,'bytes':x.file_size,'compressed_bytes':x.compress_size,'crc':x.CRC,'encrypted':bool(x.flag_bits & 1)} for x in z.infolist()]
    try: zip_error=z.testzip()
    except RuntimeError: zip_error='BLOCKED_ENCRYPTED_MEMBER_NO_PASSWORD'
dump('archivo-historico.json',{'origin':'d80000b:data.zip','sha256':sha(blob),'bytes':len(blob),'crc_test':zip_error,'members':members,'current_official_source':False,'execution':False})
print(json.dumps({'out':str(OUT),'commits':len(commits),'paths':sorted(all_paths),'zip_members':members,'preexisting_files':len(pre)},ensure_ascii=False))
