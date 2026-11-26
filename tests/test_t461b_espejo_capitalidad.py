"""T-461b: entrada de descubrimiento de las leyes de capitalidad (diarios oficiales autonómicos)."""
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "herramientas"))
import espejo_fuente_oficial as ef  # noqa: E402

T = "capitalidad-partidos-judiciales"


class EntradaCapitalidad(unittest.TestCase):
    def test_declarada_solo_para_descubrir_y_con_los_cinco_diarios(self):
        e = ef.declaracion(T)
        self.assertNotIn("url", e)  # no se espeja ni se sube: sin url ni sha256_esperado
        self.assertNotIn("sha256_esperado", e)
        self.assertEqual(set(e["hosts_permitidos"]),
                         {"dogc.gencat.cat", "www.xunta.gal", "www.boa.aragon.es", "www.caib.es", "www.gobiernodecanarias.org"})
        self.assertTrue(all(ef.host_sondeable(p, e["descubrir"]["sufijos_host"]) for p in e["descubrir"]["paginas"]))

    def test_descubrir_sondea_las_cinco_paginas_sin_red(self):
        visitadas = []

        def falsa(url, tope):
            visitadas.append(url)
            return 200, {"content-type": "text/html"}, b"<html><tr><td>x</td></tr></html>"

        with tempfile.TemporaryDirectory() as d:
            r = ef.descubrir(T, Path(d), peticion=falsa)
        self.assertEqual(len(r["paginas"]), 5)
        self.assertEqual(len(visitadas), 5)
        self.assertEqual(r["ficheros_de_datos"], [])


if __name__ == "__main__":
    unittest.main()
