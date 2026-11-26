"""T-421: bloques y alias  de las autonómicas vigentes (interfaz pública, valores literales de la fuente)."""
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
        self.assertEqual(self.fila("aut01", "PP")["bloque_propuesto"], "Derecha nacional")
        self.assertEqual(self.fila("aut01", "PSOE")["bloque_propuesto"], "Izquierdas")
        self.assertEqual(self.fila("aut09", "CUP")["bloque_propuesto"], "Nacionalistas")

    def test_lista_cerrada_del_propietario(self):
        for aut, sigla, bloque in (("aut09", "ALIANÇA.CAT", "Nacionalistas"), ("aut09", "ALHORA", "Nacionalistas"), ("aut05", "UXGC", "Nacionalistas"),
                                   ("aut01", "ANDALUCISTAS", "Nacionalistas"), ("aut01", "SALF", "Derecha nacional"), ("aut07", "SALF", "Derecha nacional"),
                                   ("aut05", "DVC", "Izquierdas"), ("aut09", "JUNTS+", "Nacionalistas")):
            self.assertEqual(self.fila(aut, sigla)["bloque_propuesto"], bloque, (aut, sigla))
        self.assertEqual(self.top, [])  # sin dudosos: el resto de menores, sin bloque
        self.assertEqual(self.fila("aut09", "F.N.C.")["bloque_propuesto"], "")

    def test_alias_por_comunidad(self):
        a = ROOT / ba.SAL_ALIAS
        self.assertEqual(dv.cargar_alias(a, "2026-05", "aut01")["PSOE-A"], "PSOE")
        self.assertEqual(dv.cargar_alias(a, "2023-05", "aut15")["PSN-PSOE"], "PSOE")

    def test_sin_comunidad_el_alias_general_no_cambia(self):
        a = ROOT / "configuracion/alias_partidos_generales.csv"
        self.assertEqual(dv.cargar_alias(a, "2023-07"), dv.cargar_alias(a, "2023-07", None))

    def test_extremo_a_extremo_sin_votos_sin_casar(self):
        """generar con --alias --comunidad sobre votos reales: todo partido con alias casa con la tabla (PSOE-A, EB-AZ…)."""
        for aut, com, ele, ide, literal in (("aut01", "andalucia", "2026-05", "PSOE-A", 946267), ("aut16", "pais_vasco", "2024-04", "EB-AZ", 3072)):
            with tempfile.TemporaryDirectory() as t:
                src = ROOT / ba.HIST / com / ele.replace("-", "") / f"{com}_partidos.csv"
                p31 = Path(t) / "p31.csv"
                with src.open(encoding="utf-8", newline="") as fi, p31.open("w", encoding="utf-8", newline="") as fo:
                    w = csv.writer(fo)
                    w.writerow(["district_id", "party", "votes"])
                    rows = list(csv.DictReader(fi))
                    w.writerows([r["distrito"], r["partido"], r["votos"]] for r in rows)
                self.assertEqual(sum(int(r["votos"]) for r in rows if r["partido"] == ide), literal)
                dv.generar(p31, ROOT / ba.SAL_BLOQUES, ele, Path(t) / "o.csv", Path(t) / "m.json", None, ROOT / ba.SAL_ALIAS, aut)
                import json
                self.assertEqual(json.loads((Path(t) / "m.json").read_text())["sin_casar"]["votos"], 0)

    def test_alias_por_comunidad_exige_comunidad(self):
        with self.assertRaises(ValueError):
            dv.cargar_alias(ROOT / ba.SAL_ALIAS, "2026-05")

    def test_comunidad_sin_alias_falla(self):
        with self.assertRaises(ValueError):
            dv.generar("x", ROOT / ba.SAL_BLOQUES, "2026-05", "y", comunidad="aut01")

    def test_la_tabla_escrita_coincide(self):
        with (ROOT / ba.SAL_BLOQUES).open(encoding="utf-8", newline="") as fh:
            self.assertEqual(len(list(csv.DictReader(fh))), len(self.bloques))


if __name__ == "__main__":
    unittest.main()
