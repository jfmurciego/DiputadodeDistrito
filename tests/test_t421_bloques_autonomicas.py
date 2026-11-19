"""T-421: bloques y alias PROPUESTOS de las autonómicas vigentes (interfaz pública, valores literales de la fuente)."""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import bloques_autonomicas as ba  # noqa: E402
import doble_vuelta as dv  # noqa: E402


class BloquesAutonomicas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bloques, cls.alias, cls.top, cls.todos, cls.cob = ba.construir()

    def fila(self, aut, sigla):
        return next(f for f in self.bloques if f["comunidad"] == aut and f["siglas"] == sigla)

    def test_votos_de_la_fuente(self):  # Andalucía 2026-05: total literal del CSV de la fuente = 4.120.892
        self.assertEqual(sum(f["votos"] for f in self.bloques if f["comunidad"] == "aut01"), 4120892)
        self.assertEqual(self.cob["aut01"]["total"], 4120892)

    def test_mismo_partido_mismo_bloque(self):
        self.assertEqual(self.fila("aut01", "PP")["bloque_propuesto"], "Patriotas")
        self.assertEqual(self.fila("aut01", "PSOE-A")["bloque_propuesto"], "Izquierdas")
        self.assertEqual(self.fila("aut09", "CUP - DT")["bloque_propuesto"], "Nacionalistas")

    def test_junts_nacionalistas_y_dudosos_acotados(self):
        self.assertEqual(self.fila("aut09", "JUNTS+")["bloque_propuesto"], "Nacionalistas")
        self.assertLessEqual(len(self.top), 15)
        self.assertEqual([t[0] for t in self.top], sorted((t[0] for t in self.top), reverse=True))

    def test_alias_por_comunidad(self):
        a = ROOT / ba.SAL_ALIAS
        self.assertEqual(dv.cargar_alias(a, "2026-05", "aut01")["PSOE-A"], "PSOE")
        self.assertEqual(dv.cargar_alias(a, "2023-05", "aut15").get("PSOE-A"), None)

    def test_sin_comunidad_el_alias_general_no_cambia(self):
        a = ROOT / "configuracion/alias_partidos_generales.csv"
        self.assertEqual(dv.cargar_alias(a, "2023-07"), dv.cargar_alias(a, "2023-07", None))

    def test_la_tabla_escrita_coincide(self):
        with (ROOT / ba.SAL_BLOQUES).open(encoding="utf-8", newline="") as fh:
            self.assertEqual(len(list(csv.DictReader(fh))), len(self.bloques))


if __name__ == "__main__":
    unittest.main()
