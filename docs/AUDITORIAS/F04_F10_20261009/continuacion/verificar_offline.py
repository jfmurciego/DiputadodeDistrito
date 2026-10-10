"""DDD F05/F07 directed offline checks, version 1.0.1, 2026-10-10.
Only five new inputs; reuse unchanged previous fourteen results explicitly.
No acquisitions, generation, canonical promotion or modification of inputs.
Patch: tracked evidence path; criteria/results unchanged; predecessor legacy/docs/AUDITORIAS/F04_F10_20261009/continuacion/verificar_offline.py; state candidate.
"""
from pathlib import Path
import sys,json,socket,tempfile,shutil
from unittest.mock import patch
OUT=Path(__file__).resolve().parent
DELIVERY=OUT.parent
ROOT=DELIVERY.parents[2]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from herramientas.seleccionar_paquete_fuentes import select_first_valid,validate_prepared_package
from herramientas.consumir_par_fuentes_legislatura import validate_territorial_receipt,PreparedPairExecutionBlock

results=[]
with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
     patch.object(socket,'create_connection',side_effect=AssertionError('network forbidden')), \
     patch.object(socket,'getaddrinfo',side_effect=AssertionError('network forbidden')):
    for row in json.loads((DELIVERY/'candidate-results-v3.json').read_text())['rows']:
        territory=row['territory_id'];candidate=(ROOT/row['package']).parent
        args=dict(territory_id=territory,edition='2025',population_year=2025,section_year=2025)
        chosen,diagnostics=select_first_valid([candidate],**args)
        assert chosen==candidate,diagnostics
        negatives=[]
        for label,overrides in [('wrong_territory',{'territory_id':'wrong_territory'}),
                                ('wrong_population_year',{'population_year':2024}),
                                ('wrong_section_year',{'section_year':2024})]:
            valid,reasons=validate_prepared_package(candidate,**(args|overrides))
            assert not valid and reasons
            negatives.append({'case':label,'result':'PASS','reasons':reasons})
        with tempfile.TemporaryDirectory(prefix='ddd-f07-',dir='/private/tmp') as tmp:
            damaged=Path(tmp)/'candidate';shutil.copytree(candidate,damaged)
            manifest=json.loads((damaged/'manifest.json').read_text());manifest['sha256']='0'*64
            (damaged/'manifest.json').write_text(json.dumps(manifest))
            valid,reasons=validate_prepared_package(damaged,**args)
            assert not valid and reasons
            negatives.append({'case':'contradictory_manifest_digest','result':'PASS','reasons':reasons})
        try:
            validate_territorial_receipt(root_dir=ROOT,territory=territory,edition='2025')
        except PreparedPairExecutionBlock as exc:
            canonical={'result':'BLOCKED','reason':str(exc),'accreditation':'Actual current canonical receipt validator rejection'}
        else:
            canonical={'result':'PASS','accreditation':'Actual current canonical receipt validator acceptance'}
        result={'territory_id':territory,'package_sha256':row['package_sha256'],
                'territorial_identity_sha256':row['identity']['territorial_identity_sha256'],
                'offline_candidate_selection':'PASS','diagnostics':diagnostics,
                'negative_checks':negatives,'canonical_territorial_consumer':canonical,
                'production_promotion':'NONE'}
        results.append(result);print(json.dumps(result,ensure_ascii=False))
prior=json.loads((ROOT/'docs/AUDITORIAS/F04_F10_20261009/continuacion/evidencia-previa-reutilizada.json').read_text())
for row in prior['rows']:
    assert row['controls']['F03_consumer_receipt']=='PASS'
    assert row['controls']['F03_effective_consumer']=='PASS'
    results.append({'territory_id':row['territory_id'],'package_sha256':row['package_sha256'],
                    'territorial_identity_sha256':row['territorial_identity_sha256'],
                    'canonical_territorial_consumer':{'result':'PASS_REUSED','evidence':
                       'docs/AUDITORIAS/F04_F10_20261009/continuacion/evidencia-previa-reutilizada.json',
                       'controls':['F03_consumer_receipt','F03_effective_consumer'],
                       'condition':'Same unchanged canonical files and contract at base HEAD; no rerun'},
                    'production_promotion':'UNCHANGED'})
assert len(results)==19 and len({r['territory_id'] for r in results})==19
value={'schema':'ddd.f07-offline-results/1.0','version':'1.0.1','network':'FORBIDDEN',
       'new_inputs':5,'previous_exact_results_reused':14,'new_negative_checks':20,
       'rows':results,'scope':'Canonical BLOCKED is accredited, not converted into candidate PASS'}
(OUT/'offline-results.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
