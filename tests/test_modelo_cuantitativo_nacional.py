"""VERSIÓN: 1.0.0; NOMBRE: regresiones del modelo nacional; FECHA: 2026-10-08.
ALCANCE: aritmética y fuentes sintéticas; ESTADO: candidato.
CAMBIOS: conservación, redondeos, determinismo, límites y correspondencias.
MOTIVO: comprobar hipótesis de cálculo sin ejecutar generación.
ORIGEN: archivo nuevo, sin predecesor.
"""
import csv
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from fractions import Fraction
from pathlib import Path

from herramientas.modelo_cuantitativo_nacional import (
    calculate, compare_assignments, extract_ine, largest_remainder,
)


class NationalCalculation(unittest.TestCase):
    def test_k_derives_from_population_not_350(self):
        result = calculate({"01": 180000, "02": 120000})
        self.assertEqual(result["global_derived_k"], 3)  # 2.5, empate hacia arriba
        self.assertEqual([a["k_total"] for a in result["alternatives"]], [2, 3, 3, 3])
        self.assertEqual(result["alternatives"][0]["rows"][0]["target_quota"], "3/2")

    def test_every_alternative_preserves_population_and_reports_k_sum(self):
        for pop in ({"01": 90000, "02": 170001}, {"01": 0, "02": 0}):
            for alternative in calculate(pop)["alternatives"]:
                self.assertEqual(sum(r["population"] for r in alternative["rows"]), sum(pop.values()))
                self.assertEqual(sum(r["k_assigned"] for r in alternative["rows"]), alternative["k_total"])

    def test_deterministic_under_permutation_and_ties(self):
        self.assertEqual(largest_remainder({"02": 1, "01": 1}, 1), {"01": 1, "02": 0})
        self.assertEqual(calculate({"02": 100000, "01": 100000}), calculate({"01": 100000, "02": 100000}))

    def test_hamilton_conservation_and_quota_bounds(self):
        for seats in range(15):
            populations = {"01": 1, "02": 4, "03": 7, "04": 0}
            allocation = largest_remainder(populations, seats)
            self.assertEqual(sum(allocation.values()), seats)
            self.assertEqual(allocation["04"], 0)
            for code, assigned in allocation.items():
                quota = Fraction(populations[code] * seats, 12)
                self.assertIn(assigned, {quota.numerator // quota.denominator, -(-quota.numerator // quota.denominator)})

    def test_thresholds_and_no_float_precision_loss(self):
        cases = [(59999, 0), (60000, 1), (60001, 1), (119999, 1), (120000, 1), (120001, 1)]
        for population, expected in cases:
            self.assertEqual(calculate({"01": population})["global_derived_k"], expected)
        huge = 120000 * 10**20 + 59999
        self.assertEqual(calculate({"01": huge})["global_derived_k"], 10**20)

    def test_zero_seats_do_not_divide_by_zero(self):
        result = calculate({"01": 1})
        self.assertEqual(result["alternatives"][0]["rows"][0]["mean_population"], None)
        self.assertEqual(result["alternatives"][0]["zero_district_populated_provinces"], ["01"])

    def test_negative_boolean_fractional_and_empty_rejected(self):
        for populations in ({}, {"01": -1}, {"01": True}, {"01": 1.5}, {1: 1}):
            with self.assertRaises(ValueError):
                calculate(populations)
        for target in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                calculate({"01": 1}, target)
        with self.assertRaises(ValueError):
            largest_remainder({"01": 0}, 1)

    def test_minimum_counterfactual_conserves_derived_total_and_cities(self):
        populations = {f"{i:02d}": 1200000 for i in range(1, 53)}
        result = calculate(populations)
        model = result["alternatives"][-1]
        self.assertEqual(model["rule"], "minimos_referencia_k_derivado")
        self.assertEqual(model["k_total"], result["global_derived_k"])
        self.assertEqual(model["minimum_reference_violations"], [])
        self.assertEqual([r["k_assigned"] for r in model["rows"][-2:]], [1, 1])

    def test_infeasible_minima_do_not_inflate_k(self):
        populations = {f"{i:02d}": 1 for i in range(1, 53)}
        result = calculate(populations)
        self.assertEqual(result["global_derived_k"], 0)
        self.assertEqual(len(result["alternatives"]), 4)
        self.assertEqual(result["minimum_reference_model_status"], "NOT_APPLICABLE_OR_INFEASIBLE")

    def test_zero_provincial_population_with_fixed_cities(self):
        populations = {f"{i:02d}": 0 for i in range(1, 53)}
        populations['51'] = 102 * 120000
        result = calculate(populations)
        self.assertEqual(result['alternatives'][-1]['k_total'], 102)
        self.assertEqual(result['alternatives'][-1]['rows'][0]['allocation_quota'], '2')
        populations['51'] += 120000
        self.assertEqual(calculate(populations)['minimum_reference_model_status'], 'NOT_APPLICABLE_OR_INFEASIBLE')


class INESource(unittest.TestCase):
    def fixture(self, change=None):
        columns = ['Total Nacional', 'Provincias', 'Municipios', 'Secciones', 'Sexo', 'Edad', 'Periodo', 'Total']
        rows = [['Total Nacional', '', '', '', 'Total', 'Todas las edades', '2025', '52']]
        rows += [['Total Nacional', f'{i:02d} Provincia {i}', '', '', 'Total', 'Todas las edades', '2025', '1'] for i in range(1, 53)]
        # Otro sexo/año/nivel no debe contarse.
        rows += [['Total Nacional', '01 Provincia 1', '01001 Municipio', '', 'Total', 'Todas las edades', '2025', '999']]
        rows += [['Total Nacional', '01 Provincia 1', '', '', 'Hombres', 'Todas las edades', '2025', '99']]
        if change:
            change(rows)
        buffer = io.StringIO(); writer = csv.writer(buffer, delimiter='\t')
        writer.writerow(columns); writer.writerows(rows)
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / 'source.zip'
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('65034.csv', buffer.getvalue().encode('utf-8-sig'))
        return path, hashlib.sha256(path.read_bytes()).hexdigest()

    def test_selects_unique_official_aggregates(self):
        source = extract_ine(*self.fixture(), 2025)
        self.assertEqual(source['national_population'], 52)
        self.assertEqual(len(source['rows']), 52)
        self.assertEqual(source['reference_date'], '2025-01-01')

    def test_integrity_coverage_duplicates_and_conservation(self):
        path, digest = self.fixture()
        with self.assertRaises(ValueError):
            extract_ine(path, '0'*64, 2025)
        for change in (lambda rows: rows.pop(1), lambda rows: rows.append(rows[1]), lambda rows: rows[0].__setitem__(-1, '53'), lambda rows: rows[1].__setitem__(-1, '1,5')):
            with self.assertRaises(ValueError):
                extract_ine(*self.fixture(change), 2025)


class AssignmentComparison(unittest.TestCase):
    def test_renumbered_map_matches_exactly_by_membership(self):
        result = compare_assignments({'a': '1', 'b': '1', 'c': '2'}, {'a': '9', 'b': '9', 'c': '8'}, same_unit_universe_accredited=True)
        self.assertEqual(result['exact_membership_pairs'], 2)
        self.assertTrue(all(p['jaccard'] == '1' for p in result['pairs']))

    def test_splits_merges_and_permutation(self):
        old = {'a': '1', 'b': '1'}; new = {'b': '3', 'a': '2'}
        result = compare_assignments(old, new, same_unit_universe_accredited=True)
        self.assertEqual(result['exact_membership_pairs'], 0)
        self.assertEqual(len(result['pairs']), 2)
        self.assertEqual([p['jaccard'] for p in result['pairs']], ['1/2', '1/2'])
        self.assertEqual(result, compare_assignments(dict(reversed(list(old.items()))), dict(reversed(list(new.items()))), same_unit_universe_accredited=True))

    def test_missing_or_non_accredited_universe_is_not_comparable(self):
        self.assertEqual(compare_assignments({'a': '1'}, {'a': '1'})['status'], 'NOT_COMPARABLE')
        self.assertEqual(compare_assignments({'a': '1'}, {'a': '1'}, same_unit_universe_accredited='false')['status'], 'NOT_COMPARABLE')
        result = compare_assignments({'a': '1'}, {'b': '1'}, same_unit_universe_accredited=True)
        self.assertEqual(result['status'], 'NOT_COMPARABLE')
        self.assertIsNone(result['pairs'])
        with self.assertRaises(ValueError):
            compare_assignments({}, {}, same_unit_universe_accredited=True)


class PreservedNationalResults(unittest.TestCase):
    folder = Path(__file__).resolve().parents[1] / 'docs/ESTUDIOS/modelo_nacional_2025_120000'

    def test_official_snapshot_reproduces_model_and_csv(self):
        source = json.loads((self.folder / 'fuente_poblacion.json').read_text())
        model = json.loads((self.folder / 'modelo.json').read_text())
        populations = {r['province_code']: r['population'] for r in source['rows']}
        self.assertEqual(set(populations), {f'{i:02d}' for i in range(1, 53)})
        self.assertEqual(sum(populations.values()), source['national_population'])
        self.assertEqual(source['national_population'], 49128297)
        self.assertEqual(source['source_zip_sha256'], '91d3ff9a90bac1c06e26df97179daa325b65fa77c9209879d6a40333b17057f3')
        self.assertEqual(model, calculate(populations, 120000))
        with (self.folder / 'reparto_provincial.csv').open() as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(len(rows), len(populations) * len(model['alternatives']))
        for alternative in model['alternatives']:
            actual = [r for r in rows if r['rule'] == alternative['rule']]
            self.assertEqual([r['province_code'] for r in actual], sorted(populations))
            self.assertEqual(sum(int(r['population']) for r in actual), source['national_population'])
            self.assertEqual(sum(int(r['k_assigned']) for r in actual), alternative['k_total'])
            for raw, expected in zip(actual, alternative['rows'], strict=True):
                for key in ('target_quota', 'allocation_quota'):
                    self.assertEqual(Fraction(raw[key]), Fraction(expected[key]))

    def test_manifest_hashes_and_comparison_cannot_claim_measured_matches(self):
        manifest = json.loads((self.folder / 'MANIFEST.json').read_text())
        for name, digest in manifest['files'].items():
            self.assertEqual(hashlib.sha256((self.folder / name).read_bytes()).hexdigest(), digest)
        generator = Path(__file__).resolve().parents[1] / 'herramientas/modelo_cuantitativo_nacional.py'
        self.assertEqual(hashlib.sha256(generator.read_bytes()).hexdigest(), manifest['generator_sha256'])
        report = json.loads((self.folder / 'comparacion_mapas.json').read_text())
        self.assertEqual(report['status'], 'NOT_COMPARABLE')
        self.assertIsNone(report['exact_matches'])
        self.assertIsNone(report['differences'])


if __name__ == '__main__':
    unittest.main()
