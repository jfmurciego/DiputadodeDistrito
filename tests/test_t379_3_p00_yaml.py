"""T-379 PR 3 (diseño T-378 1.1.4 §3, §4, §5, §6 y §10): forma de `p00-campana.yml` y de `p00-cadena.yml`.

Lee los ficheros reales; cada regla con su control negativo (el YAML mutilado en memoria debe fallar).
Los bloques de shell de «empezar» y «cerrar» de la cadena se ejecutan bajo `bash -eo pipefail` con un almacén local
(lección #726: un bloque nuevo se prueba ejecutándolo, rc 0 y fallo).
"""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
sys.path.insert(0, str(ROOT / "herramientas"))
import campana_estado as ce  # noqa: E402


def leer(nombre):
    return yaml.safe_load((WF / nombre).read_text(encoding="utf-8"))


def needs(job):
    n = job.get("needs") or []
    return [n] if isinstance(n, str) else list(n)


def ancestros(jobs, nombre, vistos=None):
    vistos = set() if vistos is None else vistos
    for n in needs(jobs[nombre]):
        if n not in vistos:
            vistos.add(n)
            ancestros(jobs, n, vistos)
    return vistos


def en_serie(jobs):
    """Ningún par de jobs puede correr a la vez: de cada dos, uno es ancestro del otro (§3, decisión B)."""
    nombres = list(jobs)
    libres = [(a, b) for i, a in enumerate(nombres) for b in nombres[i + 1:]
              if a not in ancestros(jobs, b) and b not in ancestros(jobs, a)]
    return libres


def usos(doc):
    return {j: v["uses"] for j, v in doc["jobs"].items() if "uses" in v}


class Cadena(unittest.TestCase):
    def setUp(self):
        self.doc = leer("p00-cadena.yml")
        self.jobs = self.doc["jobs"]

    def test_solo_workflow_call_y_solo_lectura(self):
        self.assertEqual(set(self.doc[True]), {"workflow_call"})
        self.assertEqual(self.doc["permissions"], {"contents": "read", "actions": "read"})
        texto = (WF / "p00-cadena.yml").read_text(encoding="utf-8")
        for prohibido in ("contents: write", "git push", "DDD_REGISTRO_APP", "registrar_en_main"):
            self.assertNotIn(prohibido, texto)

    def test_serie(self):
        self.assertEqual(en_serie(self.jobs), [])
        roto = copy.deepcopy(self.jobs)
        roto["p12"]["needs"] = ["plan", "p11"]  # P12 en paralelo con la puerta 01
        self.assertIn(("puerta_01", "p12"), en_serie(roto))

    def test_cancelled_en_todo_job_con_predecesor(self):
        for nombre, job in self.jobs.items():
            if needs(job):
                self.assertIn("!cancelled()", job.get("if", ""), nombre)

    def test_cada_paso_exige_el_sano_del_anterior(self):
        for nombre in ("p11", "cerrar_p10"):
            self.assertIn("needs.plan.outputs.sano == 'true'", self.jobs[nombre]["if"], nombre)
        for nombre in ("acreditar", "p20", "cerrar_p20"):
            self.assertIn("needs.cerrar_p10.outputs.sano == 'true'", self.jobs[nombre]["if"], nombre)
        for nombre in ("puerta_03", "cerrar_p30"):
            self.assertIn("needs.cerrar_p20.outputs.sano == 'true'", self.jobs[nombre]["if"], nombre)

    def test_p10_p30_con_campana_y_persistencia_en_ensayo(self):
        """3b: P10, P20 y P30 registran en ensayo (persist_state true)."""
        llamados = {j: u for j, u in usos(self.doc).items() if "puerta" not in u}
        self.assertEqual(set(llamados), {"p11", "p12", "acreditar", "p20", "p30"})
        for j in llamados:
            w = self.jobs[j]["with"]
            self.assertEqual(w["campana"], "${{ inputs.campana }}", j)
            self.assertIs(w["persist_state"], True, j)

    def test_source_ref_es_la_version_de_la_campana(self):
        """Los commits del registro en ensayo no existen en GitHub: ningún checkout puede apuntar a ellos."""
        for j, job in self.jobs.items():
            if "source_ref" in (job.get("with") or {}):
                self.assertEqual(job["with"]["source_ref"], "${{ github.sha }}", j)
        texto = (WF / "p00-cadena.yml").read_text(encoding="utf-8")
        self.assertNotIn("prepared_source_ref", texto)
        self.assertNotIn("enabled_source_ref", texto)

    def test_espacio_de_artefactos_por_territorio(self):
        for j in ("p20", "puerta_02", "puerta_03", "p30"):
            self.assertEqual(self.jobs[j]["with"]["artifact_namespace"], "${{ needs.plan.outputs.ns }}", j)

    def test_la_puerta_02_acepta_el_nombre_del_m06(self):
        """Regresión del humo 44609048607: el M06 de la cadena debe pasar la comprobación de nombre de la puerta real."""
        sys.path.insert(0, str(ROOT))
        from herramientas.validar_puerta_ejecucion import _artifact_name_is_consistent as ok
        plan = next(p for p in self.jobs["plan"]["steps"] if p.get("id") == "plan")["run"]
        linea = next(l for l in plan.splitlines() if l.strip().startswith('echo "ns='))
        ns = linea.split('"ns=', 1)[1].split("$(", 1)[0].replace("$GITHUB_RUN_ID", "900") + "aut11"
        self.assertEqual(ns, "campaign-900-1--01--aut11")
        self.assertTrue(ok("territorial_product", "aut11", "2025", "900", f"ddd-state-900-M06-{ns}", ns))
        # control negativo: el espacio a secas que llevaba la 1.0.0 del humo
        self.assertFalse(ok("territorial_product", "aut11", "2025", "900", "ddd-state-900-M06-aut11", "aut11"))

    def test_motor_fijo_y_modo_del_plan(self):
        w = self.jobs["p20"]["with"]
        self.assertEqual((w["motor"], w["optimization_algorithm"]), ("motor2", "Canónico"))
        self.assertEqual(w["execution_mode"], "${{ needs.plan.outputs.modo_p20 }}")

    def test_cada_paso_se_cierra_en_r2(self):
        pasos = {}
        for nombre, job in self.jobs.items():
            for paso in job.get("steps") or []:
                env = paso.get("env") or {}
                if "PASO" in env:
                    pasos.setdefault(env["PASO"], []).append((nombre, paso["id"]))
        self.assertEqual(pasos, {"P10": [("plan", "empezar"), ("cerrar_p10", "cerrar")],
                                 "P20": [("cerrar_p10", "empezar"), ("cerrar_p20", "cerrar")],
                                 "P30": [("cerrar_p20", "empezar"), ("cerrar_p30", "cerrar")]})

    def test_secretos_r2_en_el_paso(self):
        for nombre, job in self.jobs.items():
            self.assertNotIn("R2_ACCESS_KEY_ID", json.dumps(job.get("env") or {}), nombre)


class Bloques(unittest.TestCase):
    """Los bloques «empezar» y «cerrar» de la cadena, ejecutados (rc y salida `sano`)."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.dir = Path(self._td.name)
        self.alm = ce.AlmacenLocal(self.dir / "alm")
        ce.guardar_semaforo(self.alm, "900", ce.comprobar("nac22, nac42, nac52", "vigente"))
        jobs = leer("p00-cadena.yml")["jobs"]
        self.empezar = next(p for p in jobs["plan"]["steps"] if p.get("id") == "empezar")["run"]
        self.cerrar = next(p for p in jobs["cerrar_p10"]["steps"] if p.get("id") == "cerrar")["run"]

    def tearDown(self):
        self._td.cleanup()

    def bash(self, bloque, **env):
        salida = self.dir / "salida"
        salida.write_text("", encoding="utf-8")
        e = {**os.environ, "ALMACEN": f"dir:{self.dir / 'alm'}", "GITHUB_OUTPUT": str(salida), "CAMPANA": "900",
             "INTENTO": "1", **env}
        r = subprocess.run(["bash", "-eo", "pipefail", "-c", bloque], cwd=ROOT, env=e, capture_output=True, text=True)
        return r.returncode, salida.read_text(encoding="utf-8"), r.stderr

    def test_empezar_y_cerrar_ok(self):
        rc, out, err = self.bash(self.empezar, TERRITORIO="nac22", PASO="P10")
        self.assertEqual((rc, out), (0, "sano=true\n"), err)
        rc, out, err = self.bash(self.cerrar, TERRITORIO="nac22", PASO="P10", OBLIGATORIOS="p11 puerta_01",
                                 RESULTADOS='{"p11":"success","puerta_01":"success"}', HUELLAS='{"p":""}')
        self.assertEqual((rc, out), (0, "sano=true\n"), err)

    def test_cerrar_con_rojo_no_es_sano(self):
        self.bash(self.empezar, TERRITORIO="nac22", PASO="P10")
        rc, out, err = self.bash(self.cerrar, TERRITORIO="nac22", PASO="P10", OBLIGATORIOS="p11",
                                 RESULTADOS='{"p11":"failure"}', HUELLAS="{}")
        self.assertEqual((rc, out), (0, "sano=false\n"), err)

    def test_parada_da_sano_false_sin_fallar(self):
        for t in ("nac42", "nac52", "nac22"):
            ce.empezar(self.alm, "900", t, "P10", 1)
            ce.registrar(self.alm, "900", t, "P10", 1, "apartado", "CONTRATO_ROTO")
        rc, out, err = self.bash(self.empezar, TERRITORIO="nac22", PASO="P20")
        self.assertEqual((rc, out), (0, "sano=false\n"), err)

    def test_no_reejecutable_falla(self):
        self.bash(self.empezar, TERRITORIO="nac22", PASO="P10")
        self.bash(self.cerrar, TERRITORIO="nac22", PASO="P10", OBLIGATORIOS="p11", RESULTADOS='{"p11":"failure"}',
                  HUELLAS="{}")
        rc, out, _ = self.bash(self.empezar, TERRITORIO="nac22", PASO="P10", INTENTO="2")
        self.assertEqual((rc, out), (ce.RC_NO_REEJECUTABLE, ""))


class Campana(unittest.TestCase):
    def setUp(self):
        self.doc = leer("p00-campana.yml")
        self.jobs = self.doc["jobs"]

    def test_nombre_y_run_name(self):
        self.assertEqual(self.doc["name"], "P00 Campaña")  # §9: mismo nombre que la 00 mientras convivan
        self.assertIn("· campaña ·", self.doc["run-name"])

    def test_boton_sin_parametros_tecnicos(self):
        entradas = self.doc[True]["workflow_dispatch"]["inputs"]
        self.assertEqual(list(entradas), ["territorios", "eleccion", "inicio", "modo", "publicar"])
        self.assertEqual(entradas["modo"]["default"], "solo comprobar")
        self.assertEqual(entradas["publicar"]["default"], "no")

    def test_sin_concurrencia_de_workflow(self):
        self.assertNotIn("concurrency", self.doc)  # §3: la segunda campaña se rechaza, no se encola

    def test_matriz(self):
        c = self.jobs["cadena"]
        self.assertEqual(c["uses"], "./.github/workflows/p00-cadena.yml")
        self.assertEqual(c["permissions"], {"contents": "read", "actions": "read"})
        self.assertIs(c["strategy"]["fail-fast"], False)
        self.assertEqual(c["strategy"]["max-parallel"], 15)
        self.assertEqual(c["with"]["campana"], "${{ github.run_id }}")

    def test_cierres_excluyentes(self):
        m, r = self.jobs["cierre_main"]["if"], self.jobs["cierre_rama"]["if"]
        self.assertIn("github.ref == 'refs/heads/main'", m)
        self.assertNotIn("github.ref != 'refs/heads/main'", m)
        self.assertIn("github.ref != 'refs/heads/main'", r)
        for j in ("cierre_main", "cierre_rama"):
            self.assertIn("!cancelled()", self.jobs[j]["if"], j)
            self.assertNotIn("environment", self.jobs[j], j)  # entra con la 2a (D-164)
        self.assertNotIn("DDD_REGISTRO_APP", json.dumps(self.jobs["cierre_rama"]))

    def test_resultado(self):
        r = self.jobs["resultado"]
        self.assertEqual(r["name"], "resultado")  # nombre exacto (#882, P90)
        self.assertEqual(r["if"], "${{ !cancelled() }}")
        self.assertTrue({"cierre_main", "cierre_rama", "publicar", "cadena", "comprobar"} <= set(needs(r)))

    def test_publicar_solo_tras_commit_en_main(self):
        p = self.jobs["publicar"]
        self.assertEqual(p["uses"], "./.github/workflows/p40-publicacion.yml")
        for trozo in ("needs.comprobar.outputs.publicar == 'true'", "needs.cierre_main.outputs.commit == 'true'"):
            self.assertIn(trozo, p["if"])

    def test_solo_el_cierre_escribe(self):
        """3b: la app de registro solo en cierre_main; el único push directo es la rama de cierre de cierre_rama."""
        for j, job in self.jobs.items():
            t = json.dumps(job, ensure_ascii=False)
            self.assertEqual("DDD_REGISTRO_APP" in t, j == "cierre_main", j)
            self.assertNotIn("git push", t, j)
            self.assertEqual("campana_registro.py cerrar" in t, j in ("cierre_main", "cierre_rama"), j)
        rama = self.jobs["cierre_rama"]
        crea = next(p for p in rama["steps"] if "git/refs" in p.get("run", ""))
        self.assertIn('rama="p00-cierre/$GITHUB_RUN_ID"', crea["run"])
        self.assertIn('"ref=refs/heads/$rama"', crea["run"])
        # la rama de cierre usa GITHUB_TOKEN; el árbol de main del cierre en main, la app (sin credenciales del checkout)
        destino = lambda job: next(p for p in self.jobs[job]["steps"] if (p.get("with") or {}).get("path") == "destino")
        self.assertEqual(destino("cierre_main")["with"]["persist-credentials"], False)
        self.assertEqual(destino("cierre_rama")["with"]["persist-credentials"], True)

    def test_humo_en_pull_request(self):
        self.assertIn("pull_request", self.doc[True])
        self.assertIn("nac22, aut11, xyz99", json.dumps(self.jobs["comprobar"], ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
