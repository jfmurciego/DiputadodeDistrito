"""DDD exact-universe local candidates, version 1.0.0, 2026-10-10.
Scope: select actual same-year section keys; no imputation or redistribution.
Originals and failed reports stay immutable. Candidate only, no promotion.
Origin: explicit work order permits traceable transformations; no predecessor.
"""
from pathlib import Path
import sys,json,csv,io,zipfile,hashlib,copy,datetime
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from herramientas.compatibilidad_poblacion_seccionado import build_materialized_report,_geometry_frame_from_zip,normalize_section_key
from herramientas.seleccionar_paquete_fuentes import validate_prepared_package
from herramientas.identidad_fuentes_legislatura import territorial_identity
from ddd_core.territorial_validation import parse_population_value
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def archive_one(name,b):
 stream=io.BytesIO()
 with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
  info=zipfile.ZipInfo(name,(2026,10,10,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b)
 return stream.getvalue()
results=[]
for meta in json.loads((OUT/'artifact-metadata.json').read_text()):
 t=meta['territory'];orig=OUT/t/'original/bundle';p=OUT/t/'candidato-v2';assert not p.exists();p.mkdir()
 inv=json.loads((OUT/t/'compatibilidad/inventario_fuentes.json').read_text());prov=json.loads((orig/'manifiesto_procedencia.json').read_text());decision=json.loads((orig/'decision_adquisicion.json').read_text());resolved=json.loads((orig/'declaracion_materializacion.json').read_text())
 years={'population_year':inv['population_year'],'section_year':inv['section_year']};assert years['population_year']==years['section_year']==2025
 byrole={s['role']:s for s in inv['sources']};section=orig/'materialized'/byrole['target_sectioning']['path'];gdf,keyfield=_geometry_frame_from_zip(section);keys={normalize_section_key(v) for v in gdf[keyfield]};assert len(keys)==len(gdf)
 pop=orig/'materialized'/byrole['population']['path'];original_pop=pop.read_bytes()
 with zipfile.ZipFile(io.BytesIO(original_pop)) as z:
  names=[n for n in z.namelist() if n.endswith('.csv')];assert len(names)==1
  reader=csv.DictReader(io.StringIO(z.read(names[0]).decode('utf-8-sig')),delimiter=';');fields=reader.fieldnames;records=list(reader)
 kept=[];excluded=[];seen=set();known_total=0
 for index,r in enumerate(records,2):
  key=normalize_section_key(r['Secciones']);assert key not in seen;seen.add(key)
  if key in keys:
   known_total+=parse_population_value(r['Total'],section_id=key);kept.append(r)
  else:
   assert not r['Total'].strip(),'nonempty population outside target universe; forbidden to remove'
   excluded.append({'csv_line':index,'section':key,'raw_row':r,'reason':'Key absent from exact frozen same-year target sectioning; Total empty; no numeric population discarded'})
 assert {normalize_section_key(r['Secciones']) for r in kept}==keys
 assert len(kept)+len(excluded)==len(records)
 output=io.StringIO();writer=csv.DictWriter(output,fieldnames=fields,delimiter=';',lineterminator='\n');writer.writeheader();writer.writerows(kept)
 payload=archive_one(names[0],output.getvalue().encode('utf-8-sig'))
 for s in inv['sources']:
  target=p/'materialized'/s['path'];target.parent.mkdir(parents=True,exist_ok=True)
  b=payload if s['role']=='population' else (orig/'materialized'/s['path']).read_bytes();target.write_bytes(b)
  if s['role']=='population':
   s['derivation']={'operation':'select_exact_same_year_section_universe','original_path':str(pop.relative_to(ROOT)),'original_sha256':sha(original_pop),'universe_source_sha256':sha(section.read_bytes()),'excluded_records':len(excluded),'population_imputation':False,'numeric_population_removed':0};s['sha256']=sha(b);s['bytes']=len(b);s['content_checks']['rows']=len(kept)
   pr=next(x for x in prov['sources'] if x['source_id']==s['source_id']);pr['original_sha256']=pr['sha256'];pr['sha256']=sha(b);pr['bytes']=len(b);pr['local_derivation']=s['derivation']
 for d in [inv,prov,decision,resolved]:d.update(years);d['local_status']='CANDIDATE_UNPROMOTED';d['local_derivation']='Exact same-year target section universe; only empty records absent from universe excluded; original preserved'
 write(p/'inventario_fuentes.json',inv);write(p/'manifiesto_procedencia.json',prov);write(p/'decision_adquisicion.json',decision);write(p/'declaracion_materializacion.json',resolved)
 report=build_materialized_report(evidence_dir=p,territory_id=t,edition='2025',inventory=inv,**years);assert report['decision']=='READY' and not report['causes'] and report['population']['exact_conservation']
 assert report['population']['input_total']==report['population']['assigned_total']==known_total
 audit={'schema':'ddd.exact-universe-derivation/1.0','version':'1.0.0','territory_id':t,'catalog_edition':'2025',**years,'original_population_zip_sha256':sha(original_pop),'derived_population_zip_sha256':sha(payload),'unchanged_sectioning_sha256':sha(section.read_bytes()),'input_records':len(records),'output_records':len(kept),'excluded_records':excluded,'numeric_population_removed':0,'population_total':known_total,'target_universe_cardinality':len(keys),'excluded_keys_intersection_target':[],'scope':'Local candidate only; not a new official acquisition or historical receipt; no production promotion'}
 write(p/'derivation.json',audit)
 package=p/'prepared_sources.zip'
 with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
  for f in sorted(p.rglob('*')):
   if f.is_file() and f!=package:
    info=zipfile.ZipInfo(str(f.relative_to(p)),(2026,10,10,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,f.read_bytes())
 h=sha(package.read_bytes());manifest={'source_id':'local-derived-territorial:'+t,'territory_id':t,'edition':2025,**years,'path':'prepared_sources.zip','bytes':package.stat().st_size,'sha256':h,'records':2,'acquired_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'acquired_at_kind':'local_derivation_operation_not_official_acquisition','original_acquisition_dates':[s['acquired_at_utc'] for s in prov['sources']],'origin':'Recovered historical INE package '+meta['url']+'; exact local derivation.json','bundle_schema':'ddd-prepared-sources-bundle/1.1','status':'CANDIDATE_UNPROMOTED','predecessor_artifact_sha256':meta['digest'][7:]};write(p/'manifest.json',manifest)
 valid,reasons=validate_prepared_package(p,territory_id=t,edition='2025',**years);assert valid,reasons
 identity=territorial_identity(territory_id=t,edition='2025',package_sha256=h,compatibility_identity_sha256=report['compatibility_identity_sha256'],**years)
 receipt={'schema':'ddd.local-derived-source-receipt/1.0','version':'1.0.0','kind':'local_derivation','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**identity,'original_artifact_id':meta['id'],'original_run_id':meta['workflow_run']['id'],'original_artifact_sha256':meta['digest'][7:],'original_source_commit':meta['workflow_run']['head_sha'],'operation':'exact_same_year_universe_selection','derivation_path':str((p/'derivation.json').relative_to(ROOT)),'compatibility_report_sha256':sha((p/'compatibilidad_poblacion_seccionado.json').read_bytes()),'local_validation':'READY','production_promotion':'NONE','note':'New local package identity; original GitHub artifact identity is never attributed to derived bytes'};write(OUT/t/'derived-receipt.json',receipt)
 r={'territory_id':t,**years,'original_recovery':'PASS','original_compatibility':'BLOCKED','local_candidate_validation':'PASS','decision':'READY','production_eligibility':'NOT_PROMOTED','package':str(package.relative_to(ROOT)),'package_sha256':h,'receipt':str((OUT/t/'derived-receipt.json').relative_to(ROOT)),'excluded_empty_nontarget_records':len(excluded),'baseline':report['baseline'],'identity':identity};results.append(r);print(json.dumps(r,ensure_ascii=False))
write(OUT/'candidate-results.json',{'schema':'ddd.f04-local-candidates/1.0','version':'1.0.0','rows':results,'production_promotion':False})
