# -*- coding: utf-8 -*-
"""T-175 · enumeración exacta para territorios pequeños con la regla de calidad (ddd_motor2/exhaustivo.py).

VERSIÓN: 1.0.0
ANTERIOR: ninguna (fichero nuevo)
"""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_motor2.calidad import huella_plan, metricas  # noqa: E402
from ddd_motor2.exhaustivo import enumerar_exacto, escribir_composicion, huella_composicion  # noqa: E402
from ddd_motor2.reglas import Criterio, Problema, Reglas, Unidad, enumerar  # noqa: E402


def _caso(pops, k, criterio=None):
    us = tuple(Unidad(f"u{i}", p, f"{i:05d}", "01") for i, p in enumerate(pops))
    p = Problema(us, tuple((f"u{i}", f"u{i + 1}") for i in range(len(pops) - 1)))
    r = Reglas.desde_contrato({"validation": {
        "expected_districts": k, "population_floor_ratio": "0.5", "population_cap_ratio": "1.5",
        "target_tolerance_ratio": "0.1", "require_single_province_per_district": True,
        "province_districts": {"01": k}, "require_municipality_discipline": False}}, criterio or Criterio())
    return p, r


class EnumeracionExacta(unittest.TestCase):
    def test_elige_el_mejor_por_calidad(self):
        # Cadena 10-20-30-40, K=2 (objetivo 50, [25, 75]): válidos 10+20|30+40 (30/70) y 10+20+30|40 (60/40).
        # 60/40 tiene desvío 0,2 < 0,4: gana.
        p, r = _caso([10, 20, 30, 40], 2)
        res = enumerar_exacto(p, r)
        self.assertEqual((res["metodo"], res["completo"], res["validos"], res["empatados"]),
                         ("enumeracion", True, 2, 1))
        self.assertEqual(huella_plan(res["mejor"]), huella_plan({"u0": "a", "u1": "a", "u2": "a", "u3": "b"}))
        self.assertEqual(res["mejor_metricas"]["desvio_max_exacto"], "1/5")
        self.assertEqual(res["segundo_clave"]["desvio_max"], 0.4)

    def test_presupuesto_agotado_es_cadena(self):
        p, r = _caso([10] * 12, 3)
        res = enumerar_exacto(p, r, presupuesto=5)
        self.assertEqual((res["metodo"], res["completo"], res["nodos"]), ("cadena", False, 5))

    def test_criterio_tamano_no_intenta_si_es_grande(self):
        crit = Criterio(metodo="tamano", tamano_max_k=1, tamano_max_unidades=3)
        p, r = _caso([10, 20, 30, 40], 2, crit)
        res = enumerar_exacto(p, r)
        self.assertEqual((res["metodo"], res["intentada"]), ("cadena", False))
        crit = Criterio(metodo="tamano", tamano_max_k=2)
        p, r = _caso([10, 20, 30, 40], 2, crit)
        self.assertEqual(enumerar_exacto(p, r)["validos"], 2)

    def test_reproducible(self):
        p, r = _caso([10, 20, 30, 40, 25, 35], 3)
        a, b = enumerar_exacto(p, r), enumerar_exacto(p, r)
        self.assertEqual((a["huella"], a["validos"], huella_plan(a["mejor"])),
                         (b["huella"], b["validos"], huella_plan(b["mejor"])))
        # El mejor es el mínimo de la regla entre todos los planes válidos (enumerados aparte).
        self.assertEqual(metricas(p, r, a["mejor"])["clave"],
                         min(metricas(p, r, x)["clave"] for x in enumerar(p, r)["planes"]))

    def test_escribir_composicion(self):
        tmp = Path(tempfile.mkdtemp())
        base = tmp / "base.csv"
        with open(base, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["CUSEC_KEY", "district_id", "section_pop", "ddd_unit_id"])
            w.writerows([["s1", "5", 10, "A"], ["s2", "5", 10, "A"], ["s3", "9", 10, "B"]])
        out = escribir_composicion(base, {"A": "x", "B": "y"}, tmp / "o.csv", {})
        with open(out, encoding="utf-8") as fh:
            filas = list(csv.DictReader(fh))
        self.assertEqual([f["district_id"] for f in filas], ["0", "0", "1"])
        self.assertEqual(huella_composicion(out, {}), huella_plan({"s1": 0, "s2": 0, "s3": 1}))
        with self.assertRaises(ValueError):
            escribir_composicion(base, {"A": "x"}, tmp / "p.csv", {})


class CertificadorYCompetidorCoinciden(unittest.TestCase):
    def test_mismo_recuento_y_mismo_mejor(self):
        try:
            import ortools  # noqa: F401
        except ImportError:  # pragma: no cover
            self.skipTest("sin ortools")
        from herramientas.certificador_exacto import resolver
        p, r = _caso([10, 20, 30, 40, 25, 35, 15], 3)
        ex = enumerar_exacto(p, r)
        cp = resolver(p, r, tiempo=30, hilos=1, objetivo="enumerar")
        self.assertEqual((cp["estado"], cp["planes_validos"]), ("ENUMERADO", ex["validos"]))
        mejor_cp = min((metricas(p, r, x) for x in cp["_planes"]), key=lambda m: m["clave"])
        self.assertEqual(mejor_cp["huella_plan"], huella_plan(ex["mejor"]))


class M05DesdeComposicion(unittest.TestCase):
    def test_reescribe_district_id(self):
        try:
            import geopandas as gpd
            from shapely.geometry import Point
        except ImportError:  # pragma: no cover
            self.skipTest("sin geopandas")
        from ddd_core.m05_swap_polish import load_geo, write_geo
        from ddd_motor2.competidor import m05_desde_composicion
        tmp = Path(tempfile.mkdtemp())
        g = gpd.GeoDataFrame({"CUSEC_KEY": ["s1", "s2"], "district_id": [0, 0]},
                             geometry=[Point(0, 0), Point(1, 0)], crs="EPSG:4326")
        write_geo(g, tmp / "m05.geojson.zip")
        comp = tmp / "c.csv"
        comp.write_text("CUSEC_KEY,district_id\ns1,1\ns2,0\n", encoding="utf-8")
        out = m05_desde_composicion(tmp / "m05.geojson.zip", comp, tmp / "n.geojson.zip", {"id_field": "CUSEC_KEY"})
        self.assertEqual(list(load_geo(out).sort_values("CUSEC_KEY")["district_id"]), [1, 0])


if __name__ == "__main__":
    unittest.main()
