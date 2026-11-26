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
import doble_vuelta_cobertura as cob  # noqa: E402
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

    def test_tabla_vieja_con_patriotas_falla_en_voz_alta(self):
        with self.assertRaisesRegex(ValueError, "Bloque desconocido «Patriotas»"):
            dv.cargar_tabla(CONF / PAREJAS[0][0], "2023-07")

    def test_cobertura_tambien_rechaza_la_tabla_vieja(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            votos = Path(d) / "votos.csv"
            votos.write_text("district_id,party,votes\nD1,PSOE,30\nD1,PP,20\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Bloque desconocido «Patriotas»"):
                cob.cobertura(votos, CONF / PAREJAS[0][0], "2023-07")
            self.assertEqual(cob.cobertura(votos, CONF / PAREJAS[0][1], "2023-07")["eleccion"], "2023-07")

    def test_tabla_nacional_vigente_no_es_la_autonomica(self):
        self.assertEqual(p75.bloques_vigente(ROOT).name, "bloques_partidos_2026-11-25.csv")

    def test_el_generador_reproduce_la_tabla_autonomica_nueva(self):
        bloques, *_ = ba.construir()
        nuevo = {(r["comunidad"], r["siglas"]): r["bloque_propuesto"] for r in filas(PAREJAS[1][1])}
        self.assertEqual({(f["comunidad"], f["siglas"]): f["bloque_propuesto"] for f in bloques}, nuevo)


class AmbitoDeLaTabla(unittest.TestCase):
    """La tabla de bloques es explícita por ámbito: nacional (sin `comunidad`) y autonómica (con `comunidad`); no se cruzan."""

    def test_p75_nac_usa_la_nacional_y_p75_aut_la_autonomica(self):
        nac = p75.bloques_vigente(ROOT)
        self.assertNotIn("autonomicas", nac.name)
        self.assertNotIn("comunidad", filas(nac.name)[0])
        self.assertIn("autonomicas", p75.BLOQUES_AUT.name)
        self.assertIn("comunidad", filas(p75.BLOQUES_AUT.name)[0])
        self.assertTrue((ROOT / p75.BLOQUES_AUT).is_file())

    def test_ninguna_tabla_nueva_se_cruza_con_el_otro_ambito(self):
        # una tabla nacional no casa filas por comunidad y la autonómica no tiene filas 2023-07 (generales)
        with self.assertRaises(ValueError):
            dv.cargar_tabla(CONF / "bloques_partidos_autonomicas_2026-11-25.csv", "2023-07")
        with self.assertRaises(ValueError):
            dv.cargar_tabla(CONF / "bloques_partidos_2026-11-25.csv", "2023-07", comunidad="aut01")

    def test_p30_elige_la_nacional_por_nombre(self):
        wf = (ROOT / ".github/workflows/p30-resultados-electorales.yml").read_text(encoding="utf-8")
        self.assertIn("ls configuracion/bloques_partidos_2*.csv", wf)
        self.assertNotIn("ls configuracion/bloques_partidos_*.csv", wf)

    def test_la_vigente_nacional_cambia_con_una_fecha_nueva_pero_nunca_a_la_autonomica(self):
        import shutil, tempfile
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "configuracion").mkdir()
            for n in ("bloques_partidos_2026-11-25.csv", "bloques_partidos_autonomicas_2027-01-01.csv"):
                shutil.copy(CONF / n.replace("2027-01-01", "2026-11-25"), Path(d) / "configuracion" / n)
            self.assertEqual(p75.bloques_vigente(Path(d)).name, "bloques_partidos_2026-11-25.csv")


if __name__ == "__main__":
    unittest.main()
