"""Version 1.0.0; source/contract regression; 2026-10-26.
Scope: authenticated territorial input selection for Andalucía and Valencia.
Status: candidate. Origin: executor C original-run reproduction.
"""
from pathlib import Path
import json
import unittest
import yaml
from herramientas.catalogo_preparacion import lookup
from herramientas.resolver_ejecucion_completa import build_plan
from herramientas.consumir_par_fuentes_legislatura import validate_territorial_receipt

ROOT = Path(__file__).resolve().parents[1]

class TerritorialSourceContractTests(unittest.TestCase):
    def test_prepared_source_and_contract_bind_the_same_verified_edition(self):
        for territory, run, year in [('andalucia', 38082966768, 2025),
                                     ('comunidad_valenciana', 39315133646, 2023)]:
            with self.subTest(territory=territory):
                row = lookup(territory, '2025', ROOT/'configuracion/catalogo_preparacion.yaml')
                evidence = row['preparation_evidence']
                self.assertEqual(run, evidence['run_id'])
                receipt = json.loads((ROOT/evidence['receipt_path']).read_text())
                contract = yaml.safe_load((ROOT/row['contract_path']).read_text())
                baseline = contract['validation']['source_baseline']
                self.assertEqual((year, year), (contract['meta']['source_population_year'],
                                               contract['meta']['source_section_year']))
                for key in ('package_sha256','compatibility_identity_sha256',
                            'compatibility_report_sha256','population_year','section_year'):
                    self.assertEqual(receipt[key], evidence[key])
                    self.assertEqual(receipt[key], baseline[key])
                self.assertFalse(row['generation_enabled'])
                self.assertNotIn('generation_preflight', row.get('evidence', {}))
                self.assertFalse(contract['generation_state']['generation_enabled'])
                self.assertNotIn('pre_m04_run_id', contract['generation_state'])

    def test_reuse_reaccredits_the_selected_source_before_generation(self):
        for territory, run, year in [('andalucia',38082966768,2025),
                                     ('comunidad_valenciana',39315133646,2023)]:
            with self.subTest(territory=territory):
                plan=build_plan(territory=territory,edition='2025',execution_mode='reuse',
                                catalog=ROOT/'configuracion/catalogo_preparacion.yaml',root_dir=ROOT)
                self.assertEqual(run,plan['existing']['territorial_source']['run_id'])
                self.assertEqual((year,year),(plan['population_year'],plan['section_year']))
                self.assertTrue(plan['pre_m04_accreditation_planned'])
                self.assertEqual('planned_pre_m04_accreditation',plan['generation_gate']['route'])

    def test_valencia_keeps_independent_f10_receipt_and_source_2023(self):
        row, receipt = validate_territorial_receipt(root_dir=ROOT, territory='comunidad_valenciana',edition='2025')
        self.assertEqual(39315133646,receipt['run_id'])
        self.assertIs(row['independent_source_evidence']['promoted'],False)
        self.assertEqual('BLOCKED', row['independent_source_evidence']['geometry_admissibility'])
        contract=yaml.safe_load((ROOT/row['contract_path']).read_text())
        m02=contract['modulos']['modulo_02_construir_adyacencias']
        self.assertEqual('EPSG:25830',m02['working_crs'])
        self.assertEqual((1.0,1.0,0.0,0.0),(m02['min_shared_border_m'],m02['max_precision_overlap_area_m2'],m02['buffer_m'],m02['simplify_m']))
        self.assertEqual(3503,contract['validation']['expected_sections_geometry'])
        self.assertEqual(5216195,contract['validation']['expected_population_total_2023'])
        self.assertEqual(99,contract['territory_contract']['k_districts'])
