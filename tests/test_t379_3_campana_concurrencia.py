"""T-379 PR 3 (diseño T-378 §3, §16.1, D-147): segunda campaña rechazada y hechos de campaña de la comprobación previa.

Listas sintéticas de ejecuciones (nunca la API real). Cada regla con su control negativo.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import campana_estado as ce  # noqa: E402

CLI = [sys.executable, str(ROOT / "herramientas" / "campana_estado.py")]


def run(i, status="in_progress", event="workflow_dispatch"):
    return {"id": i, "status": status, "event": event}


class SegundaCampana(unittest.TestCase):
    def test_sola_sigue(self):
        self.assertEqual(ce.segunda_campana([run(500)], 500)[0], 0)
        self.assertEqual(ce.segunda_campana([], 500)[0], 0)

    def test_otra_en_curso_rechaza_con_su_run(self):
        rc, msg = ce.segunda_campana([run(400), run(500)], 500)
        self.assertEqual(rc, ce.RC_NO_LANZABLE)
        self.assertIn("CAMPANA_EN_CURSO", msg)
        self.assertIn("400", msg)

    def test_dos_simultaneas_sigue_la_menor(self):
        runs = [run(400, "queued"), run(500, "queued")]
        self.assertEqual(ce.segunda_campana(runs, 400)[0], 0)
        self.assertEqual(ce.segunda_campana(runs, 500)[0], ce.RC_NO_LANZABLE)

    def test_solo_comprobar_y_waiting_bloquean(self):
        # §16.1: un «solo comprobar» en curso cuenta; una en `waiting` bloquea y el aviso da el run que bloquea.
        for estado in ("in_progress", "queued", "waiting", "requested", "pending"):
            rc, msg = ce.segunda_campana([run(400, estado), run(500)], 500)
            self.assertEqual(rc, ce.RC_NO_LANZABLE, estado)
            self.assertIn("400", msg)

    def test_terminadas_y_pull_request_no_cuentan(self):
        self.assertEqual(ce.segunda_campana([run(400, "completed"), run(500)], 500)[0], 0)
        self.assertEqual(ce.segunda_campana([run(400, event="pull_request"), run(500)], 500)[0], 0)
        # control negativo: el mismo run 400 en curso y por botón sí bloquea
        self.assertEqual(ce.segunda_campana([run(400), run(500)], 500)[0], ce.RC_NO_LANZABLE)

    def test_entrada_invalida_falla_cerrado(self):
        with self.assertRaises(ce.EstadoError):
            ce.segunda_campana([{"status": "in_progress"}], 500)

    def test_cli(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "runs.json"
            p.write_text(json.dumps({"workflow_runs": [run(400), run(500)]}), encoding="utf-8")
            r = subprocess.run(CLI + ["concurrencia", "--runs", str(p), "--run-id", "500"], capture_output=True, text=True)
            self.assertEqual(r.returncode, ce.RC_NO_LANZABLE, r.stderr)
            r = subprocess.run(CLI + ["concurrencia", "--runs", str(p), "--run-id", "400"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)


SHA = "a" * 40


def p90(sha, conclusion, status="completed", event="push"):
    return {"head_sha": sha, "status": status, "conclusion": conclusion, "event": event}


class HechosCampana(unittest.TestCase):
    def test_ci_de_la_version(self):
        self.assertIs(ce.hechos_campana([p90(SHA, "success")], SHA, True)["campana"]["ci_verde"], True)
        self.assertIs(ce.hechos_campana([p90(SHA, "failure")], SHA, True)["campana"]["ci_verde"], False)
        # otra versión en verde no acredita la nuestra (sin evidencia → None, aviso; nunca bloquea)
        self.assertIsNone(ce.hechos_campana([p90("b" * 40, "success")], SHA, True)["campana"]["ci_verde"])
        self.assertIsNone(ce.hechos_campana([p90(SHA, None, "in_progress")], SHA, True)["campana"]["ci_verde"])

    def test_ci_cancelada_no_es_verde_ni_roja(self):
        self.assertIsNone(ce.hechos_campana([p90(SHA, "cancelled")], SHA, True)["campana"]["ci_verde"])

    def test_un_verde_basta_si_no_hay_rojo(self):
        h = ce.hechos_campana([p90(SHA, "cancelled"), p90(SHA, "success")], SHA, True)
        self.assertIs(h["campana"]["ci_verde"], True)
        h = ce.hechos_campana([p90(SHA, "failure"), p90(SHA, "success")], SHA, True)
        self.assertIs(h["campana"]["ci_verde"], False)  # un rojo de la batería sobre esa versión bloquea

    def test_r2_y_gasto(self):
        met = {"minutos_actions": {"gasto_semanal": {"por_semana": [{"semana": "2026-W46", "minutos": 812.5}]}}}
        h = ce.hechos_campana([], SHA, False, met)["campana"]
        self.assertIs(h["r2_responde"], False)
        self.assertEqual(h["gasto_semanal_min"], 812.5)
        self.assertIsNone(ce.hechos_campana([], SHA, None, {})["campana"]["gasto_semanal_min"])

    def test_alimenta_la_comprobacion(self):
        h = ce.hechos_campana([p90(SHA, "failure")], SHA, True)
        s = ce.comprobar("nac22", "vigente", h)
        self.assertFalse(s["lanzable"])
        self.assertIn("CI_NO_VERDE", s["bloqueos"])
        s = ce.comprobar("nac22", "vigente", ce.hechos_campana([p90(SHA, "success")], SHA, True))
        self.assertTrue(s["lanzable"])

    def test_sha_invalido(self):
        with self.assertRaises(ce.EstadoError):
            ce.hechos_campana([], "main", True)


if __name__ == "__main__":
    unittest.main()


class CerrarPaso(unittest.TestCase):
    """§4: un paso de la cadena se cierra desde los resultados de sus jobs; nada cuenta como verde sin success."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.alm = ce.AlmacenLocal(Path(self._td.name))
        ce.guardar_semaforo(self.alm, "900", ce.comprobar("nac22, nac42, nac52, aut11", "vigente"))

    def tearDown(self):
        self._td.cleanup()

    def cerrar(self, resultados, obligatorios, t="nac22", paso="P10", intento=1, huellas=None):
        ce.empezar(self.alm, "900", t, paso, intento)
        return ce.cerrar_paso(self.alm, "900", t, paso, intento, resultados, obligatorios, huellas)

    def ultimo(self, t, paso):
        return ce.recuento(self.alm, "900", final=True)["territorios"][t]

    def test_todo_success_es_ok_con_huellas(self):
        r = self.cerrar({"p11": "success", "puerta_01": "success", "p12": "success"}, ["p11", "puerta_01", "p12"],
                        huellas={"paquete": "b" * 64})
        self.assertTrue(r["sano"])
        clave = ce.clave_paso("900", "nac22", "P10", 1)
        self.assertEqual(json.loads(self.alm.leer(clave))["huellas"], {"paquete": "b" * 64})

    def test_job_en_rojo_es_fallo_no_controlado(self):
        r = self.cerrar({"p11": "success", "puerta_01": "failure", "p12": "skipped"}, ["p11", "puerta_01", "p12"])
        self.assertFalse(r["sano"])
        self.assertEqual(r["causa"], "FALLO_NO_CONTROLADO")
        self.assertEqual(r["rojos"], ["puerta_01"])
        self.assertEqual(self.ultimo("nac22", "P10")["causa"], "FALLO_NO_CONTROLADO")

    def test_obligatorio_saltado_no_es_verde(self):
        r = self.cerrar({"p11": "success", "puerta_01": "skipped"}, ["p11", "puerta_01"])
        self.assertEqual((r["sano"], r["causa"]), (False, "PASO_INCOMPLETO"))
        # control negativo: un opcional saltado (acreditar no planificado) no aparta
        r = self.cerrar({"acreditar": "skipped", "p20": "success", "puerta_02": "success"}, ["p20", "puerta_02"],
                        t="nac42", paso="P20")
        self.assertTrue(r["sano"])

    def test_fallo_no_controlado_no_se_reejecuta(self):
        self.cerrar({"p11": "failure"}, ["p11"])
        rc, _ = ce.empezar(self.alm, "900", "nac22", "P10", 2)
        self.assertEqual(rc, ce.RC_NO_REEJECUTABLE)

    def test_entrada_invalida(self):
        with self.assertRaises(ce.EstadoError):
            self.cerrar({"p11": "neutral"}, ["p11"])
        with self.assertRaises(ce.EstadoError):
            self.cerrar({"p11": "success"}, ["p11", "puerta_01"], t="nac42")

    def test_cli_imprime_sano(self):
        base = ["--almacen", f"dir:{self._td.name}", "--campana", "900", "--territorio", "aut11", "--paso", "P30",
                "--intento", "1"]
        r = subprocess.run(CLI + ["empezar"] + base, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = subprocess.run(CLI + ["cerrar-paso"] + base + ["--resultados", '{"p30": "success"}', "--obligatorio", "p30",
                                                         "--huellas", '{"m08": ""}'], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIs(json.loads(r.stdout)["sano"], True)
