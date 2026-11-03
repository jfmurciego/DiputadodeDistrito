"""Versión 1.0.0; 2026-11-03; candidato. T-37: la copia web de un candidato lleva una feature por distrito (K), no por sección."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from shapely.geometry import shape

from ddd_ensemble.gallery import _write_web_geojson, dissolve_by_district
from herramientas.validar_republicacion_ensemble import validate

COLS, ROWS, K = 28, 19, 3  # 532 secciones como Salamanca
UTM = {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::25830"}}


def candidate(origin=(-5.75, 40.875), step=2 ** -10, crs=None):
    features = []
    for r in range(ROWS):
        for c in range(COLS):
            x0, y0 = origin[0] + c * step, origin[1] + r * step
            ring = [[x0, y0], [x0 + step, y0], [x0 + step, y0 + step], [x0, y0 + step], [x0, y0]]
            features.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [ring]},
                             "properties": {"CUSEC_KEY": f"37{r:03d}{c:03d}", "district_id": c * K // COLS, "POP_2023": 100}})
    data = {"type": "FeatureCollection", "features": features}
    if crs:
        data["crs"] = crs
    return data


def write(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class CopiaWebPorDistritoTests(unittest.TestCase):
    def test_532_secciones_pasan_a_k_features_con_propiedades_por_distrito(self):
        data = candidate()
        self.assertEqual(len(data["features"]), 532)
        web = dissolve_by_district(data)
        self.assertEqual(len(web["features"]), K)  # rojo antes: 532 != 3 («distritos observados 532 != 3»)
        self.assertEqual(sum(f["properties"]["sections"] for f in web["features"]), 532)
        self.assertEqual(sum(f["properties"]["POP_2023"] for f in web["features"]), 53200)
        self.assertEqual({f["properties"]["district_id"] for f in web["features"]}, {0, 1, 2})
        total = sum(shape(f["geometry"]).area for f in data["features"])
        self.assertAlmostEqual(sum(shape(f["geometry"]).area for f in web["features"]), total, places=12)
        for f in web["features"]:
            self.assertEqual(shape(f["geometry"]).geom_type, "Polygon")  # distritos contiguos

    def test_es_idempotente_y_no_toca_datos_sin_distrito(self):
        web = dissolve_by_district(candidate())
        self.assertIs(dissolve_by_district(web), web)
        sin_campo = candidate()
        for f in sin_campo["features"]:
            f["properties"].pop("district_id")
        self.assertIs(dissolve_by_district(sin_campo), sin_campo)

    def test_copia_web_en_grados_y_proyectada_ambas_k_features_wgs84(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            degrees = write(root / "d.geojson", candidate(crs={"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}}))
            _write_web_geojson(degrees, root / "web_d.geojson")
            projected = write(root / "p.geojson", candidate(origin=(700000.0, 4500000.0), step=128.0, crs=UTM))
            _write_web_geojson(projected, root / "web_p.geojson")
            for name in ("web_d", "web_p"):
                web = json.loads((root / f"{name}.geojson").read_text(encoding="utf-8"))
                self.assertEqual(len(web["features"]), K, name)
                self.assertNotIn("crs", web)
                xs = [x for f in web["features"] for x, _ in _pairs(f["geometry"]["coordinates"])]
                self.assertTrue(all(-180 <= x <= 180 for x in xs), name)

    def test_la_validacion_de_republicacion_exige_una_feature_por_distrito(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "analysis").mkdir()
            (root / "analysis/summary.json").write_text(json.dumps({"complete": True, "candidate_count_valid": 10}), encoding="utf-8")
            for i in range(10):
                src = write(root / "results" / f"c{i:02d}" / "candidate.geojson", candidate())
                (root / "site/assets").mkdir(parents=True, exist_ok=True)
                _write_web_geojson(src, root / "site/assets" / f"c{i:02d}.geojson")
            result = validate(root)
            self.assertEqual((result["analytical_wgs84"], result["web_asset_count"]), (10, 10))
            # web sin disolver (copia de la analítica): era el fallo de Salamanca
            shutil.copy2(root / "results/c00/candidate.geojson", root / "site/assets/c00.geojson")
            with self.assertRaisesRegex(SystemExit, "debe haber una por distrito"):
                validate(root)

    def test_el_publicador_cuenta_features_contra_expected_districts(self):
        # «Validar sitio candidato completo»: observed = len(features); con la copia disuelta coincide con K.
        web = dissolve_by_district(candidate())
        self.assertEqual(len(web["features"]), K)


def _pairs(value):
    if isinstance(value, list):
        if len(value) >= 2 and all(isinstance(v, (int, float)) for v in value[:2]):
            yield value[0], value[1]
        else:
            for item in value:
                yield from _pairs(item)


if __name__ == "__main__":
    unittest.main()
