"""Versión 1.0.0; 2026-10-11; N07; candidato; nuevo sin predecesor.
Pruebas positivas y negativas de integridad administrativa nacional.
"""
import copy
import unittest
import tempfile
import hashlib
import csv
import json
from pathlib import Path
from herramientas.crosswalk_nacional import materialize, ROOT
from herramientas.crosswalk_nacional import validate_rows

class CrosswalkTests(unittest.TestCase):
    def setUp(self):
        self.rows = [dict(CPRO=f'{i:02d}', CMUN='001', CUMUN=f'{i:02d}001', CDIS='01', CSEC='001', CUSEC=f'{i:02d}00101001') for i in range(1,53)]
        self.counts = {f'{i:02d}':1 for i in range(1,53)}
    def test_complete(self):
        result=validate_rows(self.rows, list(reversed(self.rows)), self.counts)
        self.assertEqual(result['unit_count'],52)
        self.assertEqual((result['ceuta'],result['melilla']),(1,1))
    def reject(self, change):
        rows=copy.deepcopy(self.rows); change(rows)
        with self.assertRaises(ValueError): validate_rows(self.rows,rows,self.counts)
    def test_duplicate(self): self.reject(lambda r:r.append(r[0]))
    def test_loss(self): self.reject(lambda r:r.pop())
    def test_province(self): self.reject(lambda r:r[0].update(CPRO='99'))
    def test_prefix(self): self.reject(lambda r:r[0].update(CPRO='02'))
    def test_type(self): self.reject(lambda r:r[0].update(CUSEC=100101001))
    def test_format(self): self.reject(lambda r:r[0].update(CUSEC='010010100'))
    def test_equal_count_substitution(self): self.reject(lambda r:r[0].update(CSEC='002',CUSEC='0100101002'))
    def test_city_municipality(self): self.reject(lambda r:r[-1].update(CMUN='002',CUMUN='52002',CUSEC='5200201001'))
    def test_expected_counts(self):
        counts=dict(self.counts); counts['01']=2
        with self.assertRaises(ValueError): validate_rows(self.rows,self.rows,counts)
    def test_wrong_source_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'wrong-2025.zip'; source.write_bytes(b'not the protected source')
            output=Path(directory)/'out'
            with self.assertRaisesRegex(ValueError,'SECTIONING_REFERENCE_HASH_MISMATCH'):
                materialize(source,output)
            self.assertFalse(output.exists())
    def test_real_artifact(self):
        folder=ROOT/'docs/ESTUDIOS/N07_20261011/result'
        evidence=json.loads((folder/'evidence.json').read_text())
        payload=(folder/'crosswalk.csv').read_bytes()
        self.assertEqual(hashlib.sha256(payload).hexdigest(),evidence['crosswalk_sha256'])
        rows=list(csv.DictReader(payload.decode().splitlines()))
        result=validate_rows(rows,rows,evidence['province_counts'])
        self.assertEqual(result['unit_count'],36554)
        self.assertEqual(evidence['edition'],2025)
        self.assertEqual(evidence['geometry_invalid'],[])
if __name__=='__main__': unittest.main()
