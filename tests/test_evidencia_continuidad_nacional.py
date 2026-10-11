"""Versión 1.0.0; 2026-10-11; diagnóstico N03–N06; nuevo sin predecesor."""
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from herramientas.evidencia_continuidad_nacional import diagnose, ROOT

class ContinuityTests(unittest.TestCase):
    def test_real_diagnosis_preserves_source(self):
        source=ROOT/'docs/ESTUDIOS/cartografia_nacional_20261008/inputs/a2c8f630bd84_map.geojson.gz'
        before=source.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            report=diagnose(Path(directory)/'evidence')
        self.assertEqual(source.read_bytes(),before)
        self.assertEqual(report['N03']['status'],'BLOCKED')
        self.assertIsNone(report['N03']['geometry_edition'])
        self.assertFalse(report['N04']['valid'])
        self.assertIn('Hole lies outside shell',report['N04']['reason'])
        self.assertTrue(any(not x['covered_by_own_shell'] for x in report['N04']['hole_tests']))
        self.assertEqual(report['N04']['original_sha256'],hashlib.sha256(gzip.decompress(before)).hexdigest())
        self.assertFalse(report['N04']['repair_performed'])
        self.assertEqual([a['k_total'] for a in report['N05']['alternatives']['alternatives']],[383,407,435,409,409])
        self.assertFalse(report['N06']['decision_adopted'])
if __name__=='__main__': unittest.main()
