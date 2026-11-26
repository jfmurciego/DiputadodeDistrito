"""T-461: capitales de partido judicial desde las leyes autonómicas de capitalidad (BOE)."""
import csv
import hashlib
import unittest
from pathlib import Path

from herramientas import generar_capitales_partidos_judiciales as g

RAIZ = Path(__file__).resolve().parents[1]


def filas():
    with g.SALIDA.open(encoding="utf-8", newline="") as f:
        return {r["id_partido"]: r for r in csv.DictReader(l for l in f if not l.startswith("#"))}


class Capitales(unittest.TestCase):
    def test_valores_literales_de_las_leyes(self):
        # Esperados copiados de cada ley (texto del BOE), no recalculados por el código.
        esperado = {
            "28-11": "Madrid", "28-01": "Torrelaguna", "28-12": "Majadahonda",     # Ley 11/1989 Madrid
            "30-06": "Murcia", "30-08": "Molina de segura", "30-11": "San Javier",  # Ley 5/1989 Murcia
            "46-02": "Gandía", "03-01": "Denia", "12-01": "Castelló de la Plana",   # Ley 9/1989 C. Valenciana
            "01-02": "Vitoria-Gasteiz", "48-04": "Bilbao", "20-05": "Donostia-San Sebastián",  # Ley 1/1990 País Vasco
            "31-04": "Pamplona", "31-01": "Estella",                                # Ley Foral 4/1989
            "26-01": "Haro", "26-02": "Calahorra",                                  # Ley 6/1989 La Rioja
            "33-04": "Avilés", "33-02": "Pola de Lena",                             # Ley 1/1989 Asturias
            "11-01": "Chiclana de la Frontera", "41-06": "Sevilla",                 # Ley 3/1989 Andalucía
            "06-04": "Mérida", "10-04": "Plasencia",                                # Ley 3/1989 Extremadura
            "05-03": "Ávila", "47-01": "Valladolid",                                # Ley 3/1989 Castilla y León
            "16-01": "Cuenca", "39-03": "Santander",                                # CLM; Ley 8/1992 Cantabria
        }
        datos = filas()
        for pid, cap in esperado.items():
            self.assertEqual(datos[pid]["capital_ley"], cap, pid)

    def test_capital_dentro_de_su_partido_y_sin_repetir_municipio(self):
        por_partido, partido_de = g.cargar_partidos()
        codigos = set()
        for pid, r in filas().items():
            self.assertNotIn(r["codigo_ine"], codigos, pid)
            codigos.add(r["codigo_ine"])
            if not r["nueva_creacion"]:
                self.assertIn((r["provincia"], int(r["partido_judicial"])), [partido_de[r["codigo_ine"]]], pid)

    def test_cobertura_doce_comunidades_y_ninguna_otra(self):
        provincias = {r["provincia"] for r in filas().values()}
        faltan = {"07", "08", "15", "17", "22", "25", "27", "32", "35", "36", "38", "43", "44", "50", "51", "52"}
        self.assertFalse(provincias & faltan)  # Aragón, Baleares, Canarias, Cataluña, Galicia, Ceuta, Melilla: sin ley en el BOE
        por_partido, _ = g.cargar_partidos()
        for k in por_partido:
            if k[0] in provincias:
                self.assertIn(f"{k[0]}-{k[1]:02d}", filas(), k)  # ningún partido de las provincias cubiertas sin capital

    def test_castro_urdiales_partido_nuevo(self):
        r = filas()["39-08"]
        self.assertEqual((r["nombre_ine"], r["codigo_ine"]), ("Castro-Urdiales", "39020"))
        self.assertTrue(r["nueva_creacion"])

    def test_huella_de_las_fuentes(self):
        for r in filas().values():
            h = hashlib.sha256((g.FUENTES / f"{r['boe']}.xml").read_bytes()).hexdigest()
            self.assertEqual(h, r["sha256_boe"], r["boe"])

    def test_regenerable_igual(self):
        generadas, problemas, _ = g.generar()
        self.assertEqual(problemas, [])
        self.assertEqual({f["id_partido"]: f["codigo_ine"] for f in generadas},
                         {k: v["codigo_ine"] for k, v in filas().items()})


class NombresDeDistrito(unittest.TestCase):
    def test_ficheros_por_distrito_con_regla_de_capital(self):
        # Ejemplos con valor esperado literal: Albacete 2 (capital de partido con 40 municipios), Cuenca, Madrid 1…N.
        def leer(t):
            with (RAIZ / "datos/distritos" / f"nombres_{t}.csv").open(encoding="utf-8", newline="") as f:
                return list(csv.DictReader(f))
        self.assertEqual(sorted(r["nombre_distrito"] for r in leer("congreso_cuenca")), ["Cuenca", "Tarancón"])
        self.assertEqual({r["nombre_distrito"] for r in leer("congreso_albacete")} & {"Albacete 1", "Albacete 2"}, {"Albacete 1", "Albacete 2"})
        madrid = [r["nombre_distrito"] for r in leer("congreso_madrid") if r["nombre_distrito"].startswith("Madrid ")]
        self.assertEqual(sorted(int(n.split()[1]) for n in madrid), list(range(1, len(madrid) + 1)))
        self.assertTrue(all(r["estado_capital"] == "COMPLETO" for r in leer("congreso_madrid")))
        self.assertTrue(all(r["estado_capital"] == "SIN_CAPITAL" for r in leer("congreso_barcelona")))  # Barcelona: sin ley en el BOE
        self.assertIn("Vitoria", " ".join(r["nombre_distrito"] for r in leer("congreso_alava")))


if __name__ == "__main__":
    unittest.main()
