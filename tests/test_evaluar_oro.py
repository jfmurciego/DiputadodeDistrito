"""Tests del conjunto de oro y su evaluador (T-38). Solo biblioteca estándar; sin red."""
import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))

import evaluar_oro as eo  # noqa: E402


class ConjuntoDeOro(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.casos = eo.cargar_casos()
        cls.por_id = {c["id"]: c for c in cls.casos}

    def test_casos_validos_y_suficientes(self):
        self.assertEqual(eo.validar(self.casos), [])
        self.assertGreaterEqual(len(self.casos), 30)

    def test_cobertura_minima(self):
        ids = set(self.por_id)
        self.assertTrue({f"CR-{i:02d}" for i in range(1, 13)} <= ids, "faltan causas del §9")
        self.assertTrue({f"ADV-{i:02d}" for i in range(1, 17)} <= ids, "faltan ADV-01 a ADV-16")
        self.assertTrue({"CAL-01", "CAL-02"} <= ids, "faltan casos de calibración §29E")
        limpios = [c for c in self.casos if c["tipo"] == "revision" and c["esperado"]["veredicto"] == "APROBAR"]
        self.assertGreaterEqual(len(limpios), 3, "hacen falta controles limpios para T-39")

    def test_salida_esperada_da_100(self):
        ideales = {"salidas": [eo.salida_ideal(c) for c in self.casos]}
        inf = eo.evaluar(self.casos, ideales)
        fallos = [r for r in inf["resultados"] if not r["acierto"]]
        self.assertEqual(fallos, [])
        self.assertEqual(inf["porcentaje"], 100.0)

    def test_salida_vacia_da_0(self):
        for vacia in ({}, [], {"salidas": []}, [{"caso": c["id"]} for c in self.casos]):
            inf = eo.evaluar(self.casos, vacia)
            self.assertEqual(inf["aciertos"], 0)

    def test_revisor_sha_distinto_falla(self):
        c = self.por_id["ADV-11"]
        s = eo.salida_ideal(c)
        s["sha"] = "0" * 40
        self.assertEqual(eo.puntuar_caso(c, s)["motivo"], "sha_distinto")
        s["sha"] = c["entrada"]["sha_candidato"][:10]
        self.assertTrue(eo.puntuar_caso(c, s)["acierto"])

    def test_revisor_veredicto_correcto_sin_defecto_no_basta(self):
        c = self.por_id["ADV-03"]
        s = {"caso": c["id"], "sha": c["entrada"]["sha_candidato"], "veredicto": "BLOQUEAR",
             "defectos": [{"clase": "gobernanza_version", "fichero": "otro.py", "detalle": "baja la VERSIÓN"}]}
        self.assertEqual(eo.puntuar_caso(c, s)["motivo"], "defecto_no_cazado")
        s["defectos"].append({"clase": "otra", "fichero": c["esperado"]["ficheros"][0],
                              "detalle": "Vuelve a EPSG:3035; el autonómico usa 25830"})
        self.assertTrue(eo.puntuar_caso(c, s)["acierto"])

    def test_control_limpio_bloqueado_falla(self):
        c = self.por_id["CTRL-01"]
        s = eo.salida_ideal(c)
        s["veredicto"] = "BLOQUEAR"
        self.assertFalse(eo.puntuar_caso(c, s)["acierto"])

    def test_forense_mas_de_cinco_lineas_falla(self):
        c = self.por_id["CR-02"]
        s = eo.salida_ideal(c)
        s["lineas"] = [f"línea {i}" for i in range(6)]
        self.assertTrue(eo.puntuar_caso(c, s)["motivo"].startswith("excede_lineas"))

    def test_forense_por_claves_sin_tildes(self):
        c = self.por_id["CR-08"]
        s = {"caso": c["id"], "diagnostico": "Mide la frontera en GRADOS (EPSG:4326);\nreproyectar a metros."}
        self.assertTrue(eo.puntuar_caso(c, s)["acierto"])
        s = {"caso": c["id"], "diagnostico": "Fallo de red al descargar."}
        self.assertFalse(eo.puntuar_caso(c, s)["acierto"])

    def test_calibracion_prohibido_y_acciones(self):
        c = self.por_id["CAL-02"]
        s = eo.salida_ideal(c)
        s["veredicto"] = "PASS_WITH_EXCEPTIONS"
        self.assertTrue(eo.puntuar_caso(c, s)["motivo"].startswith("veredicto_prohibido"))
        c3 = self.por_id["CAL-03"]
        s3 = eo.salida_ideal(c3)
        s3["acciones"] = ["relanzar 00"]
        self.assertTrue(eo.puntuar_caso(c3, s3)["motivo"].startswith("acciones_no_permitidas"))

    def test_validador_rechaza_caso_sin_fuente(self):
        c = copy.deepcopy(self.por_id["CR-01"])
        c["origen"]["prs"], c["origen"]["runs"] = [], []
        self.assertTrue(any("sin fuente" in e for e in eo.validar_caso(c)))

    def test_libro_de_costes_y_umbral(self):
        sel = eo.seleccionar(self.casos, agente="forense")
        self.assertTrue(all(c["agente"] in ("forense", "cualquiera") for c in sel))
        salidas = [dict(eo.salida_ideal(c), tokens=100, intento=1) for c in sel]
        salidas[0]["intento"] = 2
        inf = eo.evaluar(sel, salidas)
        self.assertEqual(inf["tokens"], 100 * len(sel))
        self.assertEqual(inf["a_la_primera"], len(sel) - 1)
        with tempfile.TemporaryDirectory() as d:
            libro = Path(d) / "LIBRO.md"
            libro.write_text("# Libro\n", encoding="utf-8")
            eo.anotar_libro(inf, "forense", "sonnet", "prueba", libro, fecha="2026-11-07")
            fila = eo.anotar_libro(inf, "forense", "sonnet", "prueba", libro, fecha="2026-11-07")
            texto = libro.read_text(encoding="utf-8")
            self.assertEqual(texto.count(eo.CABECERA_TABLA), 1)
            self.assertEqual(texto.count(fila), 2)
            out = Path(d) / "vacia.json"
            out.write_text("[]", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(eo.main(["--salidas", str(out), "--agente", "revisor", "--umbral", "0.8"]), 1)
            out.write_text(json.dumps([eo.salida_ideal(c) for c in self.casos]), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(eo.main(["--salidas", str(out), "--umbral", "1.0"]), 0)

    def test_libro_real_tiene_cabecera(self):
        self.assertIn(eo.CABECERA_TABLA, eo.LIBRO.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
