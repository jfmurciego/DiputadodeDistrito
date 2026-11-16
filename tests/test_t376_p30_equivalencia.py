# -*- coding: utf-8 -*-
"""T-376 (D-137, paso 7): P30 Resultados electorales sustituye a `incorporacion-resultados-electorales.yml` y `_reutilizable-incorporacion-electoral.yml`.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-16 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
La equivalencia se calcula contra COPIAS CONGELADAS (`tests/fixtures/t376_workflows/`, con sha256; en CI no hay `legacy/`). Si falta una o cambia su huella
el test FALLA (no se salta). Controles negativos: un comando, permiso, concurrencia o paso cambiados se detectan.
"""
import copy
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
FIX = ROOT / "tests" / "fixtures" / "t376_workflows"
SHAS = {
    "incorporacion-resultados-electorales_2.0.8.yml": "0c1a54077d9381a23570460c47a29eb05d6734d371d248b7d8a1a2c121351509",
    "reutilizable-incorporacion-electoral_1.3.0.yml": "af38b29e600687b26a51e28180ae4cc15d3738b3bf0083baafa5797ba7adfbeb",
}
# Únicas sustituciones permitidas: las entradas de los dos workflows viejos pasan a salidas del resolutor, a salidas de pasos o al contexto fijado.
SUST_PREPARAR = [
    ("${{ inputs.territory_id }}", "${{ needs.resolver.outputs.territorio }}"),
    ("${{ inputs.data_edition }}", "${{ needs.resolver.outputs.edicion }}"),
]
SUST_INCORPORAR = [
    ("inputs.territorial_product_artifact_name", "steps.territorial.outputs.product_artifact_name"),
    ("inputs.territorial_audit_artifact_name", "steps.territorial.outputs.audit_artifact_name"),
    ("inputs.territorial_run_id", "steps.territorial.outputs.run_id"),
    ("inputs.electoral_package_artifact_name", "steps.electoral.outputs.artifact_name"),
    ("inputs.electoral_package_run_id", "steps.electoral.outputs.run_id"),
    ("inputs.artifact_namespace", "env.ARTIFACT_NAMESPACE"),
]
SUST_REGISTRAR = [("${{ needs.incorporar.outputs.source_commit }}", "${{ steps.capture_source.outputs.source_commit }}")]
CLAVES_NUEVAS_REGISTRAR = {"if", "working-directory", "env"}
PASOS_REGISTRAR = ["Cargar persistidor vigente compatible con main", "Credencial de registro",
                   "Archivo en origen — M08 a R2 y votos por partido a git", "Registrar disponibilidad del producto electoral"]
R2 = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION", "R2_ACCOUNT_ID", "R2_BUCKET"]


def on(d):
    return d.get("on") or d.get(True)


def cargar(nombre, base=FIX):
    return yaml.safe_load((base / nombre).read_text(encoding="utf-8"))


def sustituir(obj, sust):
    t = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    for a, b in sust:
        t = t.replace(json.dumps(a)[1:-1], json.dumps(b)[1:-1])
    return json.loads(t)


def paso(job, nombre):
    return next(s for s in job["steps"] if s.get("name") == nombre or s.get("id") == nombre)


def nombres(job):
    return [s.get("name") for s in job["steps"]]


class Fixtures(unittest.TestCase):
    def test_huellas(self):
        for n, sha in SHAS.items():
            p = FIX / n
            self.assertTrue(p.is_file(), f"falta la copia congelada {n}")
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), sha, n)

    def test_ficheros_viejos_borrados_y_nuevo_presente(self):
        self.assertFalse((WF / "incorporacion-resultados-electorales.yml").exists())
        self.assertFalse((WF / "_reutilizable-incorporacion-electoral.yml").exists())
        self.assertTrue((WF / "p30-resultados-electorales.yml").is_file())


class Equivalencia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nuevo = yaml.safe_load((WF / "p30-resultados-electorales.yml").read_text(encoding="utf-8"))
        cls.viejo = cargar("incorporacion-resultados-electorales_2.0.8.yml")
        cls.reut = cargar("reutilizable-incorporacion-electoral_1.3.0.yml")
        cls.job = cls.nuevo["jobs"]["incorporar"]

    # --- pasos de `preparar` (workflow viejo)
    def comparar_preparar(self, viejo, job):
        for s in viejo["jobs"]["preparar"]["steps"]:
            n = s.get("name") or s.get("id") or s["uses"]
            nuevo = paso(job, s.get("name") or s.get("id")) if (s.get("name") or s.get("id")) else job["steps"][0]
            self.assertEqual(sustituir(s, SUST_PREPARAR), nuevo, f"preparar · {n}")

    def test_preparar_identico_salvo_entradas(self):
        self.comparar_preparar(self.viejo, self.job)

    # --- pasos de `incorporar` (reutilizable): idénticos salvo el checkout y el pip duplicados
    def pasos_incorporar(self, reut):
        pasos = reut["jobs"]["incorporar"]["steps"]
        return [s for s in pasos if not (s.get("uses", "").startswith("actions/checkout@"))
                and s.get("name") != "Preparar herramientas ligeras de validación"]

    def comparar_incorporar(self, reut, job):
        previos = [s.get("name") for s in reut["jobs"]["incorporar"]["steps"]]
        self.assertIn("Preparar herramientas ligeras de validación", previos)
        for s in self.pasos_incorporar(reut):
            esperado = sustituir(s, SUST_INCORPORAR)
            nuevo = next((x for x in job["steps"] if x == esperado), None)
            self.assertIsNotNone(nuevo, f"incorporar · paso distinto o ausente: {s.get('name') or s.get('uses')}")

    def test_incorporar_identico_salvo_entradas(self):
        self.comparar_incorporar(self.reut, self.job)

    def test_orden_de_los_pasos(self):
        n = nombres(self.job)
        orden = ["Verificar elegibilidad del territorio", "Localizar producto territorial certificado", "Localizar resultados electorales preparados",
                 "Fijar el contexto de la incorporación", "Acreditar SHA efectivo del checkout de incorporación M08",
                 "Generar producto electoral territorial", "Generar informe de incorporación"] + PASOS_REGISTRAR
        pos = [n.index(x) for x in orden]
        self.assertEqual(pos, sorted(pos))

    # --- pasos de `registrar`: mismo comando; solo se añaden `if`, `working-directory`, `env` y `path` del checkout
    def test_registrar_identico_salvo_contexto(self):
        reg = self.reut["jobs"]["registrar"]
        base = [s for s in reg["steps"] if s.get("name") in PASOS_REGISTRAR]
        self.assertEqual([s["name"] for s in base], PASOS_REGISTRAR)
        env_job = reg["env"]
        for s in base:
            nuevo = paso(self.job, s["name"])
            viejo = sustituir(s, SUST_REGISTRAR)
            esperado = {k: v for k, v in viejo.items() if k not in CLAVES_NUEVAS_REGISTRAR}
            if "with" in esperado:
                esperado["with"] = {**esperado["with"], "path": "persistidor"}
            self.assertEqual({k: v for k, v in nuevo.items() if k not in CLAVES_NUEVAS_REGISTRAR}, esperado, s["name"])
            propio = {k: v for k, v in nuevo.get("env", {}).items() if k not in R2 and k != "PRODUCT_DIGEST"}
            self.assertEqual(propio, viejo.get("env", {}), s["name"])
            self.assertEqual(nuevo["if"], "${{ success() && needs.resolver.outputs.persistir == 'true' }}", s["name"])
            if s["name"] != PASOS_REGISTRAR[0]:
                self.assertEqual(nuevo["working-directory"], "persistidor", s["name"])
        # los secretos y variables de R2 del job viejo viajan en los dos pasos que los usaban (y no en el job: no se ensanchan)
        for n in PASOS_REGISTRAR[2:]:
            e = paso(self.job, n)["env"]
            for k in R2:
                self.assertEqual(e[k], env_job[k], (n, k))
        for k in R2:
            self.assertNotIn(k, self.job.get("env", {}))
        self.assertEqual(paso(self.job, PASOS_REGISTRAR[3])["env"]["PRODUCT_DIGEST"], "${{ steps.upload_product.outputs.artifact-digest }}")
        self.assertEqual(env_job["PRODUCT_DIGEST"], "${{ needs.incorporar.outputs.product_digest }}")
        self.assertEqual(self.reut["jobs"]["incorporar"]["outputs"]["product_digest"], "${{ steps.upload_product.outputs.artifact-digest }}")

    def test_registro_solo_con_persistir_y_tras_exito(self):
        self.assertEqual(self.reut["jobs"]["registrar"]["if"], "${{ needs.incorporar.result == 'success' && inputs.persist_state }}")
        for n in PASOS_REGISTRAR:
            self.assertIn("success()", paso(self.job, n)["if"])
            self.assertIn("persistir == 'true'", paso(self.job, n)["if"])

    # --- permisos, concurrencia, tiempos, salidas
    def test_permisos(self):
        self.assertEqual(self.nuevo["permissions"], self.viejo["permissions"])
        self.assertEqual(self.nuevo["permissions"], self.reut["permissions"])
        self.assertEqual(self.nuevo["permissions"], {"contents": "write", "actions": "read"})
        self.assertEqual(self.nuevo["jobs"]["resolver"]["permissions"], {"contents": "read"})  # un job que solo resuelve gana menos, no más
        self.assertNotIn("permissions", self.job)
        for j in self.nuevo["jobs"].values():
            self.assertNotIn("id-token", j.get("permissions", {}))

    def test_concurrencia_por_territorio(self):
        v = self.viejo["concurrency"]
        c = self.job["concurrency"]
        self.assertEqual(c["group"], v["group"].replace("inputs.territory_id", "needs.resolver.outputs.territorio"))
        self.assertEqual((c["cancel-in-progress"], c["queue"]), (v["cancel-in-progress"], v["queue"]))
        self.assertNotIn("concurrency", self.nuevo)
        self.assertFalse(self.nuevo["jobs"]["resolver"].get("concurrency"))
        self.assertNotIn("ddd-catalog-promotion", (WF / "p30-resultados-electorales.yml").read_text(encoding="utf-8"))

    def test_tiempo_y_entorno(self):
        self.assertGreaterEqual(self.job["timeout-minutes"], self.reut["jobs"]["incorporar"]["timeout-minutes"])
        self.assertNotIn("environment", self.job)
        self.assertEqual(self.job["env"]["RUN_ID"], self.reut["jobs"]["incorporar"]["env"]["RUN_ID"])
        self.assertNotIn("strategy", self.job)  # D-148: un territorio por ejecución, sin matriz
        self.assertEqual(self.job["runs-on"], self.reut["jobs"]["incorporar"]["runs-on"])

    def test_entradas_un_solo_territorio(self):
        wc = on(self.nuevo)["workflow_call"]["inputs"]
        viejas = on(self.viejo)["workflow_call"]["inputs"]
        self.assertEqual(set(wc), set(viejas))
        for k, v in viejas.items():
            self.assertEqual(wc[k]["type"], v["type"], k)
        self.assertEqual(wc["data_edition"]["default"], "")
        self.assertTrue(wc["territory_id"]["required"])
        wd = on(self.nuevo)["workflow_dispatch"]["inputs"]
        self.assertEqual(list(wd), ["territorio"])
        self.assertEqual(wd["territorio"]["type"], "string")
        codigo = "\n".join(l for l in (WF / "p30-resultados-electorales.yml").read_text(encoding="utf-8").split("\n") if not l.lstrip().startswith("#"))
        self.assertNotIn("fromJSON", codigo)
        self.assertNotIn("matrix", codigo)

    def test_el_boton_no_expone_parametros_tecnicos(self):
        wd = on(self.nuevo)["workflow_dispatch"]["inputs"]
        for k in ("data_edition", "territory_id", "source_ref", "persist_state", "artifact_namespace", "electoral_package_run_id"):
            self.assertNotIn(k, wd)
        self.assertEqual(self.nuevo["name"], "P30 Resultados electorales")

    def test_nombres_de_artefactos_con_espacio_de_nombres(self):
        texto = (WF / "p30-resultados-electorales.yml").read_text(encoding="utf-8")
        self.assertEqual(texto.count("env.ARTIFACT_NAMESPACE != ''"), 4)  # M07, M08, certificación e informe
        self.assertNotIn("inputs.artifact_namespace != ''", texto)

    def test_llamada_de_la_00(self):
        oo = yaml.safe_load((WF / "ejecucion-completa-proyecto.yml").read_text(encoding="utf-8"))
        inc = oo["jobs"]["incorporar"]
        self.assertEqual(inc["uses"], "./.github/workflows/p30-resultados-electorales.yml")
        self.assertEqual(inc["secrets"], "inherit")
        self.assertLessEqual(set(inc["with"]), set(on(self.nuevo)["workflow_call"]["inputs"]))

    # --- controles negativos: el comparador detecta cambios
    def test_control_negativo_comando(self):
        j = copy.deepcopy(self.job)
        paso(j, "Generar producto electoral territorial")["run"] += "\necho x"
        with self.assertRaises(AssertionError):
            self.comparar_incorporar(self.reut, j)

    def test_control_negativo_paso_de_preparar(self):
        j = copy.deepcopy(self.job)
        paso(j, "territorial")["env"]["GH_TOKEN"] = "x"
        with self.assertRaises(AssertionError):
            self.comparar_preparar(self.viejo, j)

    def test_control_negativo_paso_ausente(self):
        j = copy.deepcopy(self.job)
        j["steps"] = [s for s in j["steps"] if s.get("name") != "Conservar producto electoral territorial"]
        with self.assertRaises(AssertionError):
            self.comparar_incorporar(self.reut, j)

    def test_control_negativo_sustituciones_cubren_todo(self):
        # sin la sustitución, el paso viejo difiere del nuevo: la tabla de sustituciones es necesaria y se comprueba
        s = next(x for x in self.reut["jobs"]["incorporar"]["steps"] if x.get("with", {}).get("run-id"))
        self.assertNotEqual(s, paso(self.job, s["name"]))


class Resolutor(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "herramientas" / "p30_resolver.py"), *args], capture_output=True, text=True, cwd=ROOT)

    def test_help(self):
        self.assertEqual(self.run_cli("--help").returncode, 0)
        self.assertEqual(self.run_cli("resolver", "--help").returncode, 0)

    def test_boton_un_territorio(self):
        r = self.run_cli("resolver", "--territorio", "aut12")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout), {"territorio": "Galicia", "edicion": "2025", "persistir": "true"})
        self.assertEqual(json.loads(self.run_cli("resolver", "--territorio", "NAC42").stdout)["territorio"], "Congreso Soria")

    def test_historico_por_epoca(self):
        d = json.loads(self.run_cli("resolver", "--territorio", "nac22_h2019_11").stdout)
        self.assertEqual(d["territorio"], "nac22_h2019_11")
        for malo in ("nac22_h2030_01", "congreso350_zamora_h2019_11", "zz99_h2019_11", "nac22_h2019_1", "nac22_H2019_11x"):
            r = self.run_cli("resolver", "--territorio", malo)
            self.assertEqual((r.returncode, r.stdout), (1, ""), malo)
            self.assertIn("::error::P30_", r.stderr, malo)

    def test_llamada_tal_cual_y_persistir(self):
        d = json.loads(self.run_cli("resolver", "--territory-id", "Congreso 350 Zamora", "--persistir", "false", "--edicion", "").stdout)
        self.assertEqual(d, {"territorio": "Congreso 350 Zamora", "edicion": "2025", "persistir": "false"})
        self.assertEqual(json.loads(self.run_cli("resolver", "--territory-id", "x", "--persistir", "null").stdout)["persistir"], "true")

    def test_fallos_cerrados_a_stderr(self):
        for args in (["--territorio", ""], ["--territorio", "zz99"], ["--territorio", "congreso350_zamora"], ["--territorio", "congreso_alava"],
                     ["--territorio", "galicia"], ["--territorio", "aut12,nac42"], ["--territorio", "aut12 nac42"], ["--territorio", "a b!"],
                     ["--territorio", "aut12", "--territory-id", "x"], ["--territory-id", "x", "--persistir", "quizá"], []):
            r = self.run_cli("resolver", *args)
            self.assertEqual(r.returncode, 1, args)
            self.assertEqual(r.stdout, "", args)
            self.assertIn("::error::P30_", r.stderr, args)
        self.assertIn("P30_UN_TERRITORIO", self.run_cli("resolver", "--territorio", "aut12,nac42").stderr)


if __name__ == "__main__":
    unittest.main()
