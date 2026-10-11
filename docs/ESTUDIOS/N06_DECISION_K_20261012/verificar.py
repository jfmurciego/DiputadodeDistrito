#!/usr/bin/env python3
"""Versión 1.0.0; verificación independiente aritmética N06; 2026-10-12.
Alcance: tablas/evidencia 2025. Estado: WAIT_OWNER. Origen: nuevo.
Cambios/motivo: oráculo entero separado, conservation y límites necesarios.
"""
import csv
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('n06_comparar',HERE/'comparar.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


def oracle(populations,total,minimum):
    subset={c:p for c,p in populations.items() if not minimum or c not in {'51','52'}}
    denom=sum(subset.values()); residual=total-102 if minimum else total
    division={c:divmod(p*residual,denom) for c,p in subset.items()}
    assigned={c:parts[0] for c,parts in division.items()}
    remaining=residual-sum(assigned.values())
    # Selection by maximum integer remainder, without shared Hamilton code.
    unselected=set(subset)
    for _ in range(remaining):
        winner=max(unselected,key=lambda c:(division[c][1],-int(c)))
        assigned[winner]+=1; unselected.remove(winner)
    if minimum:
        return {c:1 if c in {'51','52'} else 2+assigned[c] for c in populations}
    return assigned


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=json.loads((ROOT/(module.BASE+'fuente_poblacion.json')).read_text())
        cls.pops={r['province_code']:r['population'] for r in cls.source['rows']}
        with (HERE/'resultados/repartos_52.csv').open(encoding='utf-8',newline='') as stream:
            cls.rows=list(csv.DictReader(stream))
        cls.evidence=json.loads((HERE/'resultados/comparaciones.json').read_text())
        cls.groups={s['scenario']:[r for r in cls.rows if r['scenario']==s['scenario']] for s in cls.evidence['scenarios']}

    def test_fixed_allocations_with_independent_integer_oracle(self):
        for sid,rows in self.groups.items():
            if sid.startswith('k'):
                k=int(rows[0]['k_total']); minimum=sid.endswith('_minimos')
                self.assertEqual({r['province_code']:int(r['k_province']) for r in rows},oracle(self.pops,k,minimum),sid)

    def test_coverage_totals_and_population(self):
        self.assertEqual(len(self.rows),15*52)
        for sid,rows in self.groups.items():
            self.assertEqual(len(rows),52,sid)
            self.assertEqual({r['province_code'] for r in rows},set(self.pops),sid)
            self.assertEqual(sum(int(r['k_province']) for r in rows),int(rows[0]['k_total']),sid)
            self.assertEqual({r['province_code']:int(r['population_2025']) for r in rows},self.pops,sid)

    def test_exact_means_deviations_and_necessary_bounds(self):
        for r in self.rows:
            p=int(r['population_2025']); n=int(r['k_province']); k=int(r['k_total'])
            self.assertEqual(F(r['target_quota_120000']),F(p,120000))
            self.assertEqual(int(r['necessary_min_k_at_cap_210000']),(p+209999)//210000)
            self.assertEqual(int(r['necessary_max_k_at_floor_96000']),p//96000)
            if n:
                self.assertEqual(F(r['mean_population']),F(p,n))
                self.assertEqual(F(r['deviation_from_120000']),F(p,n)-120000)
                self.assertEqual(F(r['deviation_from_national_mean']),F(p,n)-F(sum(self.pops.values()),k))
            else:
                self.assertEqual(r['mean_population'],'')

    def test_minima_and_city_fixed_one(self):
        for sid,rows in self.groups.items():
            if sid.endswith('_minimos') or sid=='n05_minimos_referencia_k_derivado':
                self.assertTrue(all(int(r['k_province']) >= (1 if r['province_code'] in {'51','52'} else 2) for r in rows))
                self.assertEqual([int(r['k_province']) for r in rows if r['province_code'] in {'51','52'}],[1,1])

    def test_historical_not_relabelled_as_2025_map(self):
        h=json.loads((ROOT/module.INPUTS[3]).read_text())
        rows=self.groups['antecedente_391_reponderado_2025']
        self.assertEqual({r['province_code']:int(r['k_province']) for r in rows},h['province_counts'])
        self.assertTrue(all(r['allocation_quota']=='' and r['origin']=='HISTORICAL_COUNTS_NOT_2025_MAP' for r in rows))

    def test_three_small_circumscriptions_make_floor_impossible(self):
        for c in ['42','51','52']:
            self.assertLess(self.pops[c],96000)
            self.assertEqual(self.pops[c]//96000,0)

    def test_input_hashes_and_contract_remains_wait_owner(self):
        for p,sha in self.evidence['inputs_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),sha)
        c=json.loads((ROOT/module.INPUTS[4]).read_text())
        self.assertEqual(c['k_decision']['status'],'WAIT_OWNER'); self.assertIsNone(c['k_decision']['total'])
        self.assertFalse(c['accreditation']['generation_authorized'])

    def test_deterministic_outputs(self):
        rows,evidence=module.build()
        self.assertEqual(evidence,self.evidence)
        for actual,expected in zip(self.rows,rows):
            self.assertEqual(actual,{k:'' if v is None else str(v) for k,v in expected.items()})

    def test_hamilton_non_monotonic_soria_is_explicit(self):
        def soria(sid):return next(int(r['k_province']) for r in self.groups[sid] if r['province_code']=='42')
        self.assertEqual((soria('k391_minimos'),soria('k392_minimos'),soria('k400_minimos')),(2,3,2))

    def test_reject_invalid_k_and_missing_coverage(self):
        for bad in [101,-1,True,350.0]:
            with self.assertRaises(ValueError):module.fixed(self.pops,bad,True)
        with self.assertRaises(ValueError):module.fixed({'01':100},350,True)

    def test_350_residual_ties_not_at_assignment_cutoff(self):
        subset={c:p for c,p in self.pops.items() if c not in {'51','52'}}
        total=sum(subset.values()); parts=[divmod(p*248,total) for p in subset.values()]
        extra=248-sum(q for q,r in parts)
        ranked=sorted((r for q,r in parts),reverse=True)
        self.assertGreater(ranked[extra-1],ranked[extra])


if __name__=='__main__':unittest.main(verbosity=2)
