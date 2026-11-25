"""T-460 (propietario 25-11): «Patriotas» pasa a «Derecha nacional»; ningún partido cambia de bloque.

El valor esperado sale de las tablas aprobadas (2026-11-17 y 2026-11-19), que no se tocan: misma asignación con el nombre nuevo."""
import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import bloques_autonomicas as ba  # noqa: E402
import doble_vuelta as dv  # noqa: E402
import p75_doble_vuelta_r2 as p75  # noqa: E402

CONF = ROOT / "configuracion"
PAREJAS = (("bloques_partidos_2026-11-17.csv", "bloques_partidos_2026-11-25.csv"),
           ("bloques_partidos_autonomicas_2026-11-19.csv", "bloques_partidos_autonomicas_2026-11-25.csv"))


def filas(nombre):
    with (CONF / nombre).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


class DerechaNacional(unittest.TestCase):
    def test_misma_asignacion_con_el_nombre_nuevo(self):
        for viejo, nuevo in PAREJAS:
            v, n = filas(viejo), filas(nuevo)
            self.assertEqual(len(v), len(n))
            for a, b in zip(v, n):
                clave = lambda r: {k: r[k] for k in r if k not in ("bloque_propuesto", "motivo")}
                self.assertEqual(clave(a), clave(b))
                esperado = "Derecha nacional" if a["bloque_propuesto"] == "Patriotas" else a["bloque_propuesto"]
                self.assertEqual(b["bloque_propuesto"], esperado, (nuevo, a["siglas"]))

    def test_sin_patriotas_en_las_tablas_nuevas(self):
        for _, nuevo in PAREJAS:
            self.assertTrue(all(r["bloque_propuesto"] != "Patriotas" for r in filas(nuevo)))
            self.assertIn("Derecha nacional", {r["bloque_propuesto"] for r in filas(nuevo)})

    def test_bloques_del_motor(self):
        self.assertEqual(dv.BLOQUES, ("Izquierdas", "Nacionalistas", "Derecha nacional"))
        self.assertEqual(dv.ESCENARIOS["dv_B"], frozenset({"Izquierdas", "Derecha nacional"}))
        self.assertEqual(ba.PAT, "Derecha nacional")

    def test_tabla_nacional_vigente_no_es_la_autonomica(self):
        self.assertEqual(p75.bloques_vigente(ROOT).name, "bloques_partidos_2026-11-25.csv")

    def test_el_generador_reproduce_la_tabla_autonomica_nueva(self):
        bloques, *_ = ba.construir()
        nuevo = {(r["comunidad"], r["siglas"]): r["bloque_propuesto"] for r in filas(PAREJAS[1][1])}
        self.assertEqual({(f["comunidad"], f["siglas"]): f["bloque_propuesto"] for f in bloques}, nuevo)


if __name__ == "__main__":
    unittest.main()
