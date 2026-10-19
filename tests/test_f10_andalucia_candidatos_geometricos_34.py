"""Verify 34 strictly geometric INE 2025/2026 Andalucia candidate rows.

A candidate near 100% area overlap is not electoral legal correspondence:
no votes are transferred, no F10 gate is promoted.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
import unittest
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform

BASE=Path(__file__).resolve().parents[1]/"docs/AUDITORIAS/CIERRE_FUENTES_20261017"
CSV=BASE/"ANDALUCIA_CANDIDATOS_GEOMETRICOS_34_20261019.csv"
TRANSFORMER=Transformer.from_crs("EPSG:25830","EPSG:3035",always_xy=True).transform
EXPECTED_MUNICIPALITIES=17

class Andalucia2025_2026Evidence(unittest.TestCase):
    def test_all_34_candidates_are_reproducible(self):
        with CSV.open("r",encoding="utf-8",newline="") as f:
            rows=list(csv.DictReader(f,delimiter=";"))
        self.assertEqual(len(rows),34)
        self.assertEqual(len({r["CUSEC_cambiada"] for r in rows}),34)
        self.assertEqual({r["estado"] for r in rows},
                         {"CANDIDATO_GEOMETRICO_NO_EQUIVALENCIA_ELECTORAL"})
        self.assertEqual(sum(r["sentido"]=="2026_to_2025" for r in rows),25)
        self.assertEqual(sum(r["sentido"]=="2025_to_2026" for r in rows),9)
        municipalities={r["municipio"] for r in rows}
        self.assertEqual(len(municipalities),EXPECTED_MUNICIPALITIES)
        sources={}
        for mun in municipalities:
            for year in (2025,2026):
                p=BASE/f"ANDALUCIA_EXTRACTED_{mun}_{year}.geojson"
                doc=json.loads(p.read_text(encoding="utf-8"))
                self.assertEqual(doc["type"],"FeatureCollection")
                self.assertEqual(doc["numberMatched"],len(doc["features"]))
                self.assertEqual(doc["numberReturned"],len(doc["features"]))
                self.assertEqual(doc["crs"]["properties"]["name"],
                                 "urn:ogc:def:crs:EPSG::25830")
                self.assertEqual(doc["ddd_extraction"]["method"],
                                 "TinyFish textual extraction reserialized; not raw HTTP bytes")
                polygons={}
                for feat in doc["features"]:
                    attrs=feat["properties"]
                    self.assertEqual(attrs["CUMUN"],mun)
                    self.assertEqual(attrs["TIPO"],"SECCIONADO")
                    cid=attrs["CUSEC"]
                    self.assertNotIn(cid,polygons)
                    geom=shape(feat["geometry"])
                    self.assertTrue(geom.is_valid and not geom.is_empty,cid)
                    polygons[cid]=geom
                sources[mun,year]=polygons
        for mun in municipalities:
            old=set(sources[mun,2025])
            new=set(sources[mun,2026])
            self.assertEqual(new-old,
               {r["CUSEC_cambiada"] for r in rows
                if r["municipio"]==mun and r["sentido"]=="2026_to_2025"})
            self.assertEqual(old-new,
               {r["CUSEC_cambiada"] for r in rows
                if r["municipio"]==mun and r["sentido"]=="2025_to_2026"})
        for row in rows:
            with self.subTest(cusec=row["CUSEC_cambiada"]):
                code=row["CUSEC_cambiada"]
                candidate=row["CUSEC_contraparte_principal"]
                mun=row["municipio"]
                self.assertTrue(code.startswith(mun))
                self.assertTrue(candidate.startswith(mun))
                source_year,target_year=(2026,2025) if row["sentido"]=="2026_to_2025" else (2025,2026)
                self.assertIn(code,sources[mun,source_year])
                self.assertIn(candidate,sources[mun,target_year])
                a=transform(TRANSFORMER,sources[mun,source_year][code])
                b=transform(TRANSFORMER,sources[mun,target_year][candidate])
                self.assertGreater(a.area,0.0)
                fraction=a.intersection(b).area/a.area
                self.assertGreater(fraction,0.9999)
                self.assertAlmostEqual(
                    fraction*100,float(row["coincidencia_superficie_pct"]),
                    delta=0.0005)
        print("DDD_F10_ANDALUCIA_34_REPRODUCED: 17 municipalities, 34 geographic candidate matches. Electoral crosswalk remains BLOCKED.")

if __name__=="__main__":
    unittest.main()
