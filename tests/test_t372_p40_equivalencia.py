# -*- coding: utf-8 -*-
"""T-372 (D-134, paso 5): P40 Publicación sustituye a `desplegar-visor-publico.yml`, `cadena-publicacion.yml` y `_reutilizable-publicar-sitio.yml`.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-16 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
La equivalencia se calcula contra COPIAS CONGELADAS (`tests/fixtures/t372_workflows/`, con sha256; en CI no hay `legacy/`). Si falta una o cambia su huella el
test FALLA (no se salta). Controles negativos: un permiso, entorno, concurrencia, paso o comando cambiados se detectan.
"""
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from tests import _t428, _t430
from tests._uses_sin_version import cargar as cargar_sin_version

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
FIX = ROOT / "tests" / "fixtures" / "t372_workflows"
SHAS = {
    "desplegar-visor-publico_3.6.0.yml": "2fc437f9fd91cc1eedff2e12fa4326ef525c638e727cab1d21128704595f9ae7",
    "cadena-publicacion_1.1.0.yml": "e790d97be0e65fb9966b8d6cc6910a9fb2c815830900ea492e87cac5370c0ca2",
    "reutilizable-publicar-sitio_3.17.0.yml": "81d9d29499af7c0cda76445bd7d5fe70745e22e86e12f24d13cc4887594a7d04",
}
# Las únicas sustituciones permitidas en el cuerpo del publicador: sus entradas pasan a salidas del job `preparar` (o del propio `inputs` del workflow_call).
SUSTITUCIONES = [
    ("${{ inputs.production_run_id || '' }}", "${{ needs.preparar.outputs.production_run_id || '' }}"),
    ("${{ inputs.target_page || 'Visor territorial' }}", "${{ inputs.target_page || inputs.pagina_publicar || 'Sitio completo' }}"),
    ("${{ inputs.source_ref || github.sha }}", "${{ needs.preparar.outputs.source_ref || github.sha }}"),
    ("${{ inputs.production_run_id != '' }}", "${{ needs.preparar.outputs.production_run_id != '' }}"),
]


def on(d):
    return d.get("on") or d.get(True)


def normalizar(texto):
    for a, b in SUSTITUCIONES:
        texto = texto.replace(a, b)
    return texto


def paso(job, nombre):
    return next(s for s in job["steps"] if s.get("name") == nombre)


# T-377 (D-138): P40 1.1.0 pierde la rama del ensemble y los escenarios; lo mismo se quita del publicador viejo antes de comparar.
SIN_ENSEMBLE = [(' --scenario-id \\"$SCENARIO_ID\\")', ")"),
                (' ${SCENARIO_ID:+--scenario-id \\"$SCENARIO_ID\\" --strategy \\"$SCENARIO_STRATEGY\\"}', "")]
ENV_ENSEMBLE = ("SCENARIO_ID", "SCENARIO_STRATEGY", "ENSEMBLE_RELEASE_TAG", "ENSEMBLE_SHA256")


def sin_ensemble(job):
    job = copy.deepcopy(job)
    job["steps"] = [s for s in job["steps"] if s.get("name") != "Resolver ensemble persistente solicitado"]
    for k in ENV_ENSEMBLE:
        job["env"].pop(k, None)
    t = json.dumps(job["steps"])
    for a, b in SIN_ENSEMBLE:
        assert a in t, a
        t = t.replace(a, b)
    job["steps"] = json.loads(t)
    return job


PASO_DV_T409 = "Doble vuelta de los territorios del Congreso para la V4 (D-172)"
CP_V4_T409 = ("          mkdir -p /tmp/site-candidate/v4 && cp -R visor/v4/. /tmp/site-candidate/v4/  # T-409: el visor V4 completo (el paso de la doble vuelta añade v4/mapa/datos/ después)\n"
              "          while IFS= read -r f; do [[ -z \"$f\" || \"$f\" == \\#* || \"$f\" == /* || \"$f\" == *..* ]] || rm -rf \"/tmp/site-candidate/v4/$f\"; done < visor/v4/NO_PUBLICAR.txt  # lo ficticio o interno no se publica\n")

LINEAS_V4_T409 = {l.strip() for l in CP_V4_T409.splitlines()}


def diferencias(viejo, nuevo):
    """Diferencias NO permitidas del job de publicación (vacía = equivalente)."""
    a, b = sin_ensemble(viejo["jobs"]["publicar"]), nuevo["jobs"]["publicar"]
    b = {**b, "steps": _t428.deshacer(_t430.deshacer(b["steps"]))}  # T-428 (P40 1.3.0) y T-430 (1.4.0): se deshace solo eso
    d = []
    if a["environment"] != b["environment"]:
        d.append("entorno")
    if viejo["permissions"] != nuevo["permissions"]:
        d.append("permisos")
    if viejo["concurrency"] != b.get("concurrency"):
        d.append("concurrencia")
    if a["runs-on"] != b["runs-on"]:
        d.append("runs-on")
    # T-409 (P40 1.2.0): el paso de la doble vuelta de la V4 no existía en el publicador viejo; lo demás tiene que ser idéntico
    # y la copia de visor/v4/ son DOS líneas añadidas junto al cp de V3: quitadas esas líneas, el resto del paso es idéntico (V2 y V3 no cambian)
    pasos_nuevo = [{**s, "run": "\n".join(l for l in s["run"].split("\n") if l.strip() not in LINEAS_V4_T409)} if "run" in s else s for s in b["steps"] if s.get("name") != PASO_DV_T409]
    if json.loads(normalizar(json.dumps(a["steps"]))) != pasos_nuevo:
        d.append("pasos")
    if json.loads(normalizar(json.dumps(a["env"]))) != b["env"]:
        d.append("env")
    return d


class Congelado(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for nombre, sha in SHAS.items():
            assert (FIX / nombre).is_file(), f"falta la copia congelada {nombre}"  # nunca se salta
            assert hashlib.sha256((FIX / nombre).read_bytes()).hexdigest() == sha, f"la copia congelada {nombre} cambió"
        cls.rec = cargar_sin_version((FIX / "reutilizable-publicar-sitio_3.17.0.yml").read_text(encoding="utf-8"))
        cls.des = cargar_sin_version((FIX / "desplegar-visor-publico_3.6.0.yml").read_text(encoding="utf-8"))
        cls.cad = cargar_sin_version((FIX / "cadena-publicacion_1.1.0.yml").read_text(encoding="utf-8"))
        cls.p = cargar_sin_version((WF / "p40-publicacion.yml").read_text(encoding="utf-8"))
        cls.txt = (WF / "p40-publicacion.yml").read_text(encoding="utf-8")


class Boton(Congelado):
    def test_ficheros_viejos_borrados_y_nombre(self):
        for f in ("desplegar-visor-publico.yml", "cadena-publicacion.yml", "_reutilizable-publicar-sitio.yml"):
            self.assertFalse((WF / f).exists(), f)
        self.assertEqual(self.p["name"], "P40 Publicación")

    def test_entradas_del_boton(self):
        e = on(self.p)["workflow_dispatch"]["inputs"]
        self.assertEqual(set(e), {"que_publicar", "territorios", "simular"})
        self.assertEqual(e["que_publicar"]["options"], ["Solo el sitio", "Territorios"])
        self.assertEqual(e["que_publicar"]["default"], "Solo el sitio")  # el valor más inocuo
        self.assertEqual(e["territorios"]["type"], "string")
        self.assertIs(e["simular"]["default"], True)
        self.assertEqual(e["simular"]["type"], "boolean")
        for k in e:
            self.assertTrue(k.isascii() and k.isidentifier(), k)  # GitHub no admite tildes en los inputs

    def test_entradas_tecnicas_solo_por_workflow_call(self):
        c = on(self.p)["workflow_call"]["inputs"]
        self.assertTrue({"production_run_id", "target_page", "pagina_publicar"} <= set(c))
        self.assertNotIn("source_sha", c)
        for k in ("scenario_id", "scenario_strategy", "ensemble_release_tag", "ensemble_sha256"):  # T-377 (D-138)
            self.assertNotIn(k, c)
        for k in ("production_run_id",):
            self.assertNotIn(k, on(self.p)["workflow_dispatch"]["inputs"])

    def test_siempre_sitio_completo_desde_el_boton(self):
        self.assertIn("inputs.target_page || inputs.pagina_publicar || 'Sitio completo'", self.txt)

    def test_llamadores_apuntan_al_fichero_nuevo(self):
        g = yaml.safe_load((WF / "ejecucion-completa-proyecto.yml").read_text(encoding="utf-8"))["jobs"]["publicar"]
        self.assertEqual(g["uses"], "./.github/workflows/p40-publicacion.yml")
        self.assertEqual(g["with"]["pagina_publicar"], "Sitio completo")
        self.assertFalse((WF / "generar-alternativas-territoriales.yml").exists())  # T-377 (D-138): retirado sin sustituto
        for f in WF.glob("*.yml"):
            t = f.read_text(encoding="utf-8")
            for viejo in ("desplegar-visor-publico", "_reutilizable-publicar-sitio", "cadena-publicacion"):
                self.assertNotIn(f"workflows/{viejo}.yml", "\n".join(l for l in t.splitlines() if not l.lstrip().startswith("#")), f.name)


class Equivalencia(Congelado):
    def test_publicador_equivalente(self):
        self.assertEqual(diferencias(self.rec, self.p), [])

    def test_entorno_permisos_y_concurrencias(self):
        j = self.p["jobs"]
        self.assertEqual(j["publicar"]["environment"], {"name": "github-pages", "url": "${{ steps.deployment.outputs.page_url }}"})
        self.assertEqual(self.p["permissions"], self.des["permissions"])
        self.assertEqual(self.p["permissions"], self.rec["permissions"])
        self.assertEqual(j["publicar"]["concurrency"], {"group": "ddd-pages-prod", "cancel-in-progress": False, "queue": "max"})
        self.assertEqual(j["preparar"]["concurrency"], self.des["jobs"]["preparar_publicacion"]["concurrency"])
        self.assertNotIn("concurrency", self.p)  # a nivel de workflow no hay: cada grupo va en su job, como antes
        self.assertEqual(j["resolver"]["permissions"], {"contents": "read", "actions": "read"})  # ningún job gana permisos
        self.assertNotIn("permissions", j["preparar"])

    def test_puerta_produccion_intacta(self):
        a = self.des["jobs"]["preparar_publicacion"]["environment"]
        from tests._t379_3b import sin_p00_en_p40  # T-379 3b (G4): también la pide P00 Campaña nueva
        b = sin_p00_en_p40(self.p["jobs"]["preparar"]["environment"])
        self.assertEqual(b, a.replace("P50 Publicación", "P40 Publicación"))
        self.assertIn("github.workflow == 'P40 Publicación'", b)

    def test_preparar_equivalente_salvo_el_paso_resolver(self):
        va = self.des["jobs"]["preparar_publicacion"]
        nb = self.p["jobs"]["preparar"]
        self.assertEqual(va["runs-on"], nb["runs-on"])
        self.assertEqual(va["outputs"], nb["outputs"])
        sa = [s for s in va["steps"] if s.get("id") != "resolve"]
        sb = [s for s in nb["steps"] if s.get("id") != "resolve"]
        self.assertEqual(sa, sb)
        ra, rb = paso(va, "Regenerar promoción compartida desde el HEAD vigente"), paso(nb, "Regenerar promoción compartida desde el HEAD vigente")
        self.assertIn("python -m herramientas.persistir_estado_operativo_compartido", rb["run"])
        self.assertIn("--root-dir . --edition 2025 --target-branch main --sync-dashboard-assets", rb["run"])
        self.assertIn("cp orchestracion/estado_operativo.json .ddd-publication/status.json", rb["run"])
        self.assertEqual(rb["env"]["PRODUCTION_RUN_ID_OVERRIDE"], "${{ needs.resolver.outputs.production_run_id }}")
        self.assertNotIn("SOURCE_SHA", json.dumps(rb))  # la cadena ya no existe: sin comprobación de ancestro

    def test_salidas_del_publicador_y_artefactos_intactos(self):
        a = [s for s in self.rec["jobs"]["publicar"]["steps"] if s.get("uses", "").startswith(("actions/upload-artifact", "actions/deploy-pages",
                                                                                              "actions/upload-pages-artifact", "actions/configure-pages"))]
        b = [s for s in self.p["jobs"]["publicar"]["steps"] if s.get("uses", "").startswith(("actions/upload-artifact", "actions/deploy-pages",
                                                                                            "actions/upload-pages-artifact", "actions/configure-pages"))]
        self.assertTrue(a)
        self.assertEqual(json.loads(normalizar(json.dumps(a))), b)

    def test_sin_ruta_del_ensemble(self):  # T-377 (D-138): resolver siempre corre; publicar solo tras preparar
        j = self.p["jobs"]
        self.assertNotIn("if", j["resolver"])
        self.assertEqual(j["publicar"]["if"], "${{ needs.preparar.result == 'success' }}")
        self.assertEqual(j["publicar"]["needs"], ["resolver", "preparar"])

    def test_quita_lo_de_la_cadena_que_no_se_usa(self):
        for s in ("M06_ARTEFACTO_CADUCADO", "m06_run_id", "m06_artifact", "source_sha", "SOURCE_SHA_NO_ES_ANCESTRO"):
            self.assertNotIn(s, self.txt)
        self.assertIn("M08_ARTEFACTO_CADUCADO", self.txt)  # solo aviso


class Negativos(Congelado):
    def test_controles_negativos(self):
        casos = {
            "permisos": lambda n: n["permissions"].__setitem__("packages", "write"),
            "entorno": lambda n: n["jobs"]["publicar"].__setitem__("environment", "produccion"),
            "concurrencia": lambda n: n["jobs"]["publicar"]["concurrency"].__setitem__("group", "otro"),
            "runs-on": lambda n: n["jobs"]["publicar"].__setitem__("runs-on", "ubuntu-latest"),
            "pasos": lambda n: n["jobs"]["publicar"]["steps"][-1].__setitem__("run", "echo hola"),
            "env": lambda n: n["jobs"]["publicar"]["env"].__setitem__("GH_TOKEN", "x"),
        }
        for esperado, tocar in casos.items():
            n = copy.deepcopy(self.p)
            tocar(n)
            self.assertIn(esperado, diferencias(self.rec, n), esperado)

    def test_huella_congelada_no_se_salta(self):
        with self.assertRaises(AssertionError):
            h = hashlib.sha256(b"otra cosa").hexdigest()
            assert h == SHAS["desplegar-visor-publico_3.6.0.yml"], "cambió"


# ---------------------------------------------------------------- el paso «Resolver y comprobar», ejecutado de verdad
def registro_00(root, terr, run, ok04=True, ok=True, repo=None):
    d = root / "territorios" / terr / "evidencia" / "ejecuciones_completas"
    d.mkdir(parents=True, exist_ok=True)
    fase = lambda n, r: {"name": n, "validation_decision": "VALIDADO", "phase_decision": "PASS", "run_id": r, "artifact": f"ddd-state-{r}-{n[:2]}"}
    f04 = fase("04 · I", repo or run) if ok04 else {"name": "04 · I", "validation_decision": "BLOQUEADO", "phase_decision": None, "run_id": run, "artifact": None}
    (d / f"{run}.json").write_text(json.dumps({"territory_id": terr, "status": "SUCCESS" if ok else "FAILED",
                                               "phases": [fase("02 · G", run), f04]}), encoding="utf-8")


class PasoResolver(Congelado):
    def ejecutar(self, root, bindir, **env):
        paso_r = paso(self.p["jobs"]["resolver"], "Resolver y comprobar")
        salida, resumen = root / "out.txt", root / "sum.md"
        salida.write_text(""), resumen.write_text("")
        for k in ("herramientas", "ddd_core", "configuracion"):
            if not (root / k).exists():
                (root / k).symlink_to(ROOT / k)
        e = {**os.environ, "PATH": f"{bindir}:{os.environ['PATH']}", "GITHUB_OUTPUT": str(salida), "GITHUB_STEP_SUMMARY": str(resumen),
             "GITHUB_REPOSITORY": "o/r", "GH_TOKEN": "x", "QUE": "", "TERRITORIOS": "", "SIMULAR": "", "RUN_IDS": ""}
        e.update(env)
        r = subprocess.run(["bash", "-eo", "pipefail", "-c", paso_r["run"]], cwd=root, env=e, capture_output=True, text=True)
        out = dict(l.split("=", 1) for l in salida.read_text().splitlines() if "=" in l)
        return r, out

    def gh_falso(self, tmp, cuerpo="echo 0"):
        b = Path(tmp) / "bin"
        b.mkdir(exist_ok=True)
        (b / "gh").write_text(f"#!/bin/bash\n{cuerpo}\n")
        (b / "gh").chmod(0o755)
        return b

    def test_m06_caducado_no_bloquea_publicar_el_visor(self):
        # Todos los artefactos de Actions caducados (gh devuelve 0 coincidencias vivas): el M06 sale del blob del registro (D-133).
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registro_00(root, "aut01", "500")
            r, out = self.ejecutar(root, self.gh_falso(tmp), QUE="Territorios", TERRITORIOS="aut01", SIMULAR="false")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual((out["production_run_id"], out["publicar"]), ("500", "true"))
            self.assertNotIn("M06", r.stdout + r.stderr)
            self.assertIn("M08_ARTEFACTO_CADUCADO=ddd-state-500-04", r.stdout)  # solo aviso

    def test_00_mas_recientes_descartadas_avisan_y_van_a_la_tabla(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registro_00(root, "aut01", "100")
            registro_00(root, "aut01", "300", ok04=False)
            registro_00(root, "aut01", "400", ok=False)
            r, out = self.ejecutar(root, self.gh_falso(tmp), QUE="Territorios", TERRITORIOS="aut01", SIMULAR="true")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(out["production_run_id"], "100")
            self.assertIn("::warning::P40_00_DESCARTADA aut01: 00 400 (EJECUCION_00_NO_SUCCESS=FAILED", r.stdout)
            self.assertIn("::warning::P40_00_DESCARTADA aut01: 00 300 (PUERTA_04_NO_VALIDADA", r.stdout)
            tabla = (root / "sum.md").read_text()
            self.assertIn("| aut01 | 100 | 100 |", tabla)
            self.assertIn("400: EJECUCION_00_NO_SUCCESS=FAILED", tabla)
            registro_00(root, "aut02", "200")
            r, out = self.ejecutar(root, self.gh_falso(tmp), QUE="Territorios", TERRITORIOS="aut02", SIMULAR="true")
            self.assertNotIn("DESCARTADA", r.stdout)
            self.assertIn("| aut02 | 200 | 200 | — |", (root / "sum.md").read_text())

    def test_simular_vacio_desde_workflow_call_es_no_simulado(self):
        # La 00 llama por workflow_call sin `simular`: llega vacío y se publica (solo el valor `true` simula). Sin probar en Actions.
        self.assertIn('publicar=true; [[ "$SIMULAR" != true ]] || publicar=false', self.txt)
        self.assertIn("vacío = no simulado", self.txt)
        with tempfile.TemporaryDirectory() as tmp:
            r, out = self.ejecutar(Path(tmp), self.gh_falso(tmp), SIMULAR="", RUN_IDS="9")
            self.assertEqual((r.returncode, out["publicar"]), (0, "true"))

    def test_simular_resuelve_y_no_publica(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registro_00(root, "aut01", "500")
            r, out = self.ejecutar(root, self.gh_falso(tmp, "echo 1"), QUE="Territorios", TERRITORIOS="aut01", SIMULAR="true")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual((out["production_run_id"], out["publicar"]), ("500", "false"))
            self.assertIn("Simulación: no se publica nada.", (root / "sum.md").read_text())

    def test_solo_el_sitio_sin_run_y_llamada_de_la_00(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            r, out = self.ejecutar(root, self.gh_falso(tmp), QUE="Solo el sitio", SIMULAR="false")
            self.assertEqual((r.returncode, out["production_run_id"], out["publicar"]), (0, "", "true"))
            r, out = self.ejecutar(root, Path(tmp) / "bin", RUN_IDS="43 44")  # workflow_call (la 00)
            self.assertEqual((r.returncode, out["production_run_id"], out["publicar"]), (0, "43 44", "true"))

    def test_fallos_cerrados(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registro_00(root, "aut01", "500", ok04=False)
            b = self.gh_falso(tmp)
            for env, cod in [
                (dict(QUE="Territorios", TERRITORIOS="aut01"), "P40_SIN_00_VALIDA"),
                (dict(QUE="Territorios", TERRITORIOS=""), "P40_TERRITORIOS_VACIO"),
                (dict(QUE="Territorios", TERRITORIOS="zzz"), "P40_TERRITORIO_DESCONOCIDO"),
                (dict(QUE="Solo el sitio", TERRITORIOS="aut01"), "P40_TERRITORIOS_CON_SOLO_SITIO"),
                (dict(QUE="Territorios", TERRITORIOS="aut01", RUN_IDS="5"), "P40_RUN_ID_CON_TERRITORIOS"),
            ]:
                r, out = self.ejecutar(root, b, **env)
                self.assertNotEqual(r.returncode, 0, env)
                self.assertIn(cod, r.stderr + r.stdout, env)
                self.assertEqual(out, {}, env)  # nada se escribe en GITHUB_OUTPUT: preparar y publicar no arrancan


class Resolutor(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(ROOT / "herramientas"))
        import p40_resolver
        self.m = p40_resolver

    def test_toma_la_ultima_00_valida_y_el_run_origen_de_reutilizar(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registro_00(root, "aut01", "100")
            registro_00(root, "aut01", "300", ok04=False)  # más reciente pero sin puerta 04
            registro_00(root, "aut01", "250", repo="240")  # «Reutilizar»: publica el run origen de la 04
            registro_00(root, "aut01", "400", ok=False)    # no SUCCESS
            r = self.m.territorios(root, "aut01")
            self.assertEqual(r["production_run_ids"], "240")
            self.assertEqual(r["territorios"][0]["run_00"], "250")

    def test_varios_territorios_todo_o_nada_y_sin_repetidos(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registro_00(root, "aut01", "100")
            registro_00(root, "aut02", "200")
            self.assertEqual(self.m.territorios(root, "aut02, aut01 aut02")["production_run_ids"], "200 100")
            with self.assertRaisesRegex(ValueError, "P40_SIN_00_VALIDA: aut03"):
                self.m.territorios(root, "aut01,aut03")

    def test_rechaza_invalidos_y_variantes_350(self):
        with tempfile.TemporaryDirectory() as tmp:
            for malo, cod in [("", "P40_TERRITORIOS_VACIO"), ("aut01;x", "P40_TERRITORIO_INVALIDO"), ("zzz", "P40_TERRITORIO_DESCONOCIDO")]:
                with self.assertRaisesRegex(ValueError, cod):
                    self.m.territorios(Path(tmp), malo)

    def test_cli_help_rc0_y_errores_a_stderr(self):
        h = subprocess.run([sys.executable, str(ROOT / "herramientas" / "p40_resolver.py"), "--help"], capture_output=True, text=True)
        self.assertEqual(h.returncode, 0)
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([sys.executable, str(ROOT / "herramientas" / "p40_resolver.py"), "territorios", "--root", tmp, "--territorios", "aut01"],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertEqual(r.stdout, "")
            self.assertIn("::error::P40_SIN_00_VALIDA", r.stderr)


if __name__ == "__main__":
    unittest.main()
