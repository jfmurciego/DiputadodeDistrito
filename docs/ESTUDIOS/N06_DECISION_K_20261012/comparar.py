#!/usr/bin/env python3
"""Versión 1.0.0; N06, comparaciones institucionales de K; 2026-10-12.
Alcance: aritmética provincial 2025, sin generación. Estado: WAIT_OWNER.
Cambios/motivo: completar K fijo frente a N05. Origen: nuevo, sin predecesor.
"""
from fractions import Fraction as F
from pathlib import Path
import argparse
import csv
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from herramientas.modelo_cuantitativo_nacional import largest_remainder
from herramientas.evaluar_alternativas_nacionales import validate_model, provincial_metrics

BASE = 'docs/ESTUDIOS/modelo_nacional_2025_120000/'
INPUTS = [BASE+'fuente_poblacion.json', BASE+'modelo.json', BASE+'MANIFEST.json',
          'docs/ESTUDIOS/cartografia_nacional_20261008/atributos_historicos.json',
          'territorios/congreso/contrato_congreso_2026.json',
          'docs/ESTUDIOS/N07_20261011/result/evidence.json',
          'herramientas/modelo_cuantitativo_nacional.py',
          'herramientas/evaluar_alternativas_nacionales.py']
SPANISH = {'01':'Álava','03':'Alicante','07':'Islas Baleares','12':'Castellón','15':'La Coruña','17':'Gerona',
           '20':'Guipúzcoa','25':'Lérida','26':'La Rioja','32':'Orense',
           '35':'Las Palmas','46':'Valencia','48':'Vizcaya'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixed(populations, total, minimum):
    """Mínimo 2 provincial + ciudades fijas 1; residual Hamilton solo 50."""
    if type(total) is not int or total < (102 if minimum else 0):
        raise ValueError('K_INVALID')
    if set(populations) != {f'{i:02d}' for i in range(1,53)}:
        raise ValueError('COVERAGE_INVALID')
    if not minimum:
        return largest_remainder(populations, total)
    residual = largest_remainder({c:p for c,p in populations.items() if c not in {'51','52'}}, total-102)
    return {c:1 if c in {'51','52'} else 2+residual[c] for c in populations}


def build():
    source=json.loads((ROOT/(BASE+'fuente_poblacion.json')).read_text())
    model=json.loads((ROOT/(BASE+'modelo.json')).read_text())
    manifest=json.loads((ROOT/(BASE+'MANIFEST.json')).read_text())
    for name, expected in manifest['files'].items():
        if digest(ROOT/(BASE+name)) != expected:
            raise ValueError('PROTECTED_INPUT_HASH_MISMATCH: '+name)
    pops=validate_model(model)
    assert source['population_year']==2025 and source['reference_date']=='2025-01-01'
    assert len(source['rows'])==52 and {r['province_code']:r['population'] for r in source['rows']}==pops
    assert sum(pops.values())==source['national_population']==49128297
    contract=json.loads((ROOT/INPUTS[4]).read_text())
    assert contract['k_decision']['status']=='WAIT_OWNER' and contract['k_decision']['total'] is None
    assert contract['accreditation']['generation_authorized'] is False
    hist=json.loads((ROOT/INPUTS[3]).read_text())
    names={r['province_code']:SPANISH.get(r['province_code'],r['name']) for r in source['rows']}
    scenarios=[]
    # N05: reuse existing allocations, do not replace their population-target rules.
    for a in model['alternatives']:
        scenarios.append((f"n05_{a['rule']}",a['k_total'],a['rule'],
                          {r['province_code']:r['k_assigned'] for r in a['rows']},
                          {r['province_code']:r['allocation_quota'] for r in a['rows']},'N05_REUSED'))
    provincial_total=sum(p for c,p in pops.items() if c not in {'51','52'})
    for k in (300,350,383,391,392,400):
        alloc=fixed(pops,k,True)
        quotas={c:'1' if c in {'51','52'} else str(2+F(p*(k-102),provincial_total)) for c,p in pops.items()}
        scenarios.append((f'k{k}_minimos',k,'minimos_2_ciudades_1_residual_hamilton',alloc,quotas,'NEW_FIXED_K'))
    for k in (350,391,400):
        alloc=fixed(pops,k,False)
        scenarios.append((f'k{k}_hamilton_puro',k,'hamilton_puro_52',alloc,
                          {c:str(F(p*k,sum(pops.values()))) for c,p in pops.items()},'NEW_FIXED_K'))
    scenarios.append(('antecedente_391_reponderado_2025',391,'recuento_historico_no_acreditado',hist['province_counts'],
                      {c:None for c in pops},'HISTORICAL_COUNTS_NOT_2025_MAP'))
    rows=[]; summary=[]
    for sid,k,rule,allocation,quotas,origin in scenarios:
        assert set(allocation)==set(pops) and sum(allocation.values())==k
        metrics=provincial_metrics([{'province_code':c,'population':p,'k_assigned':allocation[c]} for c,p in pops.items()],120000)
        necessary_failures=[]
        for c,p in pops.items():
            n=allocation[c]; mean=F(p,n) if n else None
            lower_k=(p+210000-1)//210000
            upper_k=p//96000
            if not (lower_k<=n<=upper_k): necessary_failures.append(c)
            rows.append({'scenario':sid,'rule':rule,'origin':origin,'k_total':k,'province_code':c,'province_name':names[c],
                         'population_2025':p,'target_quota_120000':str(F(p,120000)),
                         'allocation_quota':quotas[c], 'k_province':n,
                         'mean_population':str(mean) if mean is not None else None,
                         'mean_population_decimal':round(float(mean),6) if mean is not None else None,
                         'deviation_from_120000':str(mean-120000) if mean is not None else None,
                         'deviation_from_national_mean':str(mean-F(sum(pops.values()),k)) if mean is not None else None,
                         'relative_deviation_from_120000':str((mean-120000)/120000) if mean is not None else None,
                         'necessary_min_k_at_cap_210000':lower_k,'necessary_max_k_at_floor_96000':upper_k,
                         'necessary_population_bounds_pass':lower_k<=n<=upper_k})
        summary.append({'scenario':sid,'rule':rule,'origin':origin,'k_total':k,
                        'national_mean':str(F(sum(pops.values()),k)),
                        'within_300_400':300<=k<=400,'equals_legal_350':k==350,
                        'minimum_2_province_1_city_violations':[c for c,n in allocation.items() if n<(1 if c in {'51','52'} else 2)],
                        'cities_not_fixed_one':[c for c in ('51','52') if allocation[c]!=1],
                        'necessary_bounds_failures':necessary_failures,
                        'allocation_l1_against_historical':sum(abs(allocation[c]-hist['province_counts'][c]) for c in pops),
                        **{key:metrics[key] for key in ('unrepresented_population','district_weighted_mae','minimum_province_mean','maximum_province_mean')}})
    evidence={'metadata':{'version':'1.0.0','name':'N06 expediente decisorio K','date':'2026-10-12',
                         'scope':'52 circunscripciones, población 2025, análisis local', 'status':'WAIT_OWNER',
                         'changes':'contraste K fijo y N05','reason':'decisión expresa del propietario','origin':'nuevo'},
              'task_id':'N06','plan_id':'ddd-maestro-20261008','population_total':sum(pops.values()),
              'population_edition':2025,'source_zip_sha256':source['source_zip_sha256'],
              'inputs_sha256':{p:digest(ROOT/p) for p in INPUTS},
              'hypothetical_bounds':{'target':120000,'floor':96000,'cap':210000,'approved':False},
              'quota_semantics':'total expected provincial allocation; minimum model is 2 + residual quota; cities = 1',
              'arithmetic':'fractions exact; code ascending tie-break is modelling convention, not attributed to law',
              'geometry_generated':False,'k_approved':False,'scenarios':summary}
    return rows,evidence


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args(); rows,evidence=build()
    args.output.mkdir(parents=True,exist_ok=False)
    with (args.output/'repartos_52.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n'); w.writeheader(); w.writerows(rows)
    (args.output/'comparaciones.json').write_text(json.dumps(evidence,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    with (args.output/'resumen.csv').open('w',newline='',encoding='utf-8') as f:
        fields=['scenario','k_total','national_mean','district_weighted_mae','unrepresented_population','necessary_bounds_failures']
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n'); w.writeheader()
        for s in evidence['scenarios']: w.writerow({k:s[k] for k in fields})
    print(f"PASS: {len(evidence['scenarios'])} escenarios, {len(rows)} filas, edición 2025; N06 WAIT_OWNER")


if __name__=='__main__': main()
