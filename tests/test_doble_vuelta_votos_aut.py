"""T-426: votos por distrito de las autonómicas vigentes (aut03 por municipio, aut14 por sección) en el formato de T-427."""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import doble_vuelta_votos_aut as d  # noqa: E402

DV = ROOT / "datos/resultados/doble_vuelta_autonomicas"


class MayorResto(unittest.TestCase):
    def test_suma_exacta(self):
        self.assertEqual(d.mayor_resto({"a": 25.25, "b": 75.75}), {"a": 25, "b": 76})
        self.assertEqual(sum(d.mayor_resto({"a": 1 / 3, "b": 1 / 3, "c": 1 / 3}).values()), 1)


class Cuadre(unittest.TestCase):
    def _comp(self, raiz: Path):
        (raiz / "datos/composicion/runs").mkdir(parents=True)
        (raiz / "datos/composicion/runs/autXX_1.csv").write_text(
            "seccion,distrito,poblacion\n3300101001,0,100\n3300101002,1,300\n", encoding="utf-8")

    def test_municipio_se_reparte_sin_perder_votos(self):
        with tempfile.TemporaryDirectory() as t:
            raiz = Path(t)
            self._comp(raiz)
            ent = raiz / "m.csv"
            ent.write_text("municipio,partido,votos\n33001,PP,101\n", encoding="utf-8")
            m = d.construir("autXX", "202305", "1", ent, "municipio", raiz / "o", raiz=raiz)
            self.assertTrue(m["aproximado_en_distrito"])
            filas = {r["distrito"]: int(r["votos"]) for r in csv.DictReader((raiz / "o/autXX_partidos.csv").open())}
            self.assertEqual(sum(filas.values()), 101)
            self.assertEqual(filas, {"0": 25, "1": 76})  # 101·100/400 = 25,25 → 25; 101·300/400 = 75,75 → 76

    def test_municipio_fuera_de_la_composicion_falla(self):
        with tempfile.TemporaryDirectory() as t:
            raiz = Path(t)
            self._comp(raiz)
            ent = raiz / "m.csv"
            ent.write_text("municipio,partido,votos\n33999,PP,10\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                d.construir("autXX", "202305", "1", ent, "municipio", raiz / "o", raiz=raiz)

    def test_seccion_fuera_de_la_composicion_falla(self):
        with tempfile.TemporaryDirectory() as t:
            raiz = Path(t)
            self._comp(raiz)
            ent = raiz / "s.csv"
            ent.write_text("section_id,party,votes\n9999999999,PP,10\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                d.construir("autXX", "202305", "1", ent, "seccion", raiz / "o", raiz=raiz)


class DatosGenerados(unittest.TestCase):
    def test_totales_aut14_y_aut03(self):
        # entrada independiente: sumas de las fuentes oficiales (CREM: 7 candidaturas de las secciones; SADEI: concejos)
        for aut, esperado in (("aut14", 659281), ("aut03", 520466)):
            with (DV / aut / "202305" / f"{aut}_partidos.csv").open(encoding="utf-8") as f:
                self.assertEqual(sum(int(r["votos"]) for r in csv.DictReader(f)), esperado)


if __name__ == "__main__":
    unittest.main()


class FueraDeDistritos(unittest.TestCase):
    """El MANIFEST declara lo que queda fuera de los distritos; con ello se llega al total oficial (valores de la fuente)."""

    def _m(self, aut):
        import json
        return json.loads((DV / aut / "202305" / "MANIFEST.json").read_text(encoding="utf-8"))["cuadre"]

    def test_aut14_total_oficial_676554(self):
        c = self._m("aut14")
        f = c["fuera_de_distritos"]
        self.assertEqual(c["votos_salida"] + f["otros_votos"] + f["cera_votos_a_candidaturas_excluidos"], 676554)  # fila «Región de Murcia» del CREM

    def test_aut03_ausentes_declarados_y_total_oficial(self):
        c = self._m("aut03")
        aus = c["fuera_de_distritos"]["votos_ausentes_no_repartidos"]
        self.assertEqual(c["votos_salida"] + sum(aus.values()), 527500)  # fila ASTURIES de SADEI: votos a candidaturas
        self.assertEqual(aus["PSOE"], 2431)
