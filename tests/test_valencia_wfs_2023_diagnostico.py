"""Diagnóstico F10 independiente de tres secciones INE 2023; no promueve producto."""
from __future__ import annotations
import json
from pathlib import Path
import unittest
import pyproj
from shapely.geometry import shape
from shapely.ops import transform

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"docs/AUDITORIAS/CIERRE_FUENTES_20261017/INE_WFS_VALENCIA_2023_TRES_CUSEC.geojson"
EXPECTED={"4617201001","4619401008","4619401013"}

class ValenciaWFS2023Diagnostic(unittest.TestCase):
    def test_official_three_geometries(self):
        fc=json.loads(DATA.read_text(encoding="utf-8"))
        self.assertEqual(fc.get("type"),"FeatureCollection")
        fs=fc["features"]
        byid={f["properties"]["CUSEC"]: f for f in fs}
        self.assertEqual(len(fs),3)
        self.assertEqual(set(byid),EXPECTED)
        self.assertEqual({f["properties"]["TIPO"] for f in fs},{"SECCIONADO"})
        self.assertEqual({f["properties"]["CPRO"] for f in fs},{"46"})
        geo={k: shape(f["geometry"]) for k,f in byid.items()}
        for k,g in geo.items():
            self.assertFalse(g.is_empty,k)
            self.assertTrue(g.is_valid,k)
        projection=pyproj.Transformer.from_crs("EPSG:25830","EPSG:3035",always_xy=True).transform
        a=geo["4617201001"]
        results=[]
        for code in ("4619401008","4619401013"):
            b=geo[code]
            in_25830=a.intersection(b).area
            in_3035=transform(projection,a).intersection(transform(projection,b)).area
            results.append({"pair":["4617201001",code],
              "overlap_25830_m2":in_25830,"overlap_3035_m2":in_3035,
              "touches":a.touches(b),"intersects":a.intersects(b),
              "within_contract_1m2":in_3035<=1.0})
            self.assertGreaterEqual(in_25830,0.0)
            self.assertGreaterEqual(in_3035,0.0)
        print("DDD_F10_VALENCIA_2023_WFS_GEOMETRY_RESULT="+json.dumps({
          "source":str(DATA.relative_to(ROOT)),
          "source_crs":"EPSG:25830", "test_crs":"EPSG:3035",
          "official_timestamp":fc.get("timeStamp"),
          "rows":results},sort_keys=True))
