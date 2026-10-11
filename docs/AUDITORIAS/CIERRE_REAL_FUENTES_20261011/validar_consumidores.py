#!/usr/bin/env python3
"""Versión 1.0.0 — Validación material de 19 consumidores; fecha 2026-10-11.
Alcance: sólo consumo offline de fuentes territoriales acreditadas; estado: candidato.
Cambios: nuevo verificador de bytes históricos y nuevos receipts canónicos.
Motivo: verificar registro #179 sin generación ni publicación.
Origen: checkpoint 2af7d0d6acd15b05ad382f1afc12a75a59ddbf76; predecesor: ninguno.
"""
from pathlib import Path
import argparse,json,socket,sys,tempfile
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from herramientas.almacen_fuentes_local import consume,sha256
from herramientas.consumir_par_fuentes_legislatura import validate_territorial_receipt,validate_effective_territorial_package,PreparedPairExecutionBlock
from herramientas.resolver_preparacion_legislatura import resolve

def validate(store,authentic,output):
 before=sha256(store/'recovery-manifest.json'); rows=[]
 with tempfile.TemporaryDirectory(prefix='ddd-19-consumidores-',dir='/private/tmp') as tmp, patch.object(socket,'create_connection',side_effect=AssertionError('OFFLINE_NETWORK_FORBIDDEN')), patch.object(socket.socket,'connect',side_effect=AssertionError('OFFLINE_NETWORK_FORBIDDEN')):
  plans=resolve(ROOT,'Todos')['plans']
  assert len(plans)==19
  for plan in plans:
   tid=plan['territory_id']; row={'territory_id':tid,'name':plan['name'],'required_years':[plan['population_year_selected'],plan['section_year_selected']],'generation_executed':False,'publication_executed':False,'electoral_bytes_validated':False,'electoral_admissibility':plan['electoral_admissibility']}
   try:
    state,receipt=validate_territorial_receipt(root_dir=ROOT,territory=tid,edition='2025')
    if tid=='extremadura': package=authentic/'validated'/tid
    else: package=consume(store,destination=Path(tmp)/tid,**{k:receipt[k] for k in ('territory_id','edition','territorial_identity_sha256','package_sha256')})
    row['effective_validation']=validate_effective_territorial_package(root_dir=ROOT,territorial_receipt_path=Path(state['preparation_evidence']['receipt_path']),territorial_package=package)
    row.update(consumer='PASS',receipt_path=state['preparation_evidence']['receipt_path'],identity=receipt['territorial_identity_sha256'],package_sha256=receipt['package_sha256'],actual_years=[receipt['population_year'],receipt['section_year']])
    row['temporal_contract']='PASS' if row['required_years']==row['actual_years'] else 'BLOCKED_WRONG_YEAR'
   except (PreparedPairExecutionBlock,ValueError,OSError,KeyError) as exc: row.update(consumer='BLOCKED',reason=str(exc),temporal_contract='BLOCKED_UNACCREDITED_BYTES')
   rows.append(row)
 assert sha256(store/'recovery-manifest.json')==before
 result={'version':'1.0.0','date':'2026-10-11','scope':'19 actual offline consumers; temporal and electoral gates separate','origin':'2af7d0d6acd15b05ad382f1afc12a75a59ddbf76','predecessor':None,'historical_store_manifest_sha256':before,'counts':{s:sum(r['consumer']==s for r in rows) for s in ('PASS','BLOCKED')},'rows':rows}
 output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(result['counts']))
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('--store',type=Path,required=True); ap.add_argument('--authentic',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); validate(a.store,a.authentic,a.output)
