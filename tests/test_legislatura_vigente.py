"""T-86: legislatura vigente (71 territorios con fuente) y plan/lanzamiento del Gestor de Campañas.

VERSIÓN: 1.2.1 · FECHA: 2026-11-10
CAMBIOS 1.2.1: T-215, títulos simulados de la 05 y la 06 con los nombres v5; un run en curso con el título viejo de la 00 cuenta.
CAMBIOS 1.2.0: T-105, relevo con «@auto» para los iniciados, ensemble tras publicar y formulario 2.0 (D-22).
CAMBIOS 1.1.0: T-102, los 49 gemelos Congreso 350 van aparte (ámbito congreso_350); siguen 71 de la legislatura.
ANTERIOR: legacy/tests/test_legislatura_vigente_v1.2.0_20261110.py
"""
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import legislatura_vigente as lv  # noqa: E402

WF = ROOT / ".github/workflows/gestor-campanas.yml"


class Configuracion(unittest.TestCase):
    def setUp(self):
        self.cfg = lv.load_config(ROOT)

    def test_coincide_con_las_fuentes(self):
        self.assertEqual((ROOT / lv.CONFIG).read_text(encoding="utf-8"), lv.dump_config(lv.build_config(ROOT)))
        for path, sha in self.cfg["fuentes"].items():
            self.assertEqual(lv._sha(ROOT / path), sha, path)

    def test_71_territorios_52_nacionales_19_autonomicas(self):
        rows = [r for r in self.cfg["territorios"] if r["ambito"] != lv.VARIANT]
        self.assertEqual(len(rows), 71)
        self.assertEqual(self.cfg["totales"][lv.VARIANT], 49)
        self.assertEqual(len({r["territory_id"] for r in rows}), 71)
        self.assertEqual(sum(r["ambito"] == "nacional" for r in rows), 52)
        self.assertEqual(sorted(r["codigo"] for r in rows if r["ambito"] == "autonómica"),
                         [f"{i:02d}" for i in range(1, 20)])

    def test_fechas_y_claves_de_los_ficheros_con_fuente(self):
        registry = yaml.safe_load((ROOT / lv.REGISTRY).read_text(encoding="utf-8"))["territories"]
        prep = {t["territory_id"]: t for t in
                yaml.safe_load((ROOT / lv.PREPARATION).read_text(encoding="utf-8"))["territories"]}
        for r in self.cfg["territorios"]:
            self.assertEqual(r["fecha"], str(registry[r["territory_id"]]["election_date"]), r["territory_id"])
            self.assertEqual(r["fecha"], str(prep[r["territory_id"]]["election_date"]), r["territory_id"])
            self.assertTrue(r["clave"].endswith(r["fecha"].replace("-", "")))
            self.assertNotEqual(r["fuente_resultados"], "sin fuente", r["territory_id"])
        nac = [r for r in self.cfg["territorios"] if r["ambito"] == "nacional"]
        self.assertEqual({r["fecha"] for r in nac}, {"2023-07-23"})
        self.assertEqual(self.cfg["nacional"]["escanos_oficiales"]["boe"], "BOE-A-2023-18907")

    def test_selector_existe_en_el_00(self):
        wf = yaml.safe_load((ROOT / ".github/workflows/ejecucion-completa-proyecto.yml").read_text(encoding="utf-8"))
        options = set(wf.get(True, wf.get("on"))["workflow_dispatch"]["inputs"]["territory_id"]["options"])
        self.assertEqual([r["selector_00"] for r in self.cfg["territorios"] if r["selector_00"] not in options], [])


class Plan(unittest.TestCase):
    def setUp(self):
        self.cfg = lv.load_config(ROOT)

    def plan(self, ambito="legislatura completa", tokens=(), forzar=False, running=None):
        return lv.build_plan(self.cfg, ambito, list(tokens), forzar, running or {}, ROOT, date(2026, 11, 7))

    def test_ambitos(self):
        self.assertEqual(self.plan()["count"], 71)
        self.assertEqual(self.plan("nacional")["count"], 52)
        self.assertEqual(self.plan("autonómicas")["count"], 19)
        self.assertEqual([r["territory_id"] for r in self.plan("comunidad", ["Aragón"])["territorios"]], ["aragon"])
        self.assertEqual([r["territory_id"] for r in self.plan("comunidad", ["2"])["territorios"]], ["aragon"])
        self.assertEqual([r["territory_id"] for r in self.plan("provincias", ["HU", "50", "Teruel"])["territorios"]],
                         ["congreso_huesca", "congreso_teruel", "congreso_zaragoza"])
        with self.assertRaises(lv.GestorError):
            self.plan("provincias")
        with self.assertRaises(lv.GestorError):
            self.plan("comunidad", ["Aragón", "Cantabria"])
        with self.assertRaises(lv.GestorError):
            self.plan("provincias", ["Aragón"])

    def test_acciones(self):
        rows = {r["territory_id"]: r for r in self.plan()["territorios"]}
        self.assertEqual(set(r["accion"] for r in rows.values()) - {"nada", "publicar", "reutilizar",
                                                                      "desde_el_principio"}, set())
        for r in rows.values():
            self.assertEqual(r["accion"] == "nada", r["estado"] == "PUBLICADO", r["territory_id"])
        self.assertEqual(rows["congreso_huesca"]["accion"], "nada")  # M08 publicado
        forced = self.plan("provincias", ["HU"], forzar=True)["territorios"][0]
        self.assertEqual(forced["accion"], "desde_el_principio")
        busy = self.plan("provincias", ["HU"], forzar=True, running={"Congreso Huesca": "9"})["territorios"][0]
        self.assertEqual((busy["accion"], busy["run_id"]), ("esperar", "9"))

    def test_estado_desde_manifiestos(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "territorios/x/evidencia/ejecuciones_completas"
            d.mkdir(parents=True)
            today = date(2026, 11, 7)
            self.assertEqual(lv.territory_state(root, "x", {}, today)["estado"], "SIN_PRODUCTO")
            (d / "1.json").write_text(json.dumps({"workflow_run_id": 1, "status": "FAILED",
                                                  "territorial_status": "CERTIFIED"}))
            self.assertEqual(lv.territory_state(root, "x", {}, today)["estado"], "TERRITORIAL_CERTIFICADO")
            (d / "2.json").write_text(json.dumps({"workflow_run_id": 2, "status": "SUCCESS",
                                                  "electoral_status": "COMPLETE", "generated_at": "2026-11-01T00:00:00Z"}))
            self.assertEqual(lv.territory_state(root, "x", {}, today), {"estado": "COMPLETO_SIN_PUBLICAR", "run_id": "2"})
            self.assertEqual(lv.territory_state(root, "x", {}, date(2026, 12, 1))["estado"], "COMPLETO_CADUCADO")
            viewer = {"products": [{"territory_id": "x", "kind": "canonical_m08", "run_id": "2"}]}
            self.assertEqual(lv.territory_state(root, "x", viewer, today)["estado"], "PUBLICADO")

    def test_markdown(self):
        md = lv.plan_markdown(self.plan("provincias", ["HU"]))
        self.assertIn("| 1 | ES-NAC-22-20230723 | Congreso Huesca | PUBLICADO |", md)


class Lanzar(unittest.TestCase):
    """Simula GitHub: cada dispatch de 00 crea un run que termina en el siguiente sondeo."""

    def setUp(self):
        self.runs = {lv.WF_00: [], lv.WF_05: [], lv.WF_06: []}
        self.dispatched = []
        self.n = 100
        self.clock = 0.0

    def fake_dispatch(self, wf, inputs):
        self.dispatched.append((wf, dict(inputs)))
        if wf == lv.WF_GESTOR:
            return
        self.n += 1
        title = (f"{lv.TITLE_00} · {inputs['territory_id']} · {inputs['execution_mode']}" if wf == lv.WF_00
                 else "P50 Publicación" if wf == lv.WF_05 else "P30 Distritos · P33 Alternativas")
        self.runs[wf].append({"id": self.n, "display_title": title, "status": "queued", "conclusion": None,
                              "created_at": "2026-11-07T10:00:%02dZ" % (self.n % 60)})

    def fake_list(self, wf, since="", status=""):
        for r in self.runs[wf]:  # avanza un paso cada vez que se consulta
            if r["status"] == "queued":
                r["status"] = "in_progress"
            elif r["status"] == "in_progress":
                r["status"], r["conclusion"] = "completed", self.conclusion(r)
        return [dict(r) for r in self.runs[wf]]

    def conclusion(self, run):
        return "failure" if "Fallo" in run["display_title"] else "success"

    def campaign(self, rows, **kw):
        plan = {"territorios": rows}
        with mock.patch.object(lv, "dispatch", self.fake_dispatch), \
                mock.patch.object(lv, "list_runs", self.fake_list), \
                mock.patch.object(lv, "_now", lambda: "2026-11-07T09:00:00Z"), \
                mock.patch.object(lv.time, "sleep", lambda s: setattr(self, "clock", self.clock + s)), \
                mock.patch.object(lv.time, "time", lambda: self.clock):
            return lv.run_campaign(plan, "Canónico", kw.get("max_parallel", 2), kw.get("test_first", True),
                                   kw.get("deadline", 10 ** 9), {"estrategia": "Canónico"}, log=lambda *_: None)

    @staticmethod
    def row(name, accion="reutilizar", run_id=""):
        return {"territory_id": name.lower(), "selector_00": name, "accion": accion, "run_id": run_id}

    def test_running_00_acepta_titulo_viejo_y_p00(self):  # T-215
        runs = [{"id": 7, "display_title": "P00 Campaña · cantabria · Reutilizar"},
                {"id": 8, "display_title": "00 Ejecución Completa del Proyecto · ceuta · Reutilizar"},
                {"id": 9, "display_title": "P00 Campaña"}]
        with mock.patch.object(lv, "list_runs", side_effect=lambda wf, status="": runs if status == "queued" else []):
            self.assertEqual(lv.running_00(), {"cantabria": "7", "ceuta": "8"})

    def test_prueba_primero_y_salta_publicados(self):
        rows = [self.row("A"), self.row("B", "desde_el_principio"), self.row("C", "nada"), self.row("D", "publicar", "77")]
        report = self.campaign(rows)
        self.assertEqual([r["territory_id"] for r in report], ["a", "b", "d"])
        self.assertTrue(all(r["resultado"].startswith("OK") for r in report), report)
        first = self.dispatched[0]
        self.assertEqual((first[0], first[1]["territory_id"]), (lv.WF_00, "A"))
        self.assertTrue(first[1]["publish_result"] and first[1]["lanzado_por_eleccion"])
        self.assertEqual(first[1]["publication_mode"], "electoral")
        self.assertIn((lv.WF_05, {"pagina_publicar": "Sitio completo", "production_run_id": "77"}), self.dispatched)
        self.assertNotIn("C", [d[1].get("territory_id") for d in self.dispatched])

    def test_prueba_fallida_detiene_la_campana(self):
        report = self.campaign([self.row("Fallo"), self.row("B")])
        self.assertTrue(report[0]["resultado"].startswith("FALLO"))
        self.assertEqual(report[1]["resultado"], "NO_INICIADO")
        self.assertEqual(len(self.dispatched), 1)

    def test_hija_fallida_del_bot_no_hunde_la_00_propia(self):
        """T-130 (run 42637133308): la 00 de prueba pasa; su hija «Reutilizar» del bot falla y no cuenta sin publicar."""
        def hija(*_):
            self.runs[lv.WF_00].append({"id": 999, "display_title": f"{lv.TITLE_00} · A · Reutilizar progreso existente Fallo",
                                        "status": "queued", "conclusion": None, "created_at": "2026-11-07T10:05:00Z"})
        rows = [{**self.row("A"), "publicar": False}]
        orig = self.fake_dispatch
        def d(wf, inputs):
            orig(wf, inputs)
            if wf == lv.WF_00:
                hija()
        self.fake_dispatch = d
        report = self.campaign(rows, test_first=False)
        self.assertTrue(report[0]["resultado"].startswith("OK 00 101"), report)

    def test_relevo_al_limite(self):
        report = self.campaign([self.row("A"), self.row("B")], deadline=0)
        self.assertEqual(self.dispatched[-1][0], lv.WF_GESTOR)
        self.assertEqual(self.dispatched[-1][1]["modo"], "continuar")
        self.assertEqual(self.dispatched[-1][1]["territorios"], "a@auto,b")  # A (prueba) ya iniciada
        self.assertEqual(len(report), 2)


    def test_ensemble_tras_publicar_y_solo_ensemble_si_ya_publicado(self):
        rows = [{**self.row("A", "desde_el_principio"), "publicar": False, "ensemble": "a"},
                {**self.row("B", "nada"), "publicar": True, "ensemble": "b"}]
        report = self.campaign(rows, test_first=False)
        self.assertTrue(all(r["resultado"].startswith("OK") and "06" in r["resultado"] for r in report), report)
        e06 = [d[1] for d in self.dispatched if d[0] == lv.WF_06]
        self.assertEqual(sorted(e["territory_id"] for e in e06), ["a", "b"])
        self.assertEqual({e["territory_id"]: e["deploy_pages"] for e in e06}, {"a": False, "b": True})
        self.assertTrue(all(e["stage"] == "ensemble_10" and e["execution_confirmed"] for e in e06))
        a00 = [d[1] for d in self.dispatched if d[0] == lv.WF_00]
        self.assertEqual([(d["territory_id"], d["publish_result"]) for d in a00], [("A", False)])
        self.assertNotIn(lv.WF_05, [d[0] for d in self.dispatched])

    def test_aprovechar_fuentes(self):
        self.campaign([self.row("A", "aprovechar_fuentes")])
        self.assertEqual(self.dispatched[0][1]["execution_mode"], "Generar desde fuente territorial acreditada")


class Workflow(unittest.TestCase):
    def test_formulario_2_0_y_plan_en_pr(self):
        text = WF.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        inputs = data.get(True, data.get("on"))["workflow_dispatch"]["inputs"]
        self.assertEqual(list(inputs)[:8], ["eleccion", "tipo", "territorios", "inicio", "publicar", "ensemble",
                                            "mapa", "solo_plan"])  # orden de D-22
        self.assertIs(inputs["solo_plan"]["default"], True)
        self.assertEqual(inputs["modo"]["default"], "gestor")
        job = data["jobs"]["legislatura"]
        self.assertIn("inputs.modo == 'gestor' && !inputs.solo_plan) && 'produccion'", job["environment"])
        self.assertIn("github.event_name == 'pull_request'", job["if"])
        self.assertIn("generar --comprobar", text)
        self.assertIn("inputs.modo == 'matriz'", data["jobs"]["preparar"]["if"])


if __name__ == "__main__":
    unittest.main()
