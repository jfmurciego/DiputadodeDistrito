"""DDD F04 material recovery, version 1.0.0, 2026-10-10.
New evidence from actual historical bytes; no source acquisition or promotion.
Origin: local work order F04 A/B; no predecessor. Originals preserved.
"""
from pathlib import Path, PurePosixPath
import sys, json, hashlib, zipfile, csv, io, re, copy, datetime, traceback
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
import geopandas as gpd
import yaml
from herramientas.compatibilidad_poblacion_seccionado import build_materialized_report, validate_report_bindings
from herramientas.identidad_fuentes_legislatura import territorial_identity
from herramientas.almacen_fuentes_local import inspect_zip
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
rows=json.loads((OUT.parent/'fuentes_oficiales_19_territorios_2026-10-08.json').read_text())['territories']
metadata=json.loads((OUT/'artifact-metadata.json').read_text())
summaries=[]
for meta in metadata:
 t=meta['territory'];row=next(r for r in rows if r['territory_id']==t);expected=row['territorial_candidate'];p=OUT/'originales'/f"artifact-{meta['id']}.zip"
 assert sha(p.read_bytes())==expected['artifact_sha256']==meta['digest'][7:]
 assert p.stat().st_size==meta['size_in_bytes'] and meta['workflow_run']['id']==expected['run_id']
 original=OUT/t/'original';derived=OUT/t/'compatibilidad';assert not original.exists() and not derived.exists()
 original.mkdir(parents=True);derived.mkdir()
 with zipfile.ZipFile(p) as z:
  inspect_zip(z);assert set(z.namelist())=={'manifest.json','prepared_sources.zip'}
  manifest=json.loads(z.read('manifest.json'));bundle=z.read('prepared_sources.zip')
  assert sha(bundle)==expected['package_sha256']==manifest['sha256']
  assert manifest['territory_id']==t and str(manifest['edition'])=='2025'
  z.extractall(original)
 with zipfile.ZipFile(original/'prepared_sources.zip') as z:
  inspect_zip(z);z.extractall(original/'bundle')
 inv=json.loads((original/'bundle/inventario_fuentes.json').read_text());prov=json.loads((original/'bundle/manifiesto_procedencia.json').read_text())
 inventory=copy.deepcopy(inv);transform=[]
 years={};facts=[];provinces=set()
 for s in inventory['sources']:
  source=(original/'bundle/materialized'/s['path']);b=source.read_bytes();assert sha(b)==s['sha256'] and len(b)==s['bytes']
  pr=next(x for x in prov['sources'] if x['source_id']==s['source_id']);assert pr['sha256']==s['sha256'] and pr['urls']==s['urls'] and pr['edition']==s['edition']
  assert pr['provider']=='Instituto Nacional de Estadística' and pr['acquired_at_utc']
  assert all(u.startswith('https://www.ine.es/') for u in s['urls'])
  if s['source_id']=='poblacion_por_sexo_y_edad':
   with zipfile.ZipFile(io.BytesIO(b)) as z:
    names=[n for n in z.namelist() if n.endswith('.csv')];assert len(names)==1
    records=list(csv.DictReader(io.StringIO(z.read(names[0]).decode('utf-8-sig')),delimiter=';'))
   periods={int(r['Periodo']) for r in records};assert len(periods)==1;year=next(iter(periods));years['population_year']=year
   assert year==s['edition'];assert all(r['Sexo']=='Total' and r['Edad']=='Todas las edades' for r in records)
   pop_provinces={re.sub(r'\D','',r['Secciones'])[:2] for r in records};s['role']='population'
   facts.append({'role':s['role'],'year':year,'basis':'Distinct actual CSV Periodo; exact historical inventory/provenance edition agrees','rows':len(records),'provinces':sorted(pop_provinces),'source_sha256':sha(b)})
  else:
   assert s['source_id']=='secciones_censales';matches=[re.search(r'Secciones_(\d{4})',u) for u in s['urls']];assert all(matches)
   values={int(m.group(1)) for m in matches};assert len(values)==1;year=next(iter(values));assert year==s['edition'];years['section_year']=year;s['role']='target_sectioning'
   frame=gpd.read_file('zip://'+str(source));provinces={str(v).zfill(2) for v in frame['CPRO']};assert sorted(provinces)==sorted(inv['territorial_coverage'])
   facts.append({'role':s['role'],'year':year,'basis':'Historical annual INE collection URLs plus signed archive inventory/provenance; not catalog edition or acquisition date','rows':len(frame),'provinces':sorted(provinces),'crs':str(frame.crs),'invalid_geometry_count':int((~frame.geometry.is_valid).sum()),'source_sha256':sha(b)})
  target=derived/'materialized'/s['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
  transform.append({'operation':'Exact byte copy and role annotation for current validator','source_member':'materialized/'+s['path'],'source_sha256':sha(b),'output_sha256':sha(target.read_bytes()),'role':s['role']})
 assert pop_provinces==provinces
 declaration=yaml.safe_load((ROOT/row['declaration']).read_text());required={str(c['code']).zfill(2) for c in declaration['territory']['territorial_codes']};assert provinces==required
 inventory.update(years);write(derived/'inventario_fuentes.json',inventory)
 write(OUT/t/'temporal-provenance.json',{'catalog_edition':'2025','dataset_years':years,'actual_facts':facts,'source_acquisition_dates':[s['acquired_at_utc'] for s in prov['sources']],'limitations':['Archive manifest acquired_at=unknown-acquisition-date preserved; use per-source provenance acquisition dates','No population/section years inferred from catalog edition'],'transformations':transform})
 identity=territorial_identity(territory_id=t,edition='2025',package_sha256=expected['package_sha256'],**years)
 if row['territorial_receipt']:
  receipt=json.loads((ROOT/row['territorial_receipt']).read_text());assert all(receipt[k]==identity[k] for k in identity);assert receipt['artifact_id']==meta['id'];assert receipt['source_commit']==meta['workflow_run']['head_sha']
 result={'territory_id':t,'catalog_edition':'2025',**years,'artifact_id':meta['id'],'run_id':meta['workflow_run']['id'],'original_package_sha256':expected['package_sha256'],'original_artifact_sha256':expected['artifact_sha256'],'identity':identity,'material_recovery':'PASS','compatibility':'NOT_RUN','eligible':False}
 try:
  report=build_materialized_report(evidence_dir=derived,territory_id=t,edition='2025',inventory=inventory,**years)
  reasons=validate_report_bindings(report=report,inventory=inventory,read_member_bytes=lambda n:(derived/n).read_bytes(),territory_id=t,edition='2025',require_ready=False,**years);assert not reasons,reasons
  result.update(compatibility=report['decision'],causes=report['causes'],report=str((derived/'compatibilidad_poblacion_seccionado.json').relative_to(ROOT)),report_sha256=sha((derived/'compatibilidad_poblacion_seccionado.json').read_bytes()),compatibility_identity_sha256=report['compatibility_identity_sha256'],baseline=report['baseline'],binding_validation='PASS',eligible=report['decision']=='READY')
 except Exception as e:
  traceback.print_exc();result.update(compatibility='BLOCKED',causes=[type(e).__name__+': '+str(e)],binding_validation='NOT_REACHED')
 write(OUT/t/'transformations.json',transform)
 receipt={'schema':'ddd.local-source-recovery-receipt/1.0','version':'1.0.0','kind':'historical_artifact_recovery','recovered_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_operation':'GitHub connector download_workflow_artifact; curl exact bytes; hashes/size/CRC checked','origin':meta['url'],'source_commit':meta['workflow_run']['head_sha'],'artifact_name':meta['name'],'artifact_id':meta['id'],'run_id':meta['workflow_run']['id'],'artifact_sha256':expected['artifact_sha256'],'package_sha256':expected['package_sha256'],'original_manifest':str((original/'manifest.json').relative_to(ROOT)),**identity,'compatibility':result['compatibility'],'eligibility':'LOCAL_READY' if result['eligible'] else 'BLOCKED','promotion':'NONE','historical_receipt':row['territorial_receipt'],'note':'New recovery operation receipt; never claims historical acquisition or upgrades canonical historical receipt'}
 write(OUT/t/'recovery-receipt.json',receipt);write(OUT/t/'result.json',result);summaries.append(result)
 print(json.dumps(result,ensure_ascii=False))
write(OUT/'resultados-cinco.json',{'schema':'ddd.f04-material-results/1.0','version':'1.0.0','rows':summaries,'originals_preserved':True,'production_changes':False})
