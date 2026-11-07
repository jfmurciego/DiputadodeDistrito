# -*- coding: utf-8 -*-
"""T-71: recuperación de composición sección→distrito por geometría (sintético, sin red)."""
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "herramientas"))
import composicion_m06 as cm  # noqa: E402
import recuperar_composicion_ine as rc  # noqa: E402


def cuadro(x, y):
    return [[[x, y], [x + 1, y], [x + 1, y + 1], [x, y + 1], [x, y]]]


def m06(pops):
    feats = [{"type": "Feature", "properties": {"district_id": d, "section_count": n, "district_pop": p},
              "geometry": {"type": "Polygon", "coordinates": cuadro(2 * d, 0)}} for d, (n, p) in pops.items()]
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("t_m06_distritos.geojson", json.dumps({"type": "FeatureCollection", "features": feats}))
    return b.getvalue()


def secciones(items):
    feats = [{"type": "Feature", "properties": {"CUSEC": c, "TIPO": t, "CSEC": c[-3:]},
              "geometry": {"type": "Polygon", "coordinates": cuadro(x, 0)}} for c, t, x in items]
    return json.dumps({"type": "FeatureCollection", "features": feats}).encode()


class RecuperarComposicion(unittest.TestCase):
    ITEMS = [("0200101001", "SECCIONADO", 0.2), ("0200101002", "SECCIONADO", 0.5),
             ("0200102001", "SECCIONADO", 2.3), ("0200100000", "DISTRITO", 0.0)]
    POB = {"0200101001": 10, "0200101002": 20, "0200102001": 5}

    def test_asigna_y_valida(self):
        comp = rc.asignar(secciones(self.ITEMS), m06({0: (2, 30), 1: (1, 5)}), self.POB)
        filas = cm.validar(comp, m06({0: (2, 30), 1: (1, 5)}))
        self.assertEqual(filas, [["0200101001", 0, 10], ["0200101002", 0, 20], ["0200102001", 1, 5]])

    def test_no_cuadra_poblacion(self):
        comp = rc.asignar(secciones(self.ITEMS), m06({0: (2, 31), 1: (1, 5)}), self.POB)
        with self.assertRaises(ValueError):
            cm.validar(comp, m06({0: (2, 31), 1: (1, 5)}))

    def test_seccion_fuera_de_todo_poligono(self):
        with self.assertRaises(ValueError):
            rc.asignar(secciones([("0200101001", "SECCIONADO", 50.2)]), m06({0: (1, 10)}), self.POB)


if __name__ == "__main__":
    unittest.main()


class ContrasteObservatorio(unittest.TestCase):
    def test_contrastar(self):
        import contrastar_observatorio_2023 as co
        zv = {"A": {"PP": 5, "PSOE": 3}, "B": {"PP": 2}, "C": {"PP": 1}}
        ov = co.votos_obs({"s": ["PP", "PSOE"], "r": {"A": [0, 0, 8, [[0, 5], [1, 3]]], "B": [0, 0, 3, [[0, 3]]], "D": [0, 0, 1, [[0, 1]]]}})
        r = co.contrastar(zv, ov)
        self.assertEqual(r, [3, 3, 1, 1, 1, 10, 11, "PP"])
