"""T-59: nombres de distrito (C12) y comarcas partidas (C13) nacionales."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from herramientas import generar_nombres_comunidades_nacional as g

RAIZ = Path(__file__).resolve().parents[1]


def distrito(i, codigos, cx, cy, pob=100000):
    return {"district_id": i, "poblacion": pob, "codigos": codigos, "nombres_ine": codigos, "cx": cx, "cy": cy,
            "provincia": "22"}


class Reglas(unittest.TestCase):
    def test_articulo_y_toponimia(self):
        self.assertEqual(g.romper_articulo("Coruña, A"), "A Coruña")
        self.assertEqual(g.romper_articulo("Vall d'Uixó, la"), "La Vall d'Uixó")
        self.assertEqual(g.romper_articulo("Escala, L'"), "L'Escala")
        self.assertEqual(g.nombre_es("x", "Girona", {"x": "Gerona"}), "Gerona")

    def test_municipio_dividido_numerado_norte_a_sur(self):
        ds = [distrito(0, ["A"], 5, 10), distrito(1, ["A"], 9, 30), distrito(2, ["A"], 1, 30)]
        filas, _ = g.nombrar("t", ds, {"A": 9}, {}, {})
        nombres = {f["district_id"]: f["nombre_distrito"] for f in filas}
        # norte primero (cy mayor); a igual latitud, oeste (cx menor) primero
        self.assertEqual(nombres, {2: "A 1", 1: "A 2", 0: "A 3"})

    def test_varios_municipios_y_comarca(self):
        ds = [distrito(0, ["A", "B"], 0, 0), distrito(1, ["C", "D"], 1, 1)]
        pob = {"A": 5, "B": 9, "C": 1, "D": 2}
        comarca = {"C": "Alto", "D": "Alto", "A": "X", "B": "Y"}
        filas, _ = g.nombrar("t", ds, pob, {}, comarca)
        self.assertEqual([f["nombre_distrito"] for f in filas], ["B y entorno", "Alto"])

    def test_colision_numerada_y_unica(self):
        ds = [distrito(0, ["A", "B"], 0, 0), distrito(1, ["A", "C"], 0, 5)]
        filas, _ = g.nombrar("t", ds, {"A": 9, "B": 1, "C": 1}, {}, {})
        nombres = [f["nombre_distrito"] for f in filas]
        self.assertEqual(len(set(nombres)), 2)
        self.assertEqual(nombres, ["A y entorno 2", "A y entorno 1"])

    def test_comarca_partida(self):
        ds = [distrito(0, ["A"], 0, 0), distrito(1, ["B"], 0, 0), distrito(2, ["C"], 0, 0)]
        _, en = g.nombrar("t", ds, {"A": 1, "B": 1, "C": 1}, {}, {})
        m = g.comarcas_partidas(ds, {"A": "K1", "B": "K1", "C": "K2"}, {}, en)
        self.assertEqual((m["comarcas_tocadas"], m["comarcas_partidas"]), (2, 1))
        self.assertEqual(list(m["detalle_partidas"]), ["K1"])

    def test_determinista(self):
        ds = lambda: [distrito(0, ["A"], 5, 10), distrito(1, ["A"], 9, 30)]  # noqa: E731
        self.assertEqual(g.nombrar("t", ds(), {"A": 1}, {}, {})[0], g.nombrar("t", ds(), {"A": 1}, {}, {})[0])

    def test_m06_con_campo_partidista_se_rechaza(self):
        feat = {"properties": {"district_id": "0", "district_pop": "1", "municipality_codes": "A",
                               "municipality_names": "A", "centroid_x": "0", "centroid_y": "0",
                               "province_codes": "22", "votos": "1"}}
        with tempfile.TemporaryDirectory() as d:
            r = Path(d) / "m.geojson"
            r.write_text(json.dumps({"features": [feat]}), encoding="utf-8")
            with self.assertRaises(ValueError):
                g.leer_m06(r)


class Datos49Provincias(unittest.TestCase):
    def test_csv_de_las_49_provincias(self):
        registro = json.loads((RAIZ / g.REGISTRO).read_text(encoding="utf-8"))
        territorios = {p["territory_id"] for p in registro["products"]
                       if p.get("kind") == "canonical_m06" and p["territory_id"].startswith("congreso_")}
        self.assertEqual(len(territorios), 49)
        esperados = {p["territory_id"]: p["expected_districts"] for p in registro["products"]
                     if p.get("kind") == "canonical_m06" and p["territory_id"] in territorios}
        for t in sorted(territorios):
            ruta = RAIZ / g.SALIDA / f"nombres_{t}.csv"
            self.assertTrue(ruta.exists(), t)
            self.assertTrue((RAIZ / g.SALIDA / f"informe_{t}.md").exists(), t)
            with ruta.open(encoding="utf-8", newline="") as f:
                filas = list(csv.DictReader(f))
            nombres = [r["nombre_distrito"] for r in filas]
            self.assertEqual(len(nombres), len(set(nombres)), t)
            self.assertEqual(len(filas), esperados[t], t)
            for n in nombres:
                self.assertNotIn("/", n, t)
                self.assertFalse(g.pendientes_toponimia("", n), (t, n))

    def test_toponimos_en_espanol(self):
        with (RAIZ / g.TOPONIMOS).open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                self.assertNotIn("/", r["nombre_es"])
        nombres = " ".join(
            r["nombre_distrito"] for p in (RAIZ / g.SALIDA).glob("nombres_*.csv")
            for r in csv.DictReader(p.open(encoding="utf-8", newline="")))
        for prohibido in ("Maó", "Eivissa", "Girona", "Lleida", "Ourense", "Gipuzkoa", "Bizkaia", "Ciutadella"):
            self.assertNotIn(prohibido, nombres)

    def test_regenerable_igual(self):
        with tempfile.TemporaryDirectory() as d:
            pob, nom = g.cargar_municipios(RAIZ / g.POBLACION)
            tabla = g.cargar_toponimos(RAIZ / g.TOPONIMOS)
            comarca, cub = g.cargar_comarcas(g.FUENTES_COMARCAS)
            m06 = RAIZ / "datos" / "distritos"  # los M06 viven como blobs; sin red, se salta si no hay caché
            cache = Path("/tmp/ddd_m06_t59/congreso_huesca.zip")
            if not cache.exists():
                self.skipTest("sin M06 en caché local (python herramientas/... --descargar)")
            g.procesar_territorio("congreso_huesca", cache, pob, nom, tabla, comarca, cub, d)
            a = (Path(d) / "nombres_congreso_huesca.csv").read_bytes()
            self.assertEqual(a, (m06 / "nombres_congreso_huesca.csv").read_bytes())


if __name__ == "__main__":
    unittest.main()
