# -*- coding: utf-8 -*-
"""T-377 (D-138, D-139, paso 8): P20 Distritos sustituye a `produccion-distritos.yml` y `_reutilizable-generacion-territorial.yml`;
`generar-alternativas-territoriales.yml` (P28) se retira sin sustituto, con su rama en P40, el ensemble del Gestor y `configuracion/ensemble/`.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-16 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
La equivalencia se calcula contra COPIAS CONGELADAS (`tests/fixtures/t377_workflows/`, con sha256; en CI no hay `legacy/`). Si falta una o cambia su
huella el test FALLA (no se salta). Controles negativos: un permiso, paso, comando, `needs`, `if`, entorno o artefacto cambiados se detectan.
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

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
FIX = ROOT / "tests" / "fixtures" / "t377_workflows"
SHAS = {
    "produccion-distritos_8.3.0.yml": "d27c949d5f9c7550ecf15e88b0fbafb83e594e6c19294ea9fc18e080709c5130",
    "reutilizable-generacion-territorial_1.6.0.yml": "fb056ee2791febdbb8edb891262bc9a2e31da890de9bfe554b801b1e2507e8fa",
    "generar-alternativas-territoriales_2.6.2.yml": "3cf9864cf042603e9e809d22f0ed5c4e02b90caadd773ebf72d1c7d69fec18e9",
    "p40-publicacion_1.0.0.yml": "f3674bc14a3c942b8bfb87d9428f2e44d07154d317573c21a83391599095880d",
    "ejecucion-completa-proyecto_1.11.2.yml": "0d36d547ac8e28189afe9b10648a17908528b8a30cc750ddb2f9cf113e938e3e",
}
# Rótulos del log (D-129; con espacio, sin «·»): P21 base y población, P22 adyacencias, P23 grafo, P24 solución inicial, P25 optimización, P26 producto, P27 auditoría.
ETIQUETAS = {"resolve": "P20", "official_sources": "P21", "m01": "P21", "m02": "P22", "m03": "P23", "internal_units": "P24",
             "pre_m04_evidence": "P24", "pre_m04_diagnostic": "P24", "m04": "P24", "m05": "P25", "m06": "P26", "auditoria": "P27",
             "registrar": "P26"}
BOOLEANAS = ("persist_state", "preflight_only", "require_unique_hashes")


def on(d):
    return d.get("on") or d.get(True)


def carga(p):
    return yaml.safe_load(Path(p).read_text(encoding="utf-8"))


def motor_normalizado(texto: str) -> str:
    """Única transformación permitida en el cuerpo del motor: sus entradas pasan a salidas del job `entrada` (las booleanas, comparadas con 'true')."""
    for b in BOOLEANAS:
        texto = texto.replace(f"inputs.{b}", f"(needs.entrada.outputs.{b} == 'true')")
    texto = re.sub(r"\binputs\.([a-z_0-9]+)", r"needs.entrada.outputs.\1", texto)
    # Los pasos del P30 del motor 2 pasan a rotularse P26 (sin «·»: los workflows con botón no lo admiten, test_codauto_preparation_contract).
    return texto.replace('"name": "P30 · ', '"name": "P26 ')


def diferencias_motor(viejo: dict, nuevo: dict) -> list[str]:
    """Diferencias NO permitidas entre los jobs del reutilizable 1.6.0 y los mismos jobs de P20 (vacía = equivalente)."""
    d = []
    for k, a in viejo["jobs"].items():
        b = nuevo["jobs"].get(k)
        if b is None:
            d.append(f"{k}: falta")
            continue
        esperado = json.loads(motor_normalizado(json.dumps(a, ensure_ascii=False)))
        esperado["name"] = f"{ETIQUETAS[k]} {a['name']}"
        esperado["needs"] = ["entrada"] + list(a["needs"]) if "needs" in a else "entrada"
        for clave in sorted(set(esperado) | set(b)):
            if esperado.get(clave) != b.get(clave):
                d.append(f"{k}.{clave}")
    return d


class Congelado(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for nombre, sha in SHAS.items():
            assert (FIX / nombre).is_file(), f"falta la copia congelada {nombre}"  # nunca se salta
            assert hashlib.sha256((FIX / nombre).read_bytes()).hexdigest() == sha, f"la copia congelada {nombre} cambió"
        cls.pd = carga(FIX / "produccion-distritos_8.3.0.yml")
        cls.ru = carga(FIX / "reutilizable-generacion-territorial_1.6.0.yml")
        cls.p40v = carga(FIX / "p40-publicacion_1.0.0.yml")
        cls.c00v = carga(FIX / "ejecucion-completa-proyecto_1.11.2.yml")
        cls.p = carga(WF / "p20-distritos.yml")
        cls.txt = (WF / "p20-distritos.yml").read_text(encoding="utf-8")


class Boton(Congelado):
    def test_ficheros_viejos_borrados_y_nombre(self):
        for f in ("produccion-distritos.yml", "_reutilizable-generacion-territorial.yml", "generar-alternativas-territoriales.yml"):
            self.assertFalse((WF / f).exists(), f)
        self.assertEqual(self.p["name"], "P20 Distritos")

    def test_entradas_del_boton(self):
        e = on(self.p)["workflow_dispatch"]["inputs"]
        self.assertEqual(set(e), {"territorios", "empezar_de_cero"})
        self.assertEqual(e["territorios"]["type"], "string")
        self.assertEqual(e["empezar_de_cero"]["type"], "boolean")
        self.assertIs(e["empezar_de_cero"]["default"], False)  # desmarcado = «Reutilizar progreso existente»
        for k in e:
            self.assertTrue(k.isascii() and k.isidentifier(), k)  # GitHub no admite tildes en los inputs
        for fuera in ("optimization_algorithm", "data_edition", "execution_mode", "territory_id", "synthetic", "republicar"):
            self.assertNotIn(fuera, e)

    def test_workflow_call_es_la_union_de_los_dos_ficheros(self):
        c = on(self.p)["workflow_call"]["inputs"]
        viejas = {**on(self.pd)["workflow_call"]["inputs"], **on(self.ru)["workflow_call"]["inputs"]}
        self.assertEqual(set(c), set(viejas))
        for k, v in viejas.items():
            self.assertEqual(c[k]["type"], v["type"], k)
            self.assertFalse(c[k]["required"], k)  # cada ruta trae solo las suyas
            if k not in ("territory_id", "params", "mode", "from_stage", "to_stage", "data_edition"):
                self.assertEqual(c[k].get("default"), v.get("default"), k)
        self.assertEqual(c["data_edition"]["default"], "2025")  # edición fija
        self.assertEqual(on(self.p)["workflow_call"]["outputs"], on(self.ru)["workflow_call"]["outputs"])

    def test_la_00_solo_cambia_los_uses(self):
        n = carga(WF / "ejecucion-completa-proyecto.yml")
        for job in ("acreditar_generacion", "generar"):
            a, b = copy.deepcopy(self.c00v["jobs"][job]), copy.deepcopy(n["jobs"][job])
            self.assertEqual(b.pop("uses"), "./.github/workflows/p20-distritos.yml")
            a.pop("uses")
            self.assertEqual(a, b, job)
        a, b = copy.deepcopy(self.c00v["jobs"]), copy.deepcopy(n["jobs"])
        for job in ("acreditar_generacion", "generar"):
            a[job].pop("uses"), b[job].pop("uses")
        self.assertEqual(a, b)  # el resto de la 00, intacto

    def test_matriz_del_boton_llama_a_la_ruta_generar(self):
        j = self.p["jobs"]
        self.assertEqual(j["distritos"]["uses"], "./.github/workflows/p20-distritos.yml")
        self.assertEqual(j["distritos"]["strategy"]["fail-fast"], False)  # un territorio que falla no cancela a los demás
        self.assertEqual(j["distritos"]["strategy"]["matrix"], "${{ fromJSON(needs.territorios.outputs.matriz) }}")
        w = j["distritos"]["with"]
        self.assertEqual(w["territory_id"], "${{ matrix.nombre }}")
        self.assertEqual(w["data_edition"], "2025")
        self.assertEqual(w["execution_mode"], "${{ inputs.empezar_de_cero && 'Ejecutar desde el principio' || 'Reutilizar progreso existente' }}")
        self.assertNotEqual(w["invocation_context"], "reusable")  # como el botón viejo: persiste estado
        self.assertEqual(j["distritos"]["secrets"], "inherit")
        self.assertIn("python3 herramientas/p20_territorios.py matriz", j["territorios"]["steps"][-1]["run"])
        self.assertEqual(j["territorios"]["if"], "${{ format('{0}', inputs.territorios) != '' }}")
        # Las opciones del botón viejo que se quitan existen en la copia congelada (control de que el test no es vacuo).
        self.assertIn("GerryChain 50", on(self.pd)["workflow_dispatch"]["inputs"]["optimization_algorithm"]["options"])


class Equivalencia(Congelado):
    def test_motor_equivalente_job_a_job(self):
        self.assertEqual(diferencias_motor(self.ru, self.p), [])

    def test_motor_sin_entradas_directas(self):
        for k in self.ru["jobs"]:
            self.assertNotIn("inputs.", json.dumps(self.p["jobs"][k], ensure_ascii=False), k)

    def test_resolver_interfaz_identico_salvo_rotulo_ruta_y_permisos(self):
        a, b = copy.deepcopy(self.pd["jobs"]["resolver_interfaz"]), copy.deepcopy(self.p["jobs"]["resolver_interfaz"])
        self.assertEqual(b.pop("name"), "P20 " + a.pop("name"))
        self.assertEqual(b.pop("if"), "${{ format('{0}', inputs.territory_id) != '' }}")
        self.assertEqual(b.pop("permissions"), self.pd["permissions"])  # los mismos que tenía el workflow viejo
        self.assertEqual(a, b)

    def test_permisos_ningun_job_gana(self):
        self.assertEqual(self.p["permissions"], self.ru["permissions"])
        for k in self.ru["jobs"]:
            self.assertNotIn("permissions", self.p["jobs"][k], k)  # heredan los del reutilizable
        j = self.p["jobs"]
        self.assertEqual(j["entrada"]["permissions"], {})
        self.assertEqual(j["territorios"]["permissions"], {"contents": "read"})
        self.assertEqual(j["distritos"]["permissions"], self.pd["permissions"])

    def test_sin_entornos_como_antes(self):
        for d in (self.pd, self.ru, self.p):
            for k, job in d["jobs"].items():
                self.assertNotIn("environment", job, k)

    def test_concurrencia_por_ruta(self):
        self.assertEqual(self.pd["concurrency"]["group"], "ddd-territorial-prod-${{ inputs.territory_id }}-${{ inputs.data_edition }}")
        self.assertEqual(self.ru["concurrency"]["group"], "ddd-territorial-engine-${{ inputs.params }}")
        g = self.p["concurrency"]
        self.assertEqual({k: v for k, v in g.items() if k != "group"}, {"cancel-in-progress": False, "queue": "max"})
        self.assertEqual({k: v for k, v in self.pd["concurrency"].items() if k != "group"}, {"cancel-in-progress": False, "queue": "max"})
        self.assertEqual(g["group"],
                         "${{ format('{0}', inputs.territory_id) != '' && format('ddd-territorial-prod-{0}-{1}', inputs.territory_id, inputs.data_edition)"
                         " || (format('{0}', inputs.params) != '' && format('ddd-territorial-engine-{0}', inputs.params)"
                         " || format('ddd-p20-boton-{0}', github.run_id)) }}")
        for k, job in self.p["jobs"].items():
            self.assertNotIn("concurrency", job, k)

    def test_salidas_artefactos_y_registro_intactos(self):
        def subidas(d, jobs):
            return [s for k in jobs for s in d["jobs"][k].get("steps", []) if isinstance(s, dict)
                    and str(s.get("uses", "")).startswith(("actions/upload-artifact", "actions/download-artifact"))]
        a = subidas(self.ru, self.ru["jobs"])
        self.assertTrue(a)
        self.assertEqual(json.loads(motor_normalizado(json.dumps(a, ensure_ascii=False))), subidas(self.p, self.ru["jobs"]))
        reg = json.dumps(self.p["jobs"]["registrar"], ensure_ascii=False)
        self.assertIn("python -m herramientas.registrar_en_main", reg)

    def test_la_00_llega_con_las_mismas_entradas_al_motor(self):
        """Las entradas del job `ruta` de produccion-distritos 8.3.0 son las que reproduce `entrada` en la ruta «generar»."""
        ruta = self.pd["jobs"]["ruta"]["with"]
        self.assertEqual(ruta["mode"], "execute")
        self.assertEqual(ruta["execution_authorization"], "EXECUTE_WITH_EXPLICIT_USER_AUTHORIZATION")
        self.assertEqual(ruta["persist_state"], "${{ inputs.invocation_context != 'reusable' || inputs.persist_state }}")
        self.assertEqual(ruta["gerrychain_entrypoint"],
                         "${{ inputs.optimization_algorithm == 'GerryChain 50' && 'gerrychain_50' || inputs.gerrychain_entrypoint }}")
        self.assertEqual(set(ruta), {"params", "mode", "from_stage", "to_stage", "checkpoint_run_id", "source_package_run_id",
                                     "source_package_artifact_name", "execution_authorization", "source_ref", "persist_state",
                                     "optimization_algorithm", "motor", "artifact_namespace", "gerrychain_entrypoint", "require_unique_hashes"})
        salidas = set(self.p["jobs"]["entrada"]["outputs"])
        self.assertEqual(salidas, set(on(self.ru)["workflow_call"]["inputs"]))


class Entrada(Congelado):
    """El paso «Normalizar la entrada del motor» bajo `bash -eo pipefail` (como `shell: bash` en Actions)."""

    def correr(self, **env):
        paso = self.p["jobs"]["entrada"]["steps"][0]
        base = {k: "" for k in paso["env"]}
        base.update({"IN_PERSIST_STATE": "true", "IN_INVOCATION_CONTEXT": "reusable", "IN_REQUIRE_UNIQUE_HASHES": "false",
                     "IN_PREFLIGHT_ONLY": "false", "IN_OPTIMIZATION_ALGORITHM": "Canónico", "IN_MOTOR": "motor2"})
        base.update(env)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            out.write_text("")
            script = Path(tmp) / "s.sh"
            script.write_text(paso["run"], encoding="utf-8")
            r = subprocess.run(["bash", "-eo", "pipefail", str(script)], capture_output=True, text=True,
                               env={"PATH": os.environ["PATH"], "GITHUB_OUTPUT": str(out), **base})
            vals = dict(l.split("=", 1) for l in out.read_text().splitlines() if "=" in l)
        return r, vals

    def test_ruta_generar_de_la_00(self):
        r, v = self.correr(RUTA="generar", RI_PARAMS="territorios/aut11/config/aut11_2025.yaml", RI_FROM_STAGE="M06", RI_TO_STAGE="M06",
                           RI_CHECKPOINT_RUN_ID="123", RI_SOURCE_PACKAGE_RUN_ID="", RI_SOURCE_PACKAGE_ARTIFACT_NAME="",
                           IN_SOURCE_PACKAGE_RUN_ID="999", IN_SOURCE_PACKAGE_ARTIFACT_NAME="ddd-source-package-x", IN_PERSIST_STATE="false",
                           IN_SOURCE_REF="abc", IN_PREFLIGHT_ONLY="true", IN_SOURCE_EVIDENCE_RUN_ID="7")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(v["params"], "territorios/aut11/config/aut11_2025.yaml")
        self.assertEqual(v["mode"], "execute")
        self.assertEqual(v["checkpoint_run_id"], "123")
        self.assertEqual(v["source_package_run_id"], "")  # el del resolutor, nunca el que impone la 00 (ese solo valida el paquete)
        self.assertEqual(v["source_package_artifact_name"], "")
        self.assertEqual(v["execution_authorization"], "EXECUTE_WITH_EXPLICIT_USER_AUTHORIZATION")
        self.assertEqual(v["persist_state"], "false")  # reusable y persist_state=false
        self.assertEqual(v["preflight_only"], "false")
        self.assertEqual(v["source_evidence_run_id"], "")
        self.assertEqual(v["source_ref"], "abc")
        self.assertEqual(v["motor"], "motor2")
        self.assertEqual(v["gerrychain_entrypoint"], "")
        self.assertEqual(v["require_unique_hashes"], "false")

    def test_ruta_generar_del_boton_persiste(self):
        r, v = self.correr(RUTA="generar", RI_PARAMS="p.yaml", IN_INVOCATION_CONTEXT="boton", IN_PERSIST_STATE="false")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(v["persist_state"], "true")

    def test_gerrychain_50(self):
        r, v = self.correr(RUTA="generar", RI_PARAMS="p.yaml", IN_OPTIMIZATION_ALGORITHM="GerryChain 50", IN_GERRYCHAIN_ENTRYPOINT="x")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((v["gerrychain_entrypoint"], v["require_unique_hashes"]), ("gerrychain_50", "true"))

    def test_ruta_acreditar_pasa_las_entradas_tal_cual(self):
        r, v = self.correr(RUTA="acreditar", IN_PARAMS="territorios/aut11/config/aut11_2025.yaml", IN_MODE="execute",
                           IN_FROM_STAGE="TERRITORY_PREPARATION", IN_TO_STAGE="DISTRICT_FORMATION", IN_SOURCE_PACKAGE_RUN_ID="999",
                           IN_SOURCE_PACKAGE_ARTIFACT_NAME="ddd-source-package-x", IN_EXECUTION_AUTHORIZATION="EXECUTE_WITH_EXPLICIT_USER_AUTHORIZATION",
                           IN_PREFLIGHT_ONLY="true", IN_PERSIST_STATE="true", IN_MOTOR="")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((v["from_stage"], v["to_stage"]), ("TERRITORY_PREPARATION", "DISTRICT_FORMATION"))
        self.assertEqual((v["source_package_run_id"], v["source_package_artifact_name"]), ("999", "ddd-source-package-x"))
        self.assertEqual((v["preflight_only"], v["persist_state"], v["motor"]), ("true", "true", "motor2"))

    def test_sin_contrato_falla_cerrado(self):
        r, v = self.correr(RUTA="acreditar", IN_PARAMS="")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("P20_ENTRADA_SIN_CONTRATO", r.stdout + r.stderr)
        self.assertEqual(v, {})


class Territorios(unittest.TestCase):
    def correr(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "herramientas" / "p20_territorios.py"), *args], capture_output=True, text=True, cwd=ROOT)

    def test_matriz_con_el_nombre_del_catalogo(self):
        r = self.correr("matriz", "--territorios", "aut11, nac42,aut11")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout), {"include": [{"codigo": "aut11", "nombre": "Extremadura"},
                                                            {"codigo": "nac42", "nombre": "Congreso Soria"}]})

    def test_fallo_cerrado(self):
        for t, cod in (("aut99", "P20_TERRITORIO_DESCONOCIDO"), ("", "P20_TERRITORIOS_VACIO"), ("aut11;rm", "P20_TERRITORIO_INVALIDO"),
                       ("aut11,aut99", "P20_TERRITORIO_DESCONOCIDO")):
            r = self.correr("matriz", "--territorios", t)
            self.assertEqual(r.returncode, 1, t)
            self.assertEqual(r.stdout, "", t)
            self.assertIn(f"::error::{cod}", r.stderr, t)

    def test_help(self):
        self.assertEqual(self.correr("--help").returncode, 0)


class Negativos(Congelado):
    def test_controles_negativos_del_motor(self):
        casos = {
            "m04.steps": lambda n: n["jobs"]["m04"].__setitem__("steps", [{"run": "echo hola"}]),
            "registrar.if": lambda n: n["jobs"]["registrar"].__setitem__("if", "${{ always() }}"),
            "m06.needs": lambda n: n["jobs"]["m06"].__setitem__("needs", ["entrada", "resolve"]),
            "auditoria.permissions": lambda n: n["jobs"]["auditoria"].__setitem__("permissions", {"contents": "write", "pages": "write"}),
            "m01.environment": lambda n: n["jobs"]["m01"].__setitem__("environment", "produccion"),
            "m02.name": lambda n: n["jobs"]["m02"].__setitem__("name", "Adyacencias territoriales"),
            "resolve.falta": lambda n: n["jobs"].pop("resolve"),
        }
        for esperado, tocar in casos.items():
            n = copy.deepcopy(self.p)
            tocar(n)
            dif = diferencias_motor(self.ru, n)
            clave = esperado.replace(".falta", ": falta")
            self.assertIn(clave, dif, esperado)

    def test_artefacto_cambiado_se_detecta(self):
        n = copy.deepcopy(self.p)
        s = next(s for s in n["jobs"]["resolve"]["steps"] if str(s.get("uses", "")).startswith("actions/upload-artifact"))
        s["with"]["name"] = "otro"
        self.assertIn("resolve.steps", diferencias_motor(self.ru, n))


class Retirada(Congelado):
    def test_p40_sin_entradas_ni_rama_de_ensemble(self):
        p40 = carga(WF / "p40-publicacion.yml")
        c = on(p40)["workflow_call"]["inputs"]
        for k in ("ensemble_release_tag", "ensemble_sha256", "scenario_id", "scenario_strategy"):
            self.assertIn(k, on(self.p40v)["workflow_call"]["inputs"])  # existían (control)
            self.assertNotIn(k, c)
        t = "\n".join(l for l in (WF / "p40-publicacion.yml").read_text(encoding="utf-8").splitlines() if not l.lstrip().startswith("#"))
        for s in ("ENSEMBLE_RELEASE_TAG", "SCENARIO_ID", "Resolver ensemble persistente solicitado", "inputs.ensemble", "inputs.scenario"):
            self.assertNotIn(s, t)
        self.assertNotIn("if", p40["jobs"]["resolver"])
        self.assertEqual(p40["jobs"]["publicar"]["if"], "${{ needs.preparar.result == 'success' }}")

    def test_p40_publicar_igual_salvo_lo_del_ensemble(self):
        a = copy.deepcopy(self.p40v["jobs"]["publicar"])
        b = carga(WF / "p40-publicacion.yml")["jobs"]["publicar"]
        a["steps"] = [s for s in a["steps"] if s.get("name") != "Resolver ensemble persistente solicitado"]
        for k in ("SCENARIO_ID", "SCENARIO_STRATEGY", "ENSEMBLE_RELEASE_TAG", "ENSEMBLE_SHA256"):
            a["env"].pop(k)
        a.pop("if")
        txt = json.dumps(a["steps"], ensure_ascii=False)
        txt = txt.replace(' --scenario-id \\"$SCENARIO_ID\\")', ")")
        txt = txt.replace(' ${SCENARIO_ID:+--scenario-id \\"$SCENARIO_ID\\" --strategy \\"$SCENARIO_STRATEGY\\"}', "")
        a["steps"] = json.loads(txt)
        nb = {k: v for k, v in b.items() if k != "if"}
        self.assertEqual(a, nb)

    def test_gestor_no_lanza_ensembles(self):
        sys.path.insert(0, str(ROOT / "herramientas"))
        import legislatura_vigente as lv
        import gestor_campanas_2 as g2
        self.assertFalse(hasattr(lv, "WF_06"))
        self.assertFalse(hasattr(lv.Territorio, "ensemble"))
        texto = (ROOT / "herramientas" / "legislatura_vigente.py").read_text(encoding="utf-8")
        self.assertNotIn('dispatch(WF_06', texto)
        self.assertNotIn("cola_06\"", texto)
        for valor in ("10", "25"):
            with self.assertRaises(g2.NoDisponible) as cm:
                g2.resolve({"eleccion": "legislatura vigente", "tipo": "nacional", "territorios": "Huesca", "inicio": "reutilizar progreso",
                            "publicar": "no", "ensemble": valor, "mapa": "407"})
            self.assertIn("D-138", str(cm.exception))

    def test_configuraciones_de_ensemble_retiradas_y_sin_lectores_vivos(self):
        self.assertFalse((ROOT / "configuracion" / "ensemble").exists())
        lectores = []
        for base in ("herramientas", ".github", "ddd_core", "ddd_ensemble", "ddd_motor2", "modulos", "visor", "configuracion"):
            for dirpath, _, files in os.walk(ROOT / base):
                for f in files:
                    if f.endswith((".py", ".yml", ".yaml", ".js", ".sh", ".json")):
                        p = Path(dirpath) / f
                        if "configuracion/ensemble" in p.read_text(encoding="utf-8", errors="ignore"):
                            lectores.append(str(p.relative_to(ROOT)))
        self.assertEqual(lectores, [])

    def test_ningun_workflow_cita_los_ficheros_retirados(self):
        for f in WF.glob("*.yml"):
            t = "\n".join(l for l in f.read_text(encoding="utf-8").splitlines() if not l.lstrip().startswith("#"))
            for viejo in ("produccion-distritos.yml", "_reutilizable-generacion-territorial.yml", "generar-alternativas-territoriales.yml"):
                self.assertNotIn(viejo, t, f.name)


if __name__ == "__main__":
    unittest.main()
