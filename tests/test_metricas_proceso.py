"""T-65: métricas del proceso con datos simulados de la API."""
from __future__ import annotations

import json
import tempfile
import unittest
import unittest.mock
from datetime import datetime, timezone
from pathlib import Path

import yaml

from herramientas import metricas_proceso as mp

ROOT = Path(__file__).resolve().parents[1]


def run(i, ini, fin, concl, titulo="00 Ejecución Completa del Proyecto", path=".github/workflows/ejecucion-completa-proyecto.yml",
        actor="jfmurciego", event="workflow_dispatch", name="00 Ejecución Completa del Proyecto"):
    return {"id": i, "created_at": ini, "run_started_at": ini, "updated_at": fin, "conclusion": concl, "display_title": titulo,
            "path": path, "event": event, "name": name, "actor": {"login": actor}}


def rn(t):
    return f"00 Ejecución Completa del Proyecto · {t} · Reutilizar"


class ApiFalsa:
    repo = "o/r"

    def __init__(self, runs, prs=(), jobs=None, logs=None):
        self.runs, self.prs, self.jobs, self.logs, self.llamadas = runs, list(prs), jobs or {}, logs or {}, []

    def get(self, ruta, params=None):
        self.llamadas.append(ruta)
        if ruta == "actions/runs":
            return {"workflow_runs": self.runs if params["page"] == 1 else []}
        if ruta == "pulls":
            return self.prs if params["page"] == 1 else []
        if ruta.startswith("actions/runs/") and ruta.endswith("/jobs"):
            return {"jobs": self.jobs.get(ruta.split("/")[2], [])}
        raise AssertionError(ruta)

    def texto(self, ruta):
        return self.logs[ruta]


class Calculos(unittest.TestCase):
    def test_a_la_primera_e_intentos_por_territorio_y_semana(self):
        runs = [run(1, "2026-11-02T10:00:00Z", "2026-11-02T10:30:00Z", "failure"),
                run(2, "2026-11-03T10:00:00Z", "2026-11-03T10:30:00Z", "success"),
                run(3, "2026-11-04T10:00:00Z", "2026-11-04T10:20:00Z", "success", actor="github-actions[bot]"),
                run(4, "2026-11-05T10:00:00Z", "2026-11-05T10:20:00Z", "cancelled")]
        terr = {"1": "murcia", "2": "murcia", "3": "huesca", "4": "huesca"}
        r = mp.calcular_00(runs, terr)
        por = {f["territorio"]: f for f in r["por_territorio"]}
        self.assertEqual(por["murcia"]["intentos_hasta_exito"], 2)
        self.assertFalse(por["murcia"]["a_la_primera"])
        self.assertTrue(por["huesca"]["a_la_primera"])
        self.assertEqual(r["pct_a_la_primera"], 50.0)
        self.assertEqual(r["runs_cancelados_u_omitidos"], 1)
        self.assertEqual(r["runs_por_actor"]["github-actions[bot]"], 1)  # cuentan los encadenados del bot
        self.assertEqual(r["por_semana"][0]["semana"], "2026-W45")
        self.assertEqual(r["por_semana"][0]["pct_a_la_primera"], 50.0)

    def test_territorio_sin_exito_y_sin_territorio(self):
        r = mp.calcular_00([run(1, "2026-11-02T10:00:00Z", "2026-11-02T10:30:00Z", "failure"),
                            run(2, "2026-11-02T11:00:00Z", "2026-11-02T11:30:00Z", "failure")], {"1": "malaga"})
        self.assertEqual(r["con_exito"], 0)
        self.assertIsNone(r["por_territorio"][0]["intentos_hasta_exito"])
        self.assertEqual(r["runs_sin_territorio"], 1)

    def test_minutos_por_workflow(self):
        f = mp.minutos_por_workflow([run(1, "2026-11-02T10:00:00Z", "2026-11-02T10:30:00Z", "success"),
                                     run(2, "2026-11-02T11:00:00Z", "2026-11-02T11:10:00Z", "failure"),
                                     run(3, "2026-11-02T11:00:00Z", "2026-11-02T11:10:00Z", None)])
        self.assertEqual(f, [{"workflow": "00 Ejecución Completa del Proyecto", "runs": 2, "minutos": 40.0}])

    def test_prs_fusionadas_por_dia_y_tiempo(self):
        desde = datetime(2026, 11, 1, tzinfo=timezone.utc)
        prs = [{"created_at": "2026-11-02T08:00:00Z", "merged_at": "2026-11-02T10:00:00Z"},
               {"created_at": "2026-11-02T08:00:00Z", "merged_at": "2026-11-02T14:00:00Z"},
               {"created_at": "2026-11-02T08:00:00Z", "merged_at": None},
               {"created_at": "2026-10-01T08:00:00Z", "merged_at": "2026-10-02T08:00:00Z"}]
        r = mp.calcular_prs(prs, desde)
        self.assertEqual((r["fusionadas"], r["fusionadas_por_dia"], r["horas_abierta_mediana"]), (2, {"2026-11-02": 2}, 4.0))

    def test_duracion_de_pruebas_solo_pr_y_ok(self):
        n = mp.NOMBRE_PRUEBAS
        r = mp.calcular_pruebas([run(1, "2026-11-02T10:00:00Z", "2026-11-02T10:05:00Z", "success", event="pull_request", name=n),
                                 run(2, "2026-11-02T10:00:00Z", "2026-11-02T10:09:00Z", "success", event="pull_request", name=n),
                                 run(3, "2026-11-02T10:00:00Z", "2026-11-02T10:40:00Z", "failure", event="pull_request", name=n),
                                 run(4, "2026-11-02T10:00:00Z", "2026-11-02T11:00:00Z", "success", event="push", name=n)])
        self.assertEqual((r["runs_ok"], r["minutos_mediana"]), (2, 7.0))

    def test_costes_desde_libro(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "evals").mkdir()
            (Path(d) / "evals/LIBRO_DE_COSTES.md").write_text(
                "- 2026-11-07 · revisor · PR #425: 92.390 tokens.\n- 2026-11-07 · forense · sin cifra\n"
                "| Fecha | Agente | Modelo | Etiqueta | Casos | Aciertos | % | Tokens | A la primera |\n|---|---|---|---|---|---|---|---|---|\n"
                "| 2026-11-08 | revisor | sonnet | v2 | 24 | 20 | 83 | 1.500 | 10/12 |\n", encoding="utf-8")
            c = mp.leer_costes(Path(d))
        self.assertEqual(c["tokens_total"], 93890)
        self.assertEqual(len(c["filas_tabla"]), 1)

    def test_costes_reales_se_leen(self):
        self.assertGreaterEqual(mp.leer_costes(ROOT)["tokens_total"], 92390)


class Generacion(unittest.TestCase):
    def test_generar_resuelve_territorio_por_nombre_y_por_log_y_cachea(self):
        ahora = datetime(2026, 11, 8, tzinfo=timezone.utc)
        pr = dict(event="pull_request")
        runs = [run(10, "2026-11-02T10:00:00Z", "2026-11-02T10:30:00Z", "failure", titulo=rn("congreso_huesca")),
                run(11, "2026-11-03T10:00:00Z", "2026-11-03T10:30:00Z", "success"),  # sin título: sale del log
                run(12, "2026-11-03T12:00:00Z", "2026-11-03T12:05:00Z", "failure", name="Pruebas de la Plataforma", titulo="PR", path="x.yml", **pr)]
        jobs = {"11": [{"id": 99, "name": "Planificar ejecución completa", "started_at": "2026-11-03T10:00:00Z", "completed_at": "2026-11-03T10:01:00Z"}],
                "10": [{"id": 98, "name": "x", "started_at": "2026-11-02T10:00:00Z", "completed_at": "2026-11-02T10:12:00Z"}],
                "12": [{"id": 97, "name": "pruebas", "conclusion": "failure", "steps": [{"name": "Ejecutar suite", "conclusion": "failure"}]}]}
        api = ApiFalsa(runs, [{"created_at": "2026-11-03T08:00:00Z", "merged_at": "2026-11-03T09:00:00Z", "updated_at": "2026-11-03T09:00:00Z"}],
                       jobs, {"actions/jobs/99/logs": "2026-11-03 TERRITORY: Congreso Huesca\n"})
        with tempfile.TemporaryDirectory() as d:
            e = Path(d) / "territorios/congreso_huesca/evidencia/ejecuciones_completas"
            e.mkdir(parents=True)
            (e / "1.json").write_text(json.dumps({"territory_id": "congreso_huesca", "territory_name": "Congreso Huesca", "workflow_run_id": 1}))
            r = mp.generar(api, Path(d), 30, 5, 5, ahora=ahora)
        p = r["ejecuciones_00"]
        self.assertEqual([f["territorio"] for f in p["por_territorio"]], ["congreso_huesca"])
        self.assertEqual(p["por_territorio"][0]["intentos_hasta_exito"], 2)
        self.assertEqual(r["cache"]["territorio_por_run"], {"11": "congreso_huesca"})
        self.assertEqual(r["minutos_actions"]["por_territorio_00"][0]["territorio"], "congreso_huesca")
        self.assertEqual(r["fallos_ci_pr"]["por_causa"], {"Pruebas de la Plataforma / pruebas · Ejecutar suite": 1})
        self.assertEqual(r["pr"]["fusionadas"], 1)
        # segunda pasada con la caché: no se vuelven a pedir ni logs ni jobs
        api2 = ApiFalsa(runs, [], {}, {})
        r2 = mp.generar(api2, Path(d) if False else ROOT / "tests", 30, 0, 0, ahora=ahora, previo=r)
        self.assertEqual(r2["cache"]["territorio_por_run"], {"11": "congreso_huesca"})
        self.assertFalse([x for x in api2.llamadas if x.endswith("/jobs")])

    def test_eventos_de_pr_no_cuentan_como_00(self):
        api = ApiFalsa([run(1, "2026-11-02T10:00:00Z", "2026-11-02T10:30:00Z", "success", titulo=rn("x"), event="pull_request")])
        r = mp.generar(api, ROOT / "tests", 30, 0, 0, ahora=datetime(2026, 11, 8, tzinfo=timezone.utc))
        self.assertEqual(r["ejecuciones_00"]["territorios"], 0)


class ApiTopada:
    """API simulada fiel al defecto T-155: filtra por `created=a..b`, pagina de 100 y no devuelve más de 1.000 (los más recientes)."""
    repo = "o/r"

    def __init__(self, runs, minutos_job=10):
        self.runs, self.minutos_job, self.fallos_pendientes = runs, minutos_job, 0

    def get(self, ruta, params=None):
        if ruta == "actions/runs":
            a, b = params["created"].split("..")
            sel = sorted((r for r in self.runs if a <= r["created_at"] <= b), key=lambda r: r["created_at"], reverse=True)[:1000]
            i = (params["page"] - 1) * 100
            return {"workflow_runs": sel[i:i + 100]}
        if ruta == "pulls":
            return []
        if ruta.startswith("actions/runs/") and ruta.endswith("/jobs"):
            if self.fallos_pendientes:
                self.fallos_pendientes -= 1
                raise ConnectionResetError("reset")
            return {"jobs": [{"id": 1, "name": "j", "started_at": "2026-11-05T10:00:00Z",
                              "completed_at": f"2026-11-05T10:{self.minutos_job:02d}:00Z"}]}
        raise AssertionError(ruta)

    def texto(self, ruta):
        return ""


class PaginacionCompleta(unittest.TestCase):
    def runs(self):
        out = []
        for i in range(1300):  # 1.300 en una sola hora: obliga a partir la ventana
            out.append(run(i + 1, f"2026-11-05T03:{(i // 60) % 60:02d}:{i % 60:02d}Z", "2026-11-05T05:00:00Z", "success",
                           titulo="x", path=".github/workflows/otro.yml", name="Otro"))
        for i in range(1300):  # 1.300 repartidos en cuatro días
            d = 1 + (i % 4)
            out.append(run(5000 + i, f"2026-11-0{d}T{(i * 7) % 24:02d}:{(i * 13) % 60:02d}:{(i * 29) % 60:02d}Z",
                           "2026-11-05T05:00:00Z", "failure", titulo="y", path=".github/workflows/otro2.yml", name="Otro2"))
        return out

    def test_mas_de_mil_runs_suman_el_total_exacto(self):
        runs = self.runs()
        api = ApiTopada(runs)
        # control: la consulta única del defecto se queda en 1.000
        self.assertEqual(len(api.get("actions/runs", {"created": "2026-11-01T00:00:00Z..2026-11-10T00:00:00Z", "page": 1})["workflow_runs"]), 100)
        r = mp.generar(api, ROOT / "tests", 10, 0, 100000, ahora=datetime(2026, 11, 10, tzinfo=timezone.utc))
        m = r["minutos_actions"]
        self.assertEqual(m["runs"], 2600)
        self.assertEqual(m["runs_con_reloj_en_vez_de_jobs"], 0)
        self.assertEqual(m["total"], 26000.0)  # 2.600 runs × 1 job de 10 min (literal, no recalculado)
        self.assertEqual({f["workflow"]: f["runs"] for f in m["por_workflow"]}, {"Otro": 1300, "Otro2": 1300})

    def test_reintenta_tras_reseteo_de_conexion(self):
        api = ApiTopada([run(1, "2026-11-05T10:00:00Z", "2026-11-05T11:00:00Z", "success", path="a.yml", name="A")])
        api.fallos_pendientes = 2
        with unittest.mock.patch.object(mp.time, "sleep"):
            # el simulado lanza ConnectionResetError; el cliente real reintenta en Cliente.get
            cli = mp.Cliente("o/r", token="t")
            llamadas = []

            def falso(req, timeout=0):
                llamadas.append(1)
                if len(llamadas) < 3:
                    raise ConnectionResetError("reset")
                import io
                return io.BytesIO(b'{"ok": 1}')
            with unittest.mock.patch.object(mp.urllib.request, "urlopen", falso):
                self.assertEqual(cli.get("actions/runs"), {"ok": 1})
        self.assertEqual(len(llamadas), 3)


class TopeSemanal(unittest.TestCase):
    def test_umbrales_70_y_100_sin_corte(self):
        # W44 (2026-11-02): 10.499 min → sin aviso; W45: 10.500 → 70; W46: 15.000 → 100
        runs = [run(1, "2026-11-02T10:00:00Z", "x", "success"), run(2, "2026-11-09T10:00:00Z", "x", "success"),
                run(3, "2026-11-16T10:00:00Z", "x", "success")]
        g = mp.gasto_semanal(runs, {"1": 10499.0, "2": 10500.0, "3": 15000.0})
        self.assertEqual([f["aviso"] for f in g["por_semana"]], [None, 70, 100])
        self.assertEqual(g["por_semana"][1]["pct_tope"], 70.0)
        self.assertEqual(g["aviso_semana_actual"], 100)
        self.assertFalse(g["corte_automatico"])

    def test_generar_incluye_gasto_semanal(self):
        r = ApiTopada([run(1, "2026-11-05T10:00:00Z", "2026-11-05T11:00:00Z", "success", path="a.yml", name="A")])
        d = mp.generar(r, ROOT / "tests", 10, 0, 10, ahora=datetime(2026, 11, 10, tzinfo=timezone.utc))
        self.assertEqual(d["minutos_actions"]["gasto_semanal"]["por_semana"][0]["minutos"], 10.0)


class Entrega(unittest.TestCase):
    def test_workflow_semanal_con_cola_y_registro(self):
        w = yaml.safe_load((ROOT / ".github/workflows/metricas-proceso.yml").read_text(encoding="utf-8"))
        on = w.get("on", w.get(True))
        self.assertIn("schedule", on)
        self.assertIn("workflow_dispatch", on)
        self.assertEqual(w["concurrency"]["queue"], "max")
        self.assertFalse(w["concurrency"]["cancel-in-progress"])
        texto = (ROOT / ".github/workflows/metricas-proceso.yml").read_text(encoding="utf-8")
        self.assertIn("DDD_REGISTRO_APP_ID", texto)
        self.assertIn("herramientas/metricas_proceso.py", texto)

    def test_pagina_enlazada_desde_el_indice(self):
        self.assertIn('href="metricas.html"', (ROOT / "dashboard/index.html").read_text(encoding="utf-8"))
        self.assertIn("metricas_proceso.json", (ROOT / "dashboard/metricas.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
