#!/usr/bin/env python3
"""Versión 1.0.0; Regresiones corrección N06; 2026-10-12.
Alcance: regla provincial y evidencia; WAIT_OWNER; origen nuevo.
Cambios/motivo: comprobar mandato DDD sin generar distritos.
"""
import hashlib
import json
import unittest
from fractions import Fraction as F
from corregir import allocate, build, HERE, ROOT

class CorrectionTests(unittest.TestCase):
    def test_allocation_against_exact_quota_and_n05(self):
        rows, summary=build()
        model=json.loads((ROOT/'docs/ESTUDIOS/modelo_nacional_2025_120000/modelo.json').read_text())
        previous=next(a for a in model['alternatives'] if a['rule']=='nearest_half_up_independiente')
        self.assertEqual({r['province_code']:r['k_province'] for r in rows},
                         {r['province_code']:r['k_assigned'] for r in previous['rows']})
        for r in rows:
            q=F(r['quota']); lower=q.numerator//q.denominator
            self.assertEqual(r['k_province'], max(1,lower+int(q-lower>=F(1,2))))
        self.assertEqual(summary['k_total'],407)

    def test_minima_ties_and_no_fixed_legal_total(self):
        pops={f'{i:02d}':1 for i in range(1,53)}
        self.assertEqual(sum(allocate(pops).values()),52)
        for p,k in [(59999,1),(60000,1),(179999,1),(180000,2),(180001,2),(300000,3)]:
            pops['01']=p; self.assertEqual(allocate(pops)['01'],k)
        self.assertNotIn('total',__import__('inspect').signature(allocate).parameters)
        self.assertIsNone(build()[1]['legal_k_constraint'])

    def test_52_unique_identities_and_reject_bad_inputs(self):
        rows,_=build(); self.assertEqual(len(rows),52)
        self.assertEqual({r['province_code'] for r in rows},{f'{i:02d}' for i in range(1,53)})
        p={r['province_code']:r['population_2025'] for r in rows}
        for bad in [True,-1,0,1.0]:
            p['01']=bad
            with self.assertRaises(ValueError): allocate(p)
        with self.assertRaises(ValueError): allocate({'01':100})

    def test_determinism_and_preserved_artifact(self):
        rows, s=build(); self.assertEqual(s,json.loads((HERE/'resultados/correccion_ddd.json').read_text()))
        p={r['province_code']:r['population_2025'] for r in rows}
        self.assertEqual(allocate(p),allocate(dict(reversed(list(p.items())))))
        legacy=ROOT/'legacy/docs/ESTUDIOS/N06_DECISION_K_20261012_v1.0.0'
        m=json.loads((legacy/'MANIFEST.json').read_text())
        for name, sha in m['files_sha256'].items():
            path=legacy/name if name=='EXPEDIENTE.md' else HERE/name
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),sha,name)

    def test_explicit_exceptions_and_exact_deviations(self):
        rows,s=build(); self.assertEqual([r['province_code'] for r in s['exceptions']],['42','51','52'])
        for r in rows:
            self.assertEqual(F(r['mean']),F(r['population_2025'],r['k_province']))
            self.assertEqual(F(r['deviation']),F(r['mean'])-120000)
            self.assertEqual(r['exception']!='NONE',r['population_2025']<100000)
            self.assertGreaterEqual(r['k_province'],1)
        self.assertEqual(s['geographical_exceptions_status'],'PREDECLARED_POLICY_PENDING_ACCREDITED_REGISTER')
        doc=(HERE/'EXPEDIENTE.md').read_text()
        for requirement in ['E1','E2','E3','WAIT_OWNER','aristas ficticias','registro','prueba de necesidad']:
            self.assertIn(requirement,doc)

if __name__=='__main__': unittest.main(verbosity=2)
