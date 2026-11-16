# -*- coding: utf-8 -*-
"""T-368 (D-131/D-132): P70 Archivo sustituye a `podar-r2.yml`, `recuperar-producto-electoral-durable.yml` y `mantenimiento-programado.yml`
sin cambiar comandos, permisos, entornos ni concurrencia.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-16 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
La equivalencia se calcula contra COPIAS CONGELADAS (`tests/fixtures/t368_workflows/`, con sha256; en CI no hay `legacy/`). Si falta una copia
o cambia su huella el test FALLA (no se salta). Los controles negativos comprueban que un permiso, una concurrencia, un paso o un entorno
cambiados se detectan.
"""
import copy
import hashlib
import re
import subprocess
import unittest
from pathlib import Path

import yaml

from tests._uses_sin_version import cargar as cargar_sin_version

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
FIX = ROOT / "tests" / "fixtures" / "t368_workflows"
HUELLAS = {
    "mant": ("mantenimiento-programado_1.1.0.yml", "1e60300ecb655253bc4707b8d286fb20dd1b4b6a52353b10e1e5ecc50b3d0146"),
    "podar": ("podar-r2_1.0.1.yml", "3b252196a71982bcb0c03abbaf98c54112bfc556867dd228dfa663e9f0aa9ddd"),
    "rec": ("recuperar-producto-electoral-durable_1.0.5.yml", "8fe5a41b10a24957116c80147d28a04e0c7414bbc9df75c910d26cb7a71c351e"),
}
A_TODO, A_P10 = "P71 Archivar todo lo vivo", "P71 Archivar paquete de fuentes de un territorio"
A_PROD, A_COMP = "P72 Recuperar producto electoral", "P72 Recuperar composición M06"
A_PODA, A_LIST = "P73 Podar", "P74 Listar"
ACCIONES = [A_TODO, A_P10, A_PROD, A_COMP, A_PODA, A_LIST]
TECNICAS = ("territory_id", "data_edition", "source_run_id", "artifact_name", "artifact_sha256", "source_commit",
            "expected_context_fingerprint", "confirm_recovery", "caduca_antes", "sha256_lista", "ejecutar", "tarea")


def on(d):
    return d.get("on") or d.get(True)


def efectivos(d, job):
    return d["jobs"][job].get("permissions", d.get("permissions"))


def a_viejo(texto):
    """Deshace las sustituciones de P70 en un trozo de job: entradas técnicas o resueltas, y `!cancelled()`."""
    t = re.sub(r"\(inputs\.(\w+) \|\| needs\.resolver_producto\.outputs\.\1\)", r"inputs.\1", str(texto))
    return t.replace("!cancelled() && ", "")


def deshacer(o):
    """`a_viejo` sobre un árbol YAML (cadenas, listas y diccionarios)."""
    if isinstance(o, dict):
        return {k: deshacer(v) for k, v in o.items()}
    if isinstance(o, list):
        return [deshacer(v) for v in o]
    return a_viejo(o) if isinstance(o, str) else o


def diferencias(viejo, jv, nuevo, jn, *, sin_env=(), env_renombrado=None):
    """Diferencias NO permitidas entre un job viejo y el de P70 (vacía = equivalente)."""
    a, b = viejo["jobs"][jv], nuevo["jobs"][jn]
    d = []
    if efectivos(viejo, jv) != efectivos(nuevo, jn):
        d.append(f"permisos {efectivos(viejo, jv)} != {efectivos(nuevo, jn)}")
    ca = a.get("concurrency", viejo.get("concurrency"))
    if ca != b.get("concurrency"):
        d.append(f"concurrencia {ca} != {b.get('concurrency')}")
    for k in ("runs-on", "timeout-minutes", "outputs", "name"):
        if a.get(k) != b.get(k):
            d.append(f"{k} difiere")
    env_a = {k: v for k, v in (a.get("env") or {}).items() if k not in sin_env}
    env_b = dict(b.get("env") or {})
    for viejo_k, nuevo_k in (env_renombrado or {}).items():
        env_b.pop(nuevo_k, None)
        env_a.pop(viejo_k, None)
    if deshacer(env_a) != deshacer(env_b):
        d.append("env difiere")
    if deshacer(a.get("steps")) != deshacer(b.get("steps")):
        d.append("pasos difieren")
    return d


class Congelado(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v = {}
        for k, (nombre, sha) in HUELLAS.items():
            ruta = FIX / nombre
            assert ruta.is_file(), f"falta la copia congelada {ruta}"  # nunca se salta
            datos = ruta.read_bytes()
            assert hashlib.sha256(datos).hexdigest() == sha, f"{nombre}: la copia congelada cambió"
            cls.v[k] = cargar_sin_version(datos.decode("utf-8"))
        cls.p = cargar_sin_version((WF / "p70-archivo.yml").read_text(encoding="utf-8"))


class Disparadores(Congelado):
    def test_ficheros_viejos_borrados_y_nuevo_con_nombre(self):
        for f in ("podar-r2.yml", "recuperar-producto-electoral-durable.yml", "mantenimiento-programado.yml"):
            self.assertFalse((WF / f).exists(), f)
        self.assertEqual(self.p["name"], "P70 Archivo")
        self.assertEqual(set(on(self.p)), {"schedule", "workflow_call", "workflow_dispatch"})

    def test_cron_diario_y_workflow_call_identicos(self):
        self.assertEqual(on(self.p)["schedule"], on(self.v["mant"])["schedule"])
        self.assertEqual(on(self.p)["schedule"], [{"cron": "17 5 * * *"}])
        self.assertEqual(on(self.p)["workflow_call"], on(self.v["rec"])["workflow_call"])  # entradas técnicas y salidas para la 00

    def test_boton_sin_parametros_tecnicos_y_una_accion_por_job(self):
        ent = on(self.p)["workflow_dispatch"]["inputs"]
        self.assertEqual(set(ent), {"accion", "simular", "territorios", "eleccion"})
        self.assertEqual(ent["accion"]["options"], ACCIONES)
        self.assertIs(ent["simular"]["default"], True)
        for t in TECNICAS:
            self.assertNotIn(t, ent)
        donde = {a: [j for j, job in self.p["jobs"].items() if f"inputs.accion == '{a}'" in str(job.get("if"))] for a in ACCIONES}
        self.assertEqual({a: len(js) for a, js in donde.items()}, {a: 1 for a in ACCIONES}, donde)
        self.assertEqual(donde[A_TODO], ["archivar_r2"])
        self.assertIn("github.event.schedule == '17 5 * * *'", self.p["jobs"]["archivar_r2"]["if"])

    def test_la_00_solo_cambia_el_uses(self):
        cero = yaml.safe_load((WF / "ejecucion-completa-proyecto.yml").read_text(encoding="utf-8"))
        j = cero["jobs"]["recuperar_electoral"]
        self.assertEqual(j["uses"], "./.github/workflows/p70-archivo.yml")
        self.assertEqual(set(j["with"]), set(on(self.p)["workflow_call"]["inputs"]))


class Equivalencia(Congelado):
    def test_archivar_r2_igual_salvo_caduca_antes(self):
        d = diferencias(self.v["mant"], "archivar_r2", self.p, "archivar_r2", sin_env=("CADUCA_ANTES",))
        self.assertEqual([x for x in d if x != "pasos difieren"], [])  # los pasos se comparan abajo: solo cambia «Archivar artefactos»
        a = self.v["mant"]["jobs"]["archivar_r2"]["steps"]
        b = self.p["jobs"]["archivar_r2"]["steps"]
        self.assertEqual(len(a), len(b))
        distintos = [i for i in range(len(a)) if a[i] != b[i]]
        self.assertEqual([a[i]["name"] for i in distintos], ["Archivar artefactos"])
        self.assertEqual(b[distintos[0]]["run"].strip().splitlines()[-1], "python3 herramientas/archivar_artefactos_r2.py | tee archivo.log")
        self.assertNotIn("caduca", str(b).lower())

    def test_extraer_m06_igual_con_un_paso_mas_para_la_fecha(self):
        d = diferencias(self.v["mant"], "extraer_m06", self.p, "extraer_m06", env_renombrado={"ELECCION": "ELECCION_MES"})
        self.assertEqual([x for x in d if x != "pasos difieren"], [])
        a = self.v["mant"]["jobs"]["extraer_m06"]["steps"]
        b = [s for s in self.p["jobs"]["extraer_m06"]["steps"] if s.get("name") != "Fecha de la elección"]
        self.assertEqual(a, b)  # mismos pasos, mismos comandos
        self.assertEqual(self.p["jobs"]["extraer_m06"]["env"]["ELECCION_MES"], "${{ inputs.eleccion || '2023-07' }}")

    def test_recuperacion_cuatro_jobs_iguales_con_entradas_resueltas(self):
        for j in ("acreditar", "validar_m08", "registrar", "acreditar_registro"):
            with self.subTest(j):
                a, b = self.v["rec"]["jobs"][j], self.p["jobs"][j]
                self.assertEqual(efectivos(self.v["rec"], j), efectivos(self.p, j))
                self.assertEqual(a.get("concurrency"), None if "concurrency" not in b else deshacer(b["concurrency"]))
                for k in ("runs-on", "outputs", "name", "uses", "secrets"):
                    self.assertEqual(a.get(k), b.get(k), k)
                self.assertEqual(a.get("steps"), deshacer(b["steps"]) if "steps" in b else None)
                self.assertEqual(a.get("with"), deshacer(b["with"]) if "with" in b else None)
                nd = [n for n in ([b["needs"]] if isinstance(b["needs"], str) else b["needs"]) if n != "resolver_producto"] if "needs" in b else []
                self.assertEqual(sorted(nd), sorted(([a["needs"]] if isinstance(a.get("needs"), str) else a.get("needs", []))))
                self.assertIn("resolver_producto", ([b["needs"]] if isinstance(b["needs"], str) else b["needs"]))
                if j != "acreditar":
                    self.assertEqual(" ".join(a_viejo(b["if"]).split()), " ".join(str(a["if"]).split()))

        # en `acreditar` la condición añade solo la rama «resuelto por el botón»
        self.assertEqual(self.p["jobs"]["acreditar"]["if"],
                         "${{ !cancelled() && (inputs.confirm_recovery || needs.resolver_producto.outputs.recover == 'true') }}")
        self.assertEqual(self.v["rec"]["jobs"]["acreditar"]["if"], "${{ inputs.confirm_recovery }}")

    def test_podar_igual_con_simular_y_sin_sha_en_el_boton(self):
        a, b = self.v["podar"]["jobs"]["podar"], self.p["jobs"]["podar"]
        self.assertEqual(self.v["podar"]["permissions"], {"contents": "write"})
        self.assertEqual(efectivos(self.p, "podar"), {"contents": "write"})
        self.assertEqual(b["concurrency"], self.v["podar"]["concurrency"])
        self.assertEqual(b["concurrency"], self.p["jobs"]["archivar_r2"]["concurrency"])  # un solo escritor en R2
        self.assertEqual((a["runs-on"], a["timeout-minutes"]), (b["runs-on"], b["timeout-minutes"]))
        self.assertEqual(a["environment"], "${{ inputs.ejecutar && 'produccion' || '' }}")
        self.assertEqual(b["environment"], "${{ !inputs.simular && 'produccion' || '' }}")  # borrado real solo con `produccion`
        self.assertEqual({k: v for k, v in a["env"].items() if k not in ("SHA_LISTA", "EJECUTAR")},
                         {k: v for k, v in b["env"].items() if k != "EJECUTAR"})
        self.assertEqual(b["env"]["EJECUTAR"], "${{ !inputs.simular }}")
        self.assertNotIn("SHA_LISTA", b["env"])
        sa, sb = a["steps"], b["steps"]
        self.assertEqual(len(sa), len(sb))
        distintos = [sa[i]["name"] for i in range(len(sa)) if sa[i] != sb[i]]
        self.assertEqual(distintos, ["Verificar y podar", "Conservar informe y manifiesto como artefacto", "Registrar informe y manifiesto en main"])
        run = [s for s in sb if s.get("name") == "Verificar y podar"][0]["run"]
        self.assertIn('SHA_LISTA="$(python3 herramientas/p70_resolver.py sha-poda)"', run)
        self.assertIn('python3 herramientas/podar_r2.py "${args[@]}"', run)
        for s in sb[-2:]:
            self.assertEqual(s["if"], "${{ always() && !inputs.simular }}")

    def test_archivar_p10_mismo_comando_que_bateria(self):
        j = self.p["jobs"]["archivar_p10"]
        run = "\n".join(s.get("run", "") for s in j["steps"])
        self.assertIn('python herramientas/bateria_motor.py archivar-p10 "$TERRITORIOS" --paquete "$carpeta" --run "$RUN_P10" --out bateria', run)
        self.assertIn('python herramientas/p70_resolver.py paquete-p10 "$TERRITORIOS"', run)
        self.assertEqual(j["permissions"], {"contents": "read", "actions": "read"})
        self.assertEqual(j["concurrency"], self.p["jobs"]["archivar_r2"]["concurrency"])
        bm = cargar_sin_version((ROOT / "tests/fixtures/t369_workflows/bateria-motor_1.3.1.yml").read_text(encoding="utf-8"))["jobs"]["archivar_p10"]  # copia congelada (T-369)
        self.assertEqual([s.get("uses") for s in bm["steps"] if "uses" in s], [s.get("uses") for s in j["steps"] if "uses" in s])

    def test_listar_solo_lectura(self):
        j = self.p["jobs"]["listar"]
        self.assertEqual(j["permissions"], {"contents": "read"})
        self.assertNotIn("concurrency", j)
        run = "\n".join(s.get("run", "") for s in j["steps"])
        self.assertIn("herramientas/listar_r2.py", run)
        for prohibido in ("rm ", "delete", "put-object", "s3 cp", "git push", "--ejecutar"):
            self.assertNotIn(prohibido, run)

    def test_concurrencia_con_cola_y_secretos_r2_de_jobs_nuevos_en_el_paso(self):
        for n, job in self.p["jobs"].items():
            c = job.get("concurrency")
            if c and c["cancel-in-progress"] is False:
                self.assertEqual(c.get("queue"), "max", n)
            if n in ("archivar_p10", "resolver_producto", "listar"):  # jobs nuevos: secretos R2 solo en el env del paso
                self.assertNotIn("R2_ACCESS_KEY_ID", str(job.get("env", "")), n)


class ControlesNegativos(Congelado):
    def test_permiso_ganado_se_detecta(self):
        p = copy.deepcopy(self.p)
        p["jobs"]["extraer_m06"]["permissions"] = {"contents": "write", "actions": "write"}
        self.assertTrue(any("permisos" in d for d in diferencias(self.v["mant"], "extraer_m06", p, "extraer_m06", env_renombrado={"ELECCION": "ELECCION_MES"})))

    def test_concurrencia_cambiada_se_detecta(self):
        p = copy.deepcopy(self.p)
        p["jobs"]["archivar_r2"]["concurrency"]["group"] = "otro"
        self.assertTrue(any("concurrencia" in d for d in diferencias(self.v["mant"], "archivar_r2", p, "archivar_r2", sin_env=("CADUCA_ANTES",))))

    def test_paso_cambiado_se_detecta(self):
        p = copy.deepcopy(self.p)
        p["jobs"]["extraer_m06"]["steps"][-1]["run"] += "\necho extra"
        self.assertIn("pasos difieren", diferencias(self.v["mant"], "extraer_m06", p, "extraer_m06", env_renombrado={"ELECCION": "ELECCION_MES"}))

    def test_comparacion_de_recuperacion_detecta_un_if_perdido(self):
        p = copy.deepcopy(self.p)
        p["jobs"]["registrar"]["if"] = "${{ true }}"
        self.assertNotEqual(" ".join(a_viejo(p["jobs"]["registrar"]["if"]).split()), " ".join(str(self.v["rec"]["jobs"]["registrar"]["if"]).split()))

    def test_podar_sin_entorno_se_detecta(self):
        self.assertIn("'produccion'", self.p["jobs"]["podar"]["environment"])
        self.assertNotEqual(self.p["jobs"]["podar"]["environment"].replace("produccion", ""), self.p["jobs"]["podar"]["environment"])


class Shell(Congelado):
    def test_pasos_nuevos_corren_bajo_bash_eo_pipefail(self):
        pasos = [s for s in self.p["jobs"]["resolver_producto"]["steps"] if s.get("name") == "Resultado"]
        self.assertEqual(len(pasos), 1)
        for recover in ("true", ""):
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", pasos[0]["run"]], env={"RECOVER": recover, "ESTADO": "NONE", "MOTIVO": "", "PATH": "/usr/bin:/bin"},
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
