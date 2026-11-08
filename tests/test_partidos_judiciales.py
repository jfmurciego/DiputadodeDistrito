"""T-64: partidos judiciales (Ley 38/1988, Anexo I) y su uso en C13."""
import csv
import unittest
from collections import Counter, defaultdict
from pathlib import Path

from herramientas import generar_nombres_comunidades_nacional as c13
from herramientas import generar_partidos_judiciales as g

RAIZ = Path(__file__).resolve().parents[1]


def leer():
    with (RAIZ / g.SALIDA).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(l for l in f if not l.startswith("#")))


class Reglas(unittest.TestCase):
    def test_plegar_articulos_y_prefijo(self):
        self.assertEqual(g.plegar("Arahal, El"), g.plegar("Arahal"))
        self.assertTrue(g.parecidos("Setenil", "Setenil de las Bodegas"))
        self.assertFalse(g.parecidos("Ola", "Olabarría"))

    def test_conciliacion_no_inventa(self):
        ine = {"42001": "Abejar", "42002": "Adradas"}
        filas = [("Soria", 3, "001", "Abejar"), ("Soria", 1, "002", "Adradas"), ("Soria", 2, "999", "Fantasma")]
        asig, resto, _ = g.conciliar(filas, ine)
        self.assertEqual({k: v[1] for k, v in asig.items()}, {"42001": 3, "42002": 1})
        self.assertEqual([r[3] for r in resto], ["Fantasma"])


class Datos(unittest.TestCase):
    def test_cada_municipio_en_exactamente_un_partido(self):
        filas = leer()
        codigos = [r["codigo_ine"] for r in filas]
        self.assertEqual(len(codigos), len(set(codigos)))
        ine = g.cargar_ine()
        self.assertTrue(set(codigos) <= set(ine))
        for r in filas:
            self.assertEqual(r["codigo_ine"][:2], r["provincia"])
        # los no conciliados son exactamente el complemento del inventario
        with (RAIZ / g.NO_CONCILIADOS).open(encoding="utf-8", newline="") as f:
            sin = {r["codigo_ine"] for r in csv.DictReader(f) if r["origen"] == "ine_2025"}
        self.assertEqual(sin, set(ine) - set(codigos))

    def test_cobertura_y_excepciones_listadas(self):
        ine = g.cargar_ine()
        self.assertGreaterEqual(len(leer()) / len(ine), 0.98)
        with (RAIZ / "datos/distritos/municipios_ine_2025.csv").open(encoding="utf-8", newline="") as f:
            pob = {r["codigo_ine"]: int(r["poblacion_2025"]) for r in csv.DictReader(f)}
        con = sum(pob[r["codigo_ine"]] for r in leer())
        self.assertGreaterEqual(con / sum(pob.values()), 0.985)

    def test_contraste_boe_soria(self):
        # Ley 38/1988, Anexo I, provincia de Soria: 3 partidos (Almazán 1, Burgo de Osma 2, Soria 3).
        filas = [r for r in leer() if r["provincia"] == "42"]
        self.assertEqual(len(filas), 183)
        self.assertEqual(sorted(Counter(r["partido_judicial"] for r in filas).items()),
                         [("1", 47), ("2", 34), ("3", 102)])
        por = {r["nombre_ine"]: r["partido_judicial"] for r in filas}
        self.assertEqual((por["Almazán"], por["Burgo de Osma-Ciudad de Osma"], por["Soria"]), ("1", "2", "3"))

    def test_contraste_boe_cantabria(self):
        # Anexo I, provincia de Cantabria: 102 municipios en 7 partidos.
        filas = [r for r in leer() if r["provincia"] == "39"]
        self.assertEqual(len(filas), 102)
        self.assertEqual(sorted(Counter(r["partido_judicial"] for r in filas).items(), key=lambda x: int(x[0])),
                         [("1", 20), ("2", 14), ("3", 6), ("4", 19), ("5", 11), ("6", 12), ("7", 20)])
        por = {r["nombre_ine"]: r["partido_judicial"] for r in filas}
        self.assertEqual((por["Torrelavega"], por["Laredo"], por["Santander"], por["Potes"]), ("1", "2", "3", "4"))


class C13(unittest.TestCase):
    def test_partidos_partidos(self):
        ds = [{"district_id": 0, "codigos": ["A", "B"]}, {"district_id": 1, "codigos": ["B", "C"]}]
        en = defaultdict(set)
        for d in ds:
            for c in d["codigos"]:
                en[c].add(d["district_id"])
        m = c13.partidos_partidos(ds, {"A": "p1", "B": "p1", "C": "p2"}, {"A": 1, "B": 2, "C": 3, "D": 4}, en)
        self.assertEqual(m["comarcas_partidas"], 1)  # p1 toca los distritos 0 y 1
        self.assertEqual(m["cobertura_municipios"], 1.0)

    def test_informes_evaluan_las_49(self):
        informes = list((RAIZ / c13.SALIDA).glob("informe_congreso_*.md"))
        self.assertGreaterEqual(len(informes), 49)  # 52 con Alicante, Barcelona y Málaga (08-11)
        for p in informes:
            self.assertIn("partidos judiciales partidos", p.read_text(encoding="utf-8"), p.name)


if __name__ == "__main__":
    unittest.main()
