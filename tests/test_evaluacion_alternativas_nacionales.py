"""VERSIÓN: 1.0.0; NOMBRE: métricas nacionales; FECHA: 2026-10-08.
ALCANCE: reparto conservado y escenarios sintéticos; ESTADO: CI_PENDIENTE.
CAMBIOS: métricas, conservación y límites; MOTIVO: comparar sin aprobar K.
ORIGEN: nuevo, sin predecesor.
"""
import copy
from fractions import Fraction
import json
from pathlib import Path
import unittest
from herramientas.evaluar_alternativas_nacionales import evaluate, provincial_metrics, sensitivity, validate_model,population_diagnostic

ROOT=Path(__file__).resolve().parents[1]


class AlternativeMetrics(unittest.TestCase):
    def test_exact_weighted_deviation_and_extremes(self):
        result=provincial_metrics([{'province_code':'01','population':120,'k_assigned':1},{'province_code':'02','population':180,'k_assigned':2}],100)
        self.assertEqual(Fraction(result['district_weighted_mae']),Fraction(40,3))
        self.assertEqual(result['minimum_province_mean']['population'],'90')
        self.assertEqual(result['maximum_province_mean']['population'],'120')
        self.assertIsNone(result['observed_district_extremes'])
        self.assertFalse(result['geometric_provincial_barriers_verified'])

    def test_zero_seats_retains_unrepresented_population(self):
        result=provincial_metrics([{'province_code':'01','population':50,'k_assigned':0}],100)
        self.assertEqual(result['unrepresented_population'],50)
        self.assertIsNone(result['district_weighted_mae'])
        self.assertIsNone(result['minimum_province_mean'])

    def test_invalid_values_reject(self):
        for population,seats in [(-1,1),(1,-1),(True,1),(1,False)]:
            with self.assertRaises(ValueError):provincial_metrics([{'province_code':'01','population':population,'k_assigned':seats}],100)

    def model(self):
        return json.loads((ROOT/'docs/ESTUDIOS/modelo_nacional_2025_120000/modelo.json').read_text())

    def test_original_model_is_read_not_rewritten(self):
        model=self.model();before=copy.deepcopy(model)
        populations=validate_model(model)
        self.assertEqual(sum(populations.values()),49128297)
        results=evaluate(model)
        self.assertEqual(model,before)
        self.assertEqual([a['k_total'] for a in results['alternatives']],[383,407,435,409,409])
        self.assertEqual(results['approved_k_alternatives'],[])

    def test_population_universe_version_and_totals_fail_closed(self):
        for mutate in [lambda m:m.update(version='2.0.0'),lambda m:m['alternatives'][0]['rows'][0].update(population=1),lambda m:m['alternatives'][0].update(k_total=1),lambda m:m['alternatives'][0]['rows'].pop()]:
            model=self.model();mutate(model)
            with self.assertRaises(ValueError):validate_model(model)

    def test_sensitivity_count_determinism_and_integer_allocation(self):
        model=self.model();first=sensitivity(model);second=sensitivity(model)
        self.assertEqual(first,second)
        self.assertEqual(len(first),4*53*5)
        self.assertEqual(len([r for r in first if r['scope']=='uniform']),20)
        self.assertTrue(all(type(r['k_total'])is int and type(r['allocation_l1'])is int for r in first))
        baseline={a['rule']:a['k_total'] for a in model['alternatives']}
        self.assertTrue(all(r['k_delta']==r['k_total']-baseline[r['rule']] for r in first))

    def test_historical_distribution_is_not_cartographic_identity(self):
        counts={f'{i:02d}':1 for i in range(1,53)}
        result=evaluate(self.model(),counts)
        self.assertIn('not_administrative',result['alternatives'][0]['against_undated_historical_allocation']['interpretation'])
        self.assertEqual(result['alternatives'][0]['against_undated_historical_allocation']['k_delta'],383-52)

    def test_population_difference_does_not_assert_demographic_growth(self):
        reference=json.loads((ROOT/'docs/ESTUDIOS/modelo_nacional_2025_120000/fuente_poblacion.json').read_text())
        historical={'historical_population_edition':None,'province_population_reported_decimal':{r['province_code']:str(r['population']) for r in reference['rows']}}
        result=population_diagnostic(historical,reference)
        self.assertIsNone(result['historical_population_edition'])
        self.assertEqual(result['numeric_difference_not_temporal_growth'],'0')
        reference['population_year']=2022
        with self.assertRaises(ValueError):population_diagnostic(historical,reference)


if __name__=='__main__':
    unittest.main()
