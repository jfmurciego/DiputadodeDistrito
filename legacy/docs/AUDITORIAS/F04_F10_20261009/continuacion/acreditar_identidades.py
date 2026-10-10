"""DDD F06 metadata alignment, version 1.0.0, 2026-10-10.
Reuse existing byte/consumer evidence; no package hashes or closed tests rerun.
"""
from pathlib import Path
import sys,json,hashlib,yaml
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
prior_path=ROOT/'docs/AUDITORIAS/verificacion_F02_F03_2026-10-09.json'
prior=json.loads(prior_path.read_text());rows=[]
for territory in ['cataluna','region_de_murcia']:
    previous=next(row for row in prior['rows'] if row['territory_id']==territory)
    declaration_path=ROOT/'territorios'/territory/'config/fuentes_oficiales.yaml'
    declaration=yaml.safe_load(declaration_path.read_text())
    identity=declaration['territory']
    receipt_path=ROOT/previous['receipt_path'];receipt=json.loads(receipt_path.read_text())
    for field in ['population_year','section_year']:
        assert int(identity[field])==int(receipt[field])==int(previous[field])
    assert str(identity['edition'])==str(receipt['edition'])==str(previous['edition'])
    assert identity['id']==receipt['territory_id']==territory
    for field in ['package_sha256','territorial_identity_sha256','run_id','source_commit']:
        assert str(receipt[field])==str(previous[field])
    assert previous['controls']['F03_consumer_receipt']=='PASS'
    assert previous['controls']['F03_effective_consumer']=='PASS'
    rows.append({'territory_id':territory,'result':'PASS_METADATA_ALIGNED_EXISTING_IDENTITY',
      'catalog_edition':str(identity['edition']),'population_year':identity['population_year'],
      'section_year':identity['section_year'],'identity':receipt['territorial_identity_sha256'],
      'receipt':str(receipt_path.relative_to(ROOT)),'declaration':str(declaration_path.relative_to(ROOT)),
      'declaration_sha256':hashlib.sha256(declaration_path.read_bytes()).hexdigest(),
      'receipt_sha256':hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
      'reuse_evidence':str(prior_path.relative_to(ROOT)),
      'generation_gate':'UNCHANGED; no admissibility re-evaluation or production promotion',
      'minimal_correction':'None required: current declaration and receipt already aligned'})
value={'schema':'ddd.f06-identity-alignment/1.0','version':'1.0.0','rows':rows,
 'dependency':{'current':['F04'],'material_link':'No source bytes or identities depend on the five F04 inputs',
  'proposal_for_Work':{'depends_on':['F02'],'reason':'Identity recovery evidence exists independently in F02'},
  'applied':False,'execution_order':'F04 material acceptance obtained before this check; formal dependency preserved'}}
(OUT/'identity-alignment.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(value,ensure_ascii=False))
