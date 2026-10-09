"""DDD blocked compatibility reports, version 1.0.0, 2026-10-10.
Scope: actual recovered five packages, existing diagnostic reconciler.
Origin: strict materialized builder rejects missing population; no predecessor.
Does not change builders, consumption gates, datasets, or existing evidence.
"""
from pathlib import Path
import sys,json,csv,io,zipfile,hashlib
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from herramientas.compatibilidad_poblacion_seccionado import reconcile_population_sectioning,normalize_geometry_frames,_geometry_frame_from_zip,validate_report_bindings,normalize_section_key,_geometry_audit_context
from ddd_core.territorial_validation import parse_population_value,TerritorialDataError
def sha(b):return hashlib.sha256(b).hexdigest()
results=[]
for meta in json.loads((OUT/'artifact-metadata.json').read_text()):
 t=meta['territory'];p=OUT/t/'compatibilidad';inventory=json.loads((p/'inventario_fuentes.json').read_text());byrole={s['role']:s for s in inventory['sources']};pop=p/'materialized'/byrole['population']['path']
 with zipfile.ZipFile(pop) as z:
  names=[n for n in z.namelist() if n.endswith('.csv')];assert len(names)==1
  records=list(csv.DictReader(io.StringIO(z.read(names[0]).decode('utf-8-sig')),delimiter=';'))
 rows=[];invalid=[]
 for r in records:
  key=normalize_section_key(r['Secciones'])
  try:value=parse_population_value(r['Total'],section_id=key,label='población del paquete')
  except TerritorialDataError as e:
   assert str(e).startswith('POPULATION_MISSING:') and not r['Total'].strip(),str(e)
   value=None;invalid.append({'section':key,'raw_value':r['Total'],'cause':str(e)})
  rows.append((key,value))
 gdf,idfield=_geometry_frame_from_zip(p/'materialized'/byrole['target_sectioning']['path'])
 target,origin,crs=normalize_geometry_frames(target_gdf=gdf,target_id_field=idfield,origin_gdf=None,origin_id_field=None,cross_year=False)
 identities={role:{'role':role,'source_id':s['source_id'],'path':s['path'],'member':'materialized/'+s['path'],'bytes':len((p/'materialized'/s['path']).read_bytes()),'sha256':sha((p/'materialized'/s['path']).read_bytes())} for role,s in byrole.items()}
 report=reconcile_population_sectioning(territory_id=t,edition='2025',population_year=inventory['population_year'],section_year=inventory['section_year'],population_rows=rows,target_geometry_rows=target,origin_geometry_rows=None,input_identities=identities,crs_audit=crs,geometry_audits=_geometry_audit_context(byrole))
 assert report['decision']=='BLOCKED' and 'POPULATION_VALUE_MISSING' in report['causes']
 reasons=validate_report_bindings(report=report,inventory=inventory,read_member_bytes=lambda n:(p/n).read_bytes(),territory_id=t,edition='2025',population_year=inventory['population_year'],section_year=inventory['section_year'],require_ready=False);assert not reasons,reasons
 ready_rejections=validate_report_bindings(report=report,inventory=inventory,read_member_bytes=lambda n:(p/n).read_bytes(),territory_id=t,edition='2025',population_year=inventory['population_year'],section_year=inventory['section_year'],require_ready=True);assert ready_rejections
 path=p/'compatibilidad_diagnostica.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 detail={'method':'Existing reconcile_population_sectioning and validate_report_bindings on real rows and geometry','strict_builder_result':'BLOCKED as recorded in original result.json; no replacement or bypass','report_role':'Diagnostic BLOCKED only; not a READY materialized report','null_handling':'Only exact empty source Total kept as None; no imputation, dropping or substitution','missing_population_rows':invalid,'binding_validation':'PASS','require_ready_rejections':ready_rejections,'report_sha256':sha(path.read_bytes())}
 (p/'diagnostic-validation.json').write_text(json.dumps(detail,ensure_ascii=False,indent=2)+'\n')
 result={'territory_id':t,'report':str(path.relative_to(ROOT)),'decision':report['decision'],'causes':report['causes'],'missing_population_rows':len(invalid),'target_sections':len(gdf),'population_rows':len(rows),'compatibility_identity_sha256':report['compatibility_identity_sha256'],'report_sha256':sha(path.read_bytes()),'ready_gate':'REJECTED'};results.append(result);print(json.dumps(result,ensure_ascii=False))
(OUT/'diagnostic-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
