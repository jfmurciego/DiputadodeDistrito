"""T-379 PR 3b: P10 1.0.2 y P20 1.0.2 con el registro en ensayo (opción A del Planificador, 19-11).

- Sin campaña, idénticos a la 1.0.1: `tests/_t379_3b.deshacer(actual)` == copia congelada (sha256 abajo).
- Con campaña, cada job de registro de la lista cerrada de la 2b: la credencial de la app se salta; «Registro en ensayo
  (campaña)» va justo después y ANTES de cualquier paso que registre (así ningún push sale a GitHub); «Capturar el registro
  (campaña)» es el último paso; el orden de re-aplicación crece en la cadena; los grupos globales pasan a uno por campaña
  y territorio. Los bloques de shell del ensayo y la captura se ejecutan bajo `bash -eo pipefail` con git y almacén locales.
Cada regla con su control negativo.
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

from tests._t379_3b import CAPTURA, ENSAYO, JOBS, SOLO_SIN_CAMPANA, deshacer
from tests._uses_sin_version import cargar
from tests.test_t379_2b_campana import REGISTRO, paralelos, ruta_de_campana, RAMA_P10

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
FIX = ROOT / "tests" / "fixtures" / "t379_3b_workflows"
HUELLAS = {
    "p10-fuentes": "67ae63df4b96cabe5ecd27ab0e368974c9ff8663806a1a9bfa5dc889b13e6e1c",
    "p20-distritos": "c787e3bcdced5d22f12194fc59feb9b3d75bb3dcf838e67b6862a0a0896a1732",
    "p30-resultados-electorales": "0bb36d8cd475d38dd755474e80e8a2de863a7afeca8e2caac0899c568a8bc77b",
}
VERSION_CONGELADA = {"p10-fuentes": "1.0.1", "p20-distritos": "1.0.1", "p30-resultados-electorales": "1.0.3"}
# Pares que el grafo deja en paralelo pero las condiciones excluyen: pre_m04_diagnostic solo corre con
# `preflight_only == 'true'` (P20 acreditar) y m04…registrar solo sin él (P20 generar).
EXCLUYENTES_P20 = {("auditoria", "pre_m04_diagnostic"), ("m04", "pre_m04_diagnostic"), ("m05", "pre_m04_diagnostic"),
                   ("m06", "pre_m04_diagnostic"), ("pre_m04_diagnostic", "registrar")}


def leer(n):
    return cargar((WF / f"{n}.yml").read_text(encoding="utf-8"))


def pasos(doc, job):
    return doc["jobs"][job]["steps"]


def orden_de(run):
    return int(re.search(r"--(?:antes|orden) (\d+)", run).group(1))


class Equivalencia(unittest.TestCase):
    def test_copias_congeladas(self):
        for n, sha in HUELLAS.items():
            self.assertEqual(hashlib.sha256((FIX / f"{n}_{VERSION_CONGELADA[n]}.yml").read_bytes()).hexdigest(), sha, n)

    def test_sin_campana_igual_que_la_1_0_1(self):
        for n in HUELLAS:
            with self.subTest(workflow=n):
                antes = cargar((FIX / f"{n}_{VERSION_CONGELADA[n]}.yml").read_text(encoding="utf-8"))
                self.assertEqual(deshacer(n, leer(n)), antes)

    def test_control_negativo(self):
        d = leer("p10-fuentes")
        pasos(d, "p11_registrar")[0]["with"]["ref"] = "main"
        self.assertNotEqual(deshacer("p10-fuentes", d), cargar((FIX / "p10-fuentes_1.0.1.yml").read_text(encoding="utf-8")))


class ConCampana(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = {n: leer(n) for n in HUELLAS}

    def test_cada_registro_en_ensayo_antes_de_registrar(self):
        for n, jobs in JOBS.items():
            for j in jobs:
                with self.subTest(job=(n, j)):
                    job = self.docs[n]["jobs"][j]
                    self.assertNotIn("!inputs.campana", job["if"])
                    nombres = [s.get("name") for s in job["steps"]]
                    cred = nombres.index("Credencial de registro")
                    self.assertEqual(job["steps"][cred]["if"], SOLO_SIN_CAMPANA)
                    self.assertEqual(nombres[cred + 1], ENSAYO)
                    self.assertEqual(job["steps"][cred + 1]["if"], "${{ inputs.campana }}")
                    primer_registro = min(i for i, s in enumerate(job["steps"])
                                          if s.get("name") not in (ENSAYO, CAPTURA) and REGISTRO.search(yaml.safe_dump(s))
                                          and "DDD_REGISTRO_APP" not in yaml.safe_dump(s))
                    self.assertGreater(primer_registro, cred + 1)
                    self.assertEqual(nombres[-1], CAPTURA)
                    self.assertEqual(job["steps"][-1]["if"], "${{ success() && inputs.campana }}")
                    self.assertEqual(orden_de(job["steps"][cred + 1]["run"]), orden_de(job["steps"][-1]["run"]))

    def test_el_orden_crece_en_la_cadena(self):
        ordenes = [orden_de(next(s for s in pasos(self.docs[n], j) if s.get("name") == ENSAYO)["run"])
                   for n, jobs in JOBS.items() for j in jobs]
        self.assertEqual(ordenes, sorted(set(ordenes)))
        self.assertEqual(ordenes, [10, 11, 12, 20, 21, 22])

    def test_sin_grupos_globales_con_campana(self):
        for n, jobs in JOBS.items():
            for j in jobs:
                g = (self.docs[n]["jobs"][j].get("concurrency") or {}).get("group", "")
                if g:
                    self.assertTrue(g.startswith("${{ inputs.campana && format('ddd-campana-"), (n, j, g))

    def test_p10_ya_no_fuerza_sin_persistencia(self):
        envs = [s["env"]["PERSIST_INPUT"] for j in ("p11_resolver", "p12_resolver")
                for s in pasos(self.docs["p10-fuentes"], j) if "PERSIST_INPUT" in (s.get("env") or {})]
        self.assertEqual(envs, ["${{ toJSON(inputs.persist_state) }}"] * 2)

    def test_checkout_del_pending_con_campana(self):
        ref = pasos(self.docs["p10-fuentes"], "p11_generation_pending")[0]["with"]["ref"]
        self.assertEqual(ref, "${{ inputs.campana && github.sha || needs.p11_registrar.outputs.promotion_sha }}")

    def test_solo_lectura(self):
        for n, d in self.docs.items():
            self.assertEqual(d["permissions"], {"contents": "read", "actions": "read"}, n)
            for j, job in d["jobs"].items():
                for v in (job.get("permissions") or {}).values():
                    self.assertEqual(v, "read", (n, j))

    def test_serie(self):
        self.assertEqual(set(paralelos(ruta_de_campana(self.docs["p20-distritos"]))), EXCLUYENTES_P20)
        for prefijo in RAMA_P10.values():
            self.assertEqual(paralelos(ruta_de_campana(self.docs["p10-fuentes"], prefijo)), [])
        d = copy.deepcopy(self.docs["p20-distritos"])
        d["jobs"]["registrar"]["needs"] = ["entrada", "resolve"]  # control negativo: registrar en paralelo con el motor
        self.assertIn(("m06", "registrar"), paralelos(ruta_de_campana(d)))


class P30EnEnsayo(unittest.TestCase):
    """P30 1.0.4: los pasos de registro de `incorporar` corren con campaña, en ensayo; la credencial sigue saltada y el M06
    no se retira aquí (lo hace el cierre por territorio)."""

    @classmethod
    def setUpClass(cls):
        cls.pasos = pasos(leer("p30-resultados-electorales"), "incorporar")
        cls.nombres = [s.get("name") for s in cls.pasos]

    def paso(self, nombre):
        return self.pasos[self.nombres.index(nombre)]

    def test_orden_y_condiciones(self):
        cred = self.nombres.index("Credencial de registro")
        self.assertTrue(self.paso("Credencial de registro")["if"].endswith(" && !inputs.campana }}"))
        self.assertEqual(self.nombres[cred + 1], ENSAYO)
        self.assertEqual(self.nombres[-1], CAPTURA)
        for n in ("Doble vuelta con coaliciones (D-171; no fatal)", "Cargar persistidor vigente compatible con main",
                  "Archivo en origen — M08 a R2 y votos por partido a git", "Registrar disponibilidad del producto electoral"):
            self.assertNotIn("inputs.campana", self.paso(n)["if"], n)
        self.assertGreater(self.nombres.index("Archivo en origen — M08 a R2 y votos por partido a git"), cred + 1)
        self.assertEqual(orden_de(self.paso(ENSAYO)["run"]), 30)
        self.assertEqual(orden_de(self.pasos[-1]["run"]), 30)
        for n in (ENSAYO, CAPTURA):
            self.assertIn("--rama main", self.paso(n)["run"])  # P30 registra en main con --rama/--target-branch main
            self.assertEqual(self.paso(n)["working-directory"], "persistidor")

    def test_persistidor_de_la_version_de_campana(self):
        self.assertEqual(self.paso("Cargar persistidor vigente compatible con main")["with"]["ref"],
                         "${{ inputs.campana && github.sha || 'main' }}")

    def test_sin_retirada_del_m06_con_campana(self):
        run = self.paso("Archivo en origen — M08 a R2 y votos por partido a git")["run"]
        linea = next(l for l in run.splitlines() if l.startswith("sustituye="))
        for campana, esperado in (("", "123"), ("900", "")):
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", linea + '\nprintf %s "$sustituye"'], capture_output=True,
                               text=True, env={**os.environ, "CAMPANA": campana, "TERRITORIAL_RUN_ID": "123"})
            self.assertEqual((r.returncode, r.stdout), (0, esperado), campana)
        self.assertIn('--sustituye-m06-run "$sustituye"', run)


class Bloques(unittest.TestCase):
    """«Registro en ensayo» y «Capturar el registro» de P20 `registrar`, ejecutados en un clon local."""

    def test_ensayo_y_captura(self):
        sys.path.insert(0, str(ROOT / "herramientas"))
        import campana_estado as ce
        job = leer("p20-distritos")["jobs"]["registrar"]
        bloque_ensayo = next(s for s in job["steps"] if s.get("name") == ENSAYO)["run"]
        bloque_captura = job["steps"][-1]["run"]
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            g = lambda cwd, *a: subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a], cwd=cwd,
                                               check=True, capture_output=True, text=True).stdout.strip()
            orig = td / "orig"
            orig.mkdir()
            g(orig, "init", "-q", "-b", "main")
            (orig / "datos").mkdir()
            (orig / "datos" / "a.json").write_text('{"x": 1}\n')
            g(orig, "add", "-A")
            g(orig, "commit", "-qm", "base")
            work = td / "work"
            g(td, "clone", "-q", "--depth", "1", f"file://{orig}", str(work))
            (work / "herramientas").symlink_to(ROOT / "herramientas")
            (work / "ddd_core").symlink_to(ROOT / "ddd_core")
            (work / ".github").symlink_to(ROOT / ".github")
            salida = td / "salida"
            salida.write_text("")
            env = {**os.environ, "ALMACEN": f"dir:{td / 'alm'}", "CAMPANA": "900", "CAMPANA_TERRITORIO": "aut11",
                   "RUNNER_TEMP": str(td), "GITHUB_REF_NAME": "main", "GITHUB_OUTPUT": str(salida), "GITHUB_RUN_ATTEMPT": "1"}
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", bloque_ensayo], cwd=work, env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            base = salida.read_text().split("base=", 1)[1].strip()
            (work / "datos" / "a.json").write_text('{"x": 1, "y": 2}\n')
            g(work, "commit", "-qam", "registro")
            g(work, "push", "-q", "origin", "HEAD:refs/heads/main")
            self.assertEqual(g(orig, "rev-list", "--count", "main"), "1")  # el remoto «real» no recibe nada
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", bloque_captura], cwd=work, env={**env, "BASE": base},
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            cap = json.loads(ce.AlmacenLocal(td / "alm").leer("campanas/900/registro/aut11/22-registrar/1.json"))
            self.assertEqual(cap["entradas"], [{"ruta": "datos/a.json", "tipo": "json",
                                                "delta": [{"claves": ["y"], "valor": 2}]}])
            # control negativo: sin ensayo (origin real) la captura se niega
            g(work, "remote", "set-url", "origin", str(orig))
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", bloque_captura], cwd=work, env={**env, "BASE": base},
                               capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("CAPTURA_SIN_ENSAYO", r.stderr)


if __name__ == "__main__":
    unittest.main()


class PublicarEnCampana(unittest.TestCase):
    """G4 (Planificador, 19-11): publicar exige el permiso del propietario; una frase D-52 no aprueba `produccion`."""

    def test_p40_pide_produccion_tambien_desde_p00(self):
        env = yaml.safe_load((WF / "p40-publicacion.yml").read_text(encoding="utf-8"))["jobs"]["preparar"]["environment"]
        self.assertIn("contains(github.workflow_ref, '/.github/workflows/p00-campana.yml@')", env)
        self.assertIn("github.workflow == 'P40 Publicación'", env)
        self.assertTrue(env.endswith("&& 'produccion' || '' }}"))

    def test_por_defecto_no_se_publica(self):
        p00 = yaml.safe_load((WF / "p00-campana.yml").read_text(encoding="utf-8"))
        entrada = p00[True]["workflow_dispatch"]["inputs"]["publicar"]
        self.assertEqual(entrada["default"], "no")
        sem = next(s for s in p00["jobs"]["comprobar"]["steps"] if s.get("id") == "semaforo")
        self.assertEqual(sem["env"]["PUBLICAR"], "${{ inputs.publicar == 'sí' }}")  # «no» → false → sin --publicar
        self.assertIn('[[ "$PUBLICAR" == true ]] && args+=(--publicar)', sem["run"])
        self.assertIn("needs.comprobar.outputs.publicar == 'true'", p00["jobs"]["publicar"]["if"])
        sys.path.insert(0, str(ROOT / "herramientas"))
        import campana_estado as ce
        self.assertIs(ce.comprobar("nac22", "vigente", publicar=False)["publicar"], False)
        self.assertIs(ce.comprobar("nac22", "vigente", publicar=True)["publicar"], True)  # control negativo
