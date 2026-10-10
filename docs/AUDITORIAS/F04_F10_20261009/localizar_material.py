"""DDD F04 local material inventory, version 1.0.0, 2026-10-09.
Scope: five missing territorial inputs. Read-only source scan, new evidence only.
Origin: explicit local sources work order; no predecessor.
"""
from pathlib import Path
import json, zipfile, hashlib
OUT=Path(__file__).parent
rows=json.loads((OUT.parent/'fuentes_oficiales_19_territorios_2026-10-08.json').read_text())['territories']
gaps=[r for r in rows if r['territory_id'] in {'andalucia','aragon','castilla_y_leon','comunidad_valenciana','extremadura'}]
hashes={r['territorial_candidate'][k]:r['territory_id'] for r in gaps for k in ['artifact_sha256','package_sha256']}
scan=[];hits=[];errors=[];governance=[]
roots=[Path.home()/'Downloads',Path.home()/'Desarrollo/DDD-almacen',Path('/private/tmp')]
for root in roots:
 for p in root.rglob('*.zip'):
  if any(s in str(p) for s in ['DDD-F03','DDD-F01','ddd-cartografia-venv','/venv/','/repo/','/root/','/Dropbox/','/NaU/','/12736702/']):continue
  try:
   with zipfile.ZipFile(p) as z:
    names=z.namelist()
    for n in names:
     if n.endswith('DDD_GOBIERNO.md'):governance.append({'zip':str(p),'member':n,'text':z.read(n).decode()})
    pertinent=[n for n in names if n.endswith(('prepared_sources.zip','source_execution.json','manifest.json','inventario_fuentes.json','65034.csv.zip','seccionado_2025.zip'))]
    if pertinent or any(t in p.name.lower() for t in ['artifact','aragon','castilla','source','seccionado','65034']):
     h=hashlib.sha256(p.read_bytes()).hexdigest();scan.append({'path':str(p),'bytes':p.stat().st_size,'sha256':h,'members':pertinent})
     if h in hashes:hits.append({'path':str(p),'territory':hashes[h],'sha256':h,'exact':True})
     for n in pertinent:
      if n.endswith('.json') and z.getinfo(n).file_size<100000:
       try:
        obj=json.loads(z.read(n));tid=obj.get('territory_id') or (obj.get('territory') or {}).get('id')
        if tid in {r['territory_id'] for r in gaps}:hits.append({'path':str(p),'member':n,'territory':tid,'metadata':obj})
       except Exception:pass
      if n.endswith('prepared_sources.zip'):
       h=hashlib.sha256(z.read(n)).hexdigest()
       if h in hashes:hits.append({'path':str(p),'member':n,'territory':hashes[h],'sha256':h,'exact':True})
  except Exception as e:errors.append({'path':str(p),'error':str(e)})
result={'roots':[str(p) for p in roots],'exact_candidates':hits,'scanned_candidates':scan,'errors':errors,'governance':governance,'limits':'Sólo ubicaciones locales indicadas; no ausencia absoluta en disco. F01-F03 excluidos.'}
(OUT/'inventario-local.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'candidates':len(scan),'hits':hits,'errors':len(errors),'governance_paths':[{k:v for k,v in g.items() if k!='text'} for g in governance]},ensure_ascii=False,indent=2))
