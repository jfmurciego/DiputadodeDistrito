"""Versión 1.0.0; 2026-11-03; candidato. T-36: la republicación del ensemble admite candidatos en WGS84 sin confundir canónico y web."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from herramientas.validar_republicacion_ensemble import validate

ROOT = Path(__file__).resolve().parents[1]
CRS84 = {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}}
UTM = {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::25830"}}


def collection(coords, crs=None):
    data = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"district_id": 1}, "geometry": {"type": "Polygon", "coordinates": [coords]}}]}
    if crs:
        data["crs"] = crs
    return data


DEGREES = [[-5.66, 40.97], [-5.65, 40.97], [-5.65, 40.98], [-5.66, 40.97]]
METERS = [[700000.0, 4500000.0], [700100.0, 4500000.0], [700100.0, 4500100.0], [700000.0, 4500000.0]]


def build(root: Path, n=10, analytical=DEGREES, web=DEGREES, analytical_crs=CRS84, web_crs=CRS84, complete=True, same=True):
    (root / "analysis").mkdir(parents=True)
    (root / "analysis/summary.json").write_text(json.dumps({"complete": complete, "candidate_count_valid": n}), encoding="utf-8")
    (root / "site/assets").mkdir(parents=True)
    for i in range(n):
        cid = f"cand-{i:02d}"
        (root / "results" / cid).mkdir(parents=True)
        a = json.dumps(collection(analytical, analytical_crs))
        (root / "results" / cid / "candidate.geojson").write_text(a, encoding="utf-8")
        w = a if same else json.dumps(collection(web, web_crs))
        (root / "site/assets" / f"{cid}.geojson").write_text(w, encoding="utf-8")


class RepublicacionTests(unittest.TestCase):
    def run_case(self, **kwargs):
        with tempfile.TemporaryDirectory() as td:
            build(Path(td), **kwargs)
            return validate(Path(td))

    def test_candidatos_proyectados_como_aragon_siguen_validando(self):
        r = self.run_case(analytical=METERS, analytical_crs=UTM, web=DEGREES, web_crs=None, same=False)
        self.assertEqual((r["analytical_projected"], r["analytical_wgs84"], r["web_asset_count"]), (10, 0, 10))

    def test_candidatos_ya_en_grados_como_salamanca_validan_si_la_web_coincide(self):
        # Rojo antes de T-36: «No se reconoce la copia analítica proyectada esperada».
        r = self.run_case()
        self.assertEqual((r["analytical_projected"], r["analytical_wgs84"], r["complete"]), (0, 10, "true"))

    def test_candidato_en_grados_con_web_distinta_se_rechaza(self):
        other = [[-5.70, 41.0], [-5.69, 41.0], [-5.69, 41.01], [-5.70, 41.0]]
        with self.assertRaisesRegex(SystemExit, "no coincide"):
            self.run_case(web=other, same=False)

    def test_web_proyectada_o_con_crs_proyectado_se_rechaza(self):
        with self.assertRaisesRegex(SystemExit, "fuera de WGS84"):
            self.run_case(analytical=METERS, analytical_crs=UTM, web=METERS, web_crs=None, same=False)
        with self.assertRaisesRegex(SystemExit, "CRS proyectado"):
            self.run_case(analytical=METERS, analytical_crs=UTM, web=DEGREES, web_crs=UTM, same=False)

    def test_exige_diez_candidatos_validos_y_emparejados(self):
        with self.assertRaisesRegex(SystemExit, "incompleto"):
            self.run_case(complete=False)
        with self.assertRaisesRegex(SystemExit, "incompleto"):
            self.run_case(n=9)
        with tempfile.TemporaryDirectory() as td:
            build(Path(td))
            next((Path(td) / "site/assets").glob("*.geojson")).rename(Path(td) / "site/assets/otro.geojson")
            with self.assertRaisesRegex(SystemExit, "no se corresponden"):
                validate(Path(td))

    def test_mezcla_de_candidatos_proyectados_y_en_grados(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build(root)
            first = sorted((root / "results").glob("*/candidate.geojson"))[0]
            cid = first.parent.name
            first.write_text(json.dumps(collection(METERS, UTM)), encoding="utf-8")
            (root / "site/assets" / f"{cid}.geojson").write_text(json.dumps(collection(DEGREES)), encoding="utf-8")
            r = validate(root)
        self.assertEqual((r["analytical_projected"], r["analytical_wgs84"]), (1, 9))

    def test_el_workflow_usa_la_herramienta_y_ya_no_la_guarda_antigua(self):
        text = (ROOT / ".github/workflows/generar-alternativas-territoriales.yml").read_text(encoding="utf-8")
        self.assertIn("python herramientas/validar_republicacion_ensemble.py --root work/ensemble --expected 10", text)
        self.assertNotIn("No se reconoce la copia analítica proyectada esperada", text)


if __name__ == "__main__":
    unittest.main()
