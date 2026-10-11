"""VERSIÓN: 1.0.0; NOMBRE: recibo histórico; FECHA: 2026-10-08.
ALCANCE: bytes conservados y límites de acreditación; ESTADO: CI_PENDIENTE.
CAMBIOS: pruebas de inventario y correspondencia pendiente; MOTIVO: evitar ediciones inferidas.
ORIGEN: nuevo, sin predecesor.
"""
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from herramientas.inventariar_cartografia_historica import sectioning_reference
from herramientas.comparar_cartografia_nacional import workbook_summary

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'docs/ESTUDIOS/cartografia_nacional_20261008'


class HistoricalInventory(unittest.TestCase):
    def test_archived_originals_match_inventory_hashes_and_edition_unknown(self):
        inventory=json.loads((FOLDER/'inventario.json').read_text())
        self.assertEqual(len(inventory['files']),5)
        self.assertEqual(len({r['archived_path'] for r in inventory['files']}),4)
        for record in inventory['files']:
            raw=gzip.decompress((FOLDER/record['archived_path']).read_bytes())
            self.assertEqual(hashlib.sha256(raw).hexdigest(),record['file_sha256'])
            self.assertIsNone(record['geometry_edition']);self.assertIsNone(record['population_edition'])

    def test_real_invalid_geometry_does_not_produce_temporal_metrics(self):
        gate=json.loads((FOLDER/'comparabilidad_temporal.json').read_text())
        self.assertEqual(gate['status'],'NOT_COMPARABLE')
        self.assertIsNone(gate['pairs']);self.assertIsNone(gate['coverage']);self.assertIsNone(gate['population_differences'])
        self.assertFalse(gate['national_2025_district_map_available'])
        for report in gate['input_reports']:
            self.assertTrue(any(error['id']=='44' and 'GEOMETRY_INVALID' in error['error'] for error in report['errors']))

    def test_raw_equivalence_is_not_temporal_change(self):
        record=json.loads((FOLDER/'equivalencia_archivos.json').read_text())
        self.assertEqual(record['raw_coordinate_identical_pairs'],391)
        self.assertEqual(record['normalized_attribute_identical_pairs'],391)
        self.assertIsNone(record['temporal_change_metrics'])
        self.assertEqual(record['workbook_members_with_different_hashes'],['docProps/core.xml'])

    def test_reference_sections_are_not_a_2025_district_map(self):
        reference=json.loads((FOLDER/'referencia_seccionado_2025.json').read_text())
        self.assertEqual(reference['unit_count'],36554);self.assertEqual(reference['unique_ids'],36554)
        self.assertEqual(len(reference['province_counts']),52)
        self.assertEqual(reference['unit_kind'],'census_sections')
        with tempfile.NamedTemporaryFile() as source:
            source.write(b'not an accredited source');source.flush()
            with self.assertRaisesRegex(ValueError,'HASH_MISMATCH'):
                sectioning_reference(source.name,hashlib.sha256(b'not an accredited source').hexdigest())

    def test_workbook_dates_are_not_editions_and_macros_not_executed(self):
        record=next(r for r in json.loads((FOLDER/'inventario.json').read_text())['files'] if r['name'].endswith('.xlsm'))
        with tempfile.NamedTemporaryFile(suffix='.xlsm') as source:
            source.write(gzip.decompress((FOLDER/record['archived_path']).read_bytes()));source.flush()
            summary=workbook_summary(source.name)
        self.assertEqual(summary['row_count_excluding_header'],391)
        self.assertNotIn('geometry_edition',summary)
        self.assertEqual(summary['macro_members'],[])


if __name__=='__main__':
    unittest.main()
