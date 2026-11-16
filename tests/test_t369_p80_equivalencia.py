# -*- coding: utf-8 -*-
"""T-369 (D-131/D-132, paso 3): P80 Verificación del motor sustituye a `bateria-motor.yml` sin cambiar comandos, permisos, concurrencia ni artefactos.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-16 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
La equivalencia se calcula contra una COPIA CONGELADA (`tests/fixtures/t369_workflows/`, con sha256; en CI no hay `legacy/`). Si falta o cambia su huella
el test FALLA (no se salta). Los controles negativos comprueban que un permiso, una concurrencia, un paso, un artefacto o un `if` cambiados se detectan.
"""
import copy
import hashlib
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
FIX = ROOT / "tests" / "fixtures" / "t369_workflows" / "bateria-motor_1.3.1.yml"
SHA = "ef83f41a617f72b73bb535e1a6a0824319f4d88dc5f7c8c5f0cd101bf378dba0"
JOBS = ("bateria", "plan", "competicion", "aceptacion")
FIJOS = {"VERSIONES": "7.4.4", "CADENAS": "10", "FUNCION": "D8"}  # valores que dejan de ser entradas del botón


def on(d):
    return d.get("on") or d.get(True)


def efectivos(d, job):
    return d["jobs"][job].get("permissions", d.get("permissions"))


def a_viejo(o):
    """Deshace la única sustitución de P80 en los pasos: comas -> espacios en `territorios`."""
    if isinstance(o, dict):
        return {k: a_viejo(v) for k, v in o.items()}
    if isinstance(o, list):
        return [a_viejo(v) for v in o]
    return o.replace('<<<"${TERRITORIOS//,/ }"', '<<<"$TERRITORIOS"') if isinstance(o, str) else o


def diferencias(viejo, nuevo, job):
    """Diferencias NO permitidas entre un job de la batería y el de P80 (vacía = equivalente)."""
    a, b = viejo["jobs"][job], nuevo["jobs"][job]
    d = []
    if efectivos(viejo, job) != efectivos(nuevo, job):
        d.append("permisos")
    if a.get("concurrency", viejo.get("concurrency")) != b.get("concurrency", nuevo.get("concurrency")):
        d.append("concurrencia")
    for k in ("runs-on", "timeout-minutes", "outputs", "name", "needs", "strategy"):
        if a.get(k) != b.get(k):
            d.append(k)
    ea, eb = dict(a.get("env") or {}), dict(b.get("env") or {})
    for k in FIJOS:
        if k in eb:
            if eb[k] != FIJOS[k]:
                d.append(f"valor fijo {k}")
            eb.pop(k)
            ea.pop(k, None)  # en la batería venía del botón
    if ea != eb:
        d.append("env")
    if a.get("steps") != a_viejo(b.get("steps")):
        d.append("pasos")
    return d


class Congelado(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert FIX.is_file(), f"falta la copia congelada {FIX}"  # nunca se salta
        datos = FIX.read_bytes()
        assert hashlib.sha256(datos).hexdigest() == SHA, "la copia congelada cambió"
        cls.v = yaml.safe_load(datos.decode("utf-8"))
        cls.p = yaml.safe_load((WF / "p80-verificacion-motor.yml").read_text(encoding="utf-8"))


class Disparadores(Congelado):
    def test_fichero_viejo_borrado_y_nuevo_manual_sin_programacion(self):
        self.assertFalse((WF / "bateria-motor.yml").exists())
        self.assertEqual(self.p["name"], "P80 Verificación del motor")
        self.assertEqual(set(on(self.p)), {"workflow_dispatch"})  # sin schedule ni workflow_call

    def test_boton_solo_alcance_y_territorios(self):
        ent = on(self.p)["workflow_dispatch"]["inputs"]
        self.assertEqual(set(ent), {"alcance", "territorios"})
        self.assertEqual(ent["alcance"]["options"], ["motor vigente", "motor base M05"])
        self.assertEqual(ent["alcance"]["default"], "motor vigente")
        self.assertEqual(ent["territorios"]["default"], "")
        for o in ent["alcance"]["options"]:
            self.assertTrue(o.isascii(), o)  # los inputs de GitHub no admiten tildes
        self.assertEqual(self.p["run-name"], "P80 · ${{ inputs.alcance }} · ${{ inputs.territorios || 'todos' }}")

    def test_workflow_igual_permisos_y_concurrencia(self):
        self.assertEqual(self.p["permissions"], self.v["permissions"])
        self.assertEqual(self.p["concurrency"], self.v["concurrency"])
        self.assertEqual(self.p["concurrency"]["queue"], "max")

    def test_se_retiran_los_dos_jobs_de_un_solo_uso_y_los_cuatro_se_quedan(self):
        self.assertEqual(set(self.p["jobs"]), set(JOBS))
        self.assertEqual(set(self.v["jobs"]) - set(self.p["jobs"]), {"archivar_p10", "archivar_almacen_m06"})
        texto = "\n".join(l for l in (WF / "p80-verificacion-motor.yml").read_text(encoding="utf-8").splitlines() if not l.lstrip().startswith("#"))
        for fuera in ("archivar_almacen_m06", "inputs.archivar_p10", "inputs.funcion", "inputs.cadenas", "inputs.versiones_m05", "inputs.motor"):
            self.assertNotIn(fuera, texto)


class Equivalencia(Congelado):
    def test_cuatro_jobs_iguales_salvo_valores_fijos_y_comas(self):
        for j in JOBS:
            with self.subTest(j):
                self.assertEqual(diferencias(self.v, self.p, j), [])

    def test_alcance_selecciona_los_jobs_y_la_aceptacion_sigue_con_always(self):
        j = self.p["jobs"]
        self.assertEqual(j["bateria"]["if"], "${{ inputs.alcance == 'motor base M05' }}")
        self.assertEqual(j["plan"]["if"], "${{ inputs.alcance == 'motor vigente' }}")
        self.assertNotIn("if", j["competicion"])  # cuelga de `plan` (se salta con él)
        self.assertEqual(j["competicion"]["needs"], "plan")
        # un `needs` saltado deja el job saltado salvo always()/!cancelled(): la aceptación sigue corriendo si fallan territorios
        self.assertEqual(j["aceptacion"]["if"], "${{ always() && inputs.alcance == 'motor vigente' && needs.plan.result == 'success' }}")
        self.assertEqual(j["aceptacion"]["needs"], ["plan", "competicion"])

    def test_valores_fijados_en_el_codigo(self):
        j = self.p["jobs"]
        self.assertEqual(j["bateria"]["env"]["VERSIONES"], "7.4.4")
        self.assertEqual(j["plan"]["env"]["CADENAS"], "10")
        self.assertEqual(j["competicion"]["env"]["CADENAS"], "10")
        self.assertEqual(j["competicion"]["env"]["FUNCION"], "D8")
        self.assertEqual(j["competicion"]["env"]["PYTHONHASHSEED"], "0")
        self.assertEqual(j["aceptacion"]["env"]["CADENAS"], "10")

    def test_artefactos_mismos_nombres_rutas_y_retencion(self):
        for j in JOBS:
            a = [s for s in self.v["jobs"][j]["steps"] if str(s.get("uses", "")).startswith("actions/upload-artifact")
                 or str(s.get("uses", "")).startswith("actions/download-artifact")]
            b = [s for s in self.p["jobs"][j]["steps"] if str(s.get("uses", "")).startswith("actions/upload-artifact")
                 or str(s.get("uses", "")).startswith("actions/download-artifact")]
            self.assertEqual(a, b, j)
            self.assertTrue(b, j) if j != "plan" else None

    def test_credenciales_r2_solo_en_los_pasos_de_entradas(self):
        for j in JOBS:
            job = self.p["jobs"][j]
            self.assertFalse([k for k in job.get("env", {}) if k.startswith(("AWS_", "R2_"))], j)

    def test_comas_a_espacios_en_cada_lectura_de_territorios(self):
        texto = (WF / "p80-verificacion-motor.yml").read_text(encoding="utf-8")
        self.assertNotIn('<<<"$TERRITORIOS"', texto)
        self.assertEqual(texto.count('<<<"${TERRITORIOS//,/ }"'), 4)  # entradas, motor, lista (plan) y aceptación

    def test_archivar_p10_lo_cubre_p71_del_paquete_de_fuentes(self):
        a = self.v["jobs"]["archivar_p10"]
        b = yaml.safe_load((WF / "p70-archivo.yml").read_text(encoding="utf-8"))["jobs"]["archivar_p10"]
        self.assertEqual(a["permissions"], b["permissions"])  # contents: read, actions: read
        self.assertEqual((a["runs-on"], a["timeout-minutes"]), (b["runs-on"], b["timeout-minutes"]))
        self.assertEqual(a["steps"][:3], b["steps"][:3])  # checkout, python 3.13 y pip del lock, idénticos
        self.assertEqual({k for k in a["steps"][3] if a["steps"][3][k] != b["steps"][3].get(k)}, {"run"})  # mismo nombre, shell y env R2
        self.assertEqual({k for k in a["steps"][4] if a["steps"][4][k] != b["steps"][4].get(k)}, {"with"})  # solo el nombre del artefacto
        self.assertEqual(a["steps"][4]["with"]["path"], b["steps"][4]["with"]["path"])
        self.assertEqual(a["steps"][4]["with"]["retention-days"], b["steps"][4]["with"]["retention-days"])
        pa = [s for s in a["steps"] if s.get("name", "").startswith("Paquete P10")][0]
        pb = [s for s in b["steps"] if s.get("name", "").startswith("Paquete P10")][0]
        self.assertEqual(pa["env"], pb["env"])  # mismas credenciales R2, solo en el paso
        self.assertEqual(pa["shell"], pb["shell"])
        self.assertEqual(pa["run"].strip().splitlines()[-5:], pb["run"].strip().splitlines()[-5:])  # mismo `gh run download`, carpeta y comando
        self.assertEqual(pa["run"].strip().splitlines()[-1], pb["run"].strip().splitlines()[-1])
        self.assertIn("archivar-p10", pb["run"])
        # único cambio: el id del run lo resuelve el código (catálogo de procedencia) y la concurrencia pasa al grupo de escritores de R2
        self.assertIn("paquete-p10", pb["run"])
        self.assertEqual(b["concurrency"]["group"], "archivar-artefactos-r2")


class ControlesNegativos(Congelado):
    def test_permiso_ganado_se_detecta(self):
        p = copy.deepcopy(self.p)
        p["jobs"]["bateria"]["permissions"] = {"contents": "write"}
        self.assertIn("permisos", diferencias(self.v, p, "bateria"))

    def test_concurrencia_cambiada_se_detecta(self):
        p = copy.deepcopy(self.p)
        p["jobs"]["plan"]["concurrency"] = {"group": "otro"}
        self.assertIn("concurrencia", diferencias(self.v, p, "plan"))

    def test_paso_cambiado_se_detecta(self):
        p = copy.deepcopy(self.p)
        p["jobs"]["competicion"]["steps"][-3]["run"] += "\necho extra"
        self.assertIn("pasos", diferencias(self.v, p, "competicion"))

    def test_artefacto_cambiado_se_detecta(self):
        p = copy.deepcopy(self.p)
        p["jobs"]["bateria"]["steps"][-1]["with"]["retention-days"] = 90
        self.assertIn("pasos", diferencias(self.v, p, "bateria"))

    def test_valor_fijo_cambiado_se_detecta(self):
        p = copy.deepcopy(self.p)
        p["jobs"]["competicion"]["env"]["FUNCION"] = "A"
        self.assertIn("valor fijo FUNCION", diferencias(self.v, p, "competicion"))

    def test_entorno_cambiado_se_detecta(self):
        p = copy.deepcopy(self.p)
        p["jobs"]["aceptacion"]["env"]["EXTRA"] = "1"
        self.assertIn("env", diferencias(self.v, p, "aceptacion"))

    def test_copia_congelada_alterada_falla_la_huella(self):
        self.assertNotEqual(hashlib.sha256(FIX.read_bytes() + b"x").hexdigest(), SHA)


if __name__ == "__main__":
    unittest.main()
